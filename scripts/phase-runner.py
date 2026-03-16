#!/usr/bin/env python3
"""
Script-driven phase runner for the orchestrate pipeline.

Each protocol step runs as a separate `claude -p` subprocess with its own
context window. Artifact gates between steps enforce the full protocol —
no single agent can skip reviews, builds, or fixes.

Usage:
    python3 .claude/scripts/phase-runner.py --phase 4 --plan-dir docs/plans
    python3 .claude/scripts/phase-runner.py --phase 4 --plan-dir docs/plans --dry-run
    python3 .claude/scripts/phase-runner.py --phase 4 --plan-dir docs/plans --step review
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from textwrap import dedent


# ── Defaults ──────────────────────────────────────────────────────────

DEFAULT_MODEL = "sonnet"
BUILD_MODEL = "sonnet"
REVIEW_MODEL = "sonnet"
MAX_PARALLEL = 2
MAX_BUILD_RETRIES = 2
MAX_FIX_CYCLES = 1
CLAUDE_TIMEOUT = 600  # 10 min per step

# Accumulated cost across all subprocess calls
_total_cost = 0.0


# ── Cache Profiles ────────────────────────────────────────────────────
#
# Prompt caching keys on (system_prompt + tool_set). Calls sharing the
# same profile hit the 5-minute ephemeral cache — 2nd+ calls pay 1/10th.
#
# Profile A: "writer" — implement, build-fix, review-fix
# Profile B: "reader" — build-verify, reviews (read-only analysis)
#
# We use 2 profiles instead of 7 unique tool sets, so a full phase run
# creates at most 2 cache entries instead of 7.

CACHE_PROFILES = {
    "writer": {
        "tools": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        "system_prompt": (
            "You are a code agent working in an isolated git worktree. "
            "Follow instructions precisely. Write code when asked. "
            "Fix code when asked. Do not deviate from the task."
        ),
    },
    "reader": {
        "tools": ["Read", "Glob", "Grep", "Write", "Bash"],
        "system_prompt": (
            "You are a code analysis agent working in an isolated git worktree. "
            "Read and analyze code. Write structured findings to files. "
            "Do not modify source code. Follow the output format exactly."
        ),
    },
}

def get_profile(name):
    """Return (tools, system_prompt) for a cache profile."""
    p = CACHE_PROFILES[name]
    return p["tools"], p["system_prompt"]


# ── CLI helpers ───────────────────────────────────────────────────────

def run_claude(prompt, *, model=DEFAULT_MODEL, profile=None,
               allowed_tools=None, working_dir=None, system_prompt=None,
               max_budget=None, add_dirs=None, label="claude"):
    """Run claude -p and return parsed JSON result.

    Use `profile` to set tools + system_prompt from CACHE_PROFILES.
    Explicit allowed_tools/system_prompt override the profile.
    """
    # Resolve profile → tools + system_prompt (explicit args override)
    if profile:
        p_tools, p_sys = get_profile(profile)
        if allowed_tools is None:
            allowed_tools = p_tools
        if system_prompt is None:
            system_prompt = p_sys

    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--dangerously-skip-permissions",
        "--output-format", "json",
        "--no-session-persistence",
    ]
    if allowed_tools:
        cmd += ["--allowed-tools", " ".join(allowed_tools)]
    if system_prompt:
        cmd += ["--system-prompt", system_prompt]
    if max_budget:
        cmd += ["--max-budget-usd", str(max_budget)]
    if add_dirs:
        for d in add_dirs:
            cmd += ["--add-dir", d]

    env = {**os.environ, "CLAUDECODE": ""}

    print(f"  [{label}] launching (model={model})...")
    t0 = time.time()

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=working_dir, env=env, timeout=CLAUDE_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"Timed out after {CLAUDE_TIMEOUT}s", "is_error": True}

    elapsed = time.time() - t0

    if proc.returncode != 0 and not proc.stdout.strip():
        return {
            "error": proc.stderr.strip() or f"Exit code {proc.returncode}",
            "is_error": True,
        }

    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": f"Bad JSON output: {proc.stdout[:200]}", "is_error": True}

    cost = result.get("total_cost_usd", 0)
    usage = result.get("usage", {})
    cache_created = usage.get("cache_creation_input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    cache_info = ""
    if cache_read > 0:
        cache_info = f" [cache HIT: {cache_read} tokens read]"
    elif cache_created > 0:
        cache_info = f" [cache MISS: {cache_created} tokens created]"
    print(f"  [{label}] done in {elapsed:.0f}s (${cost:.4f}){cache_info}")

    # Accumulate cost for phase summary
    global _total_cost
    _total_cost += cost

    return result


def run_parallel_claude(tasks, *, max_workers=MAX_PARALLEL):
    """Run multiple claude -p calls in parallel. Returns list of results."""
    results = [None] * len(tasks)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {}
        for i, task in enumerate(tasks):
            future = pool.submit(run_claude, **task)
            futures[future] = i
        for future in as_completed(futures):
            idx = futures[future]
            results[idx] = future.result()
    return results


# ── Artifact gates ────────────────────────────────────────────────────

def gate_file_exists(path, name):
    """Check that a file exists and is non-empty."""
    p = Path(path)
    if not p.exists():
        print(f"  GATE FAIL: {name} not found at {path}")
        return False
    if p.stat().st_size == 0:
        print(f"  GATE FAIL: {name} is empty at {path}")
        return False
    print(f"  GATE OK: {name}")
    return True


def gate_build_result(worktree):
    """Check build-result.json exists and parse status."""
    path = Path(worktree) / ".orchestrate" / "build-result.json"
    if not gate_file_exists(path, "build-result.json"):
        return None
    with open(path) as f:
        data = json.load(f)
    status = data.get("status", "unknown")
    errors = data.get("error_count", 0)
    print(f"  BUILD: {status} ({errors} errors)")
    return data


def gate_reviews(worktree):
    """Check all 3 review files exist and parse severity summaries."""
    reviews = {}
    all_ok = True
    for name in ["test-review", "code-review", "perf-review"]:
        path = Path(worktree) / ".orchestrate" / f"{name}.md"
        if not gate_file_exists(path, f"{name}.md"):
            all_ok = False
            continue
        content = path.read_text()
        # Parse the summary header
        p0 = _extract_count(content, "P0")
        p1 = _extract_count(content, "P1")
        p2 = _extract_count(content, "P2")
        p3 = _extract_count(content, "P3")
        verdict = _extract_verdict(content)
        reviews[name] = {
            "p0": p0, "p1": p1, "p2": p2, "p3": p3,
            "verdict": verdict,
        }
        print(f"  {name}: P0={p0} P1={p1} P2={p2} P3={p3} ({verdict})")
    return reviews if all_ok else None


def _extract_count(text, level):
    match = re.search(rf"{level}:\s*(\d+)", text)
    return int(match.group(1)) if match else 0


def _extract_verdict(text):
    match = re.search(r"verdict:\s*(\S+)", text)
    return match.group(1) if match else "unknown"


# ── Plan parsing ──────────────────────────────────────────────────────

def parse_manifest(plan_dir):
    """Read manifest.md and extract spec info."""
    manifest_path = Path(plan_dir) / "manifest.md"
    if not manifest_path.exists():
        sys.exit(f"Error: manifest.md not found in {plan_dir}")
    content = manifest_path.read_text()
    return content


def parse_specs_for_phase(plan_dir, phase_num):
    """Find and read spec files for a given phase."""
    manifest = parse_manifest(plan_dir)
    specs = []

    # Parse the Phase/Sprint/Spec Map table
    for line in manifest.split("\n"):
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 5:
            continue
        try:
            p = int(cols[0])
        except ValueError:
            continue
        if p != phase_num:
            continue

        spec_name = cols[2]
        status = cols[4]
        if "dropped" in status or "completed" in status:
            continue

        spec_path = Path(plan_dir) / "specs" / f"{spec_name}-spec.md"
        if spec_path.exists():
            specs.append({
                "name": spec_name,
                "path": str(spec_path),
                "content": spec_path.read_text(),
                "status": status,
            })
        else:
            print(f"  Warning: spec file not found: {spec_path}")
    return specs


def detect_build_command(git_root):
    """Detect build command from project files."""
    root = Path(git_root)
    if (root / "project.yml").exists():
        # Detect scheme name from project.yml
        scheme = "App"
        yml_text = (root / "project.yml").read_text()
        match = re.search(r"^name:\s*(.+)", yml_text, re.MULTILINE)
        if match:
            scheme = match.group(1).strip()

        # Detect platform
        platform = "visionOS Simulator"
        device = "Apple Vision Pro"
        if "visionOS" in yml_text or "xros" in yml_text:
            platform = "visionOS Simulator"
            device = "Apple Vision Pro"
        elif "iOS" in yml_text:
            platform = "iOS Simulator"
            device = "iPhone 16 Pro"

        return (
            f"xcodegen generate && set -o pipefail && "
            f"xcodebuild -scheme {scheme} "
            f"-destination 'platform={platform},name={device}' "
            f"build 2>&1 | xcbeautify"
        )
    elif (root / "Package.swift").exists():
        return "swift build"
    elif (root / "package.json").exists():
        return "npm run build"
    return None


def extract_changed_files(specs):
    """Extract file paths from spec file tables."""
    files = {"create": [], "modify": []}
    for spec in specs:
        in_table = False
        for line in spec["content"].split("\n"):
            if "| File " in line and "| Action " in line:
                in_table = True
                continue
            if in_table and line.startswith("|"):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 2 and cols[0] != "---":
                    action = cols[1].lower() if len(cols) > 1 else ""
                    if "create" in action:
                        files["create"].append(cols[0])
                    elif "modify" in action:
                        files["modify"].append(cols[0])
            elif in_table and not line.startswith("|"):
                in_table = False
    return files


# ── Protocol steps ────────────────────────────────────────────────────

def step_worktree(git_root, phase_num, phase_slug):
    """Step 1: Create worktree."""
    project = Path(git_root).name
    branch = f"orchestrate/phase-{phase_num}-{phase_slug}"
    worktree = str(Path(git_root).parent / f"{project}-phase-{phase_num}")

    print(f"\n{'='*60}")
    print(f"STEP 1: Create worktree")
    print(f"  branch: {branch}")
    print(f"  path:   {worktree}")
    print(f"{'='*60}")

    if Path(worktree).exists():
        print(f"  Worktree already exists at {worktree}")
        # Check if branch has commits (resume case)
        try:
            result = subprocess.run(
                ["git", "-C", worktree, "log", "--oneline", "-1"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                print(f"  Last commit: {result.stdout.strip()}")
        except Exception:
            pass
        return worktree, branch

    result = subprocess.run(
        ["git", "-C", git_root, "worktree", "add", worktree, "-b", branch],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"Failed to create worktree: {result.stderr}")

    # Symlink .claude
    claude_dir = Path(git_root) / ".claude"
    claude_link = Path(worktree) / ".claude"
    if claude_dir.exists() and not claude_link.exists():
        os.symlink(str(claude_dir), str(claude_link))

    # Create artifact directory
    (Path(worktree) / ".orchestrate").mkdir(parents=True, exist_ok=True)

    print("  Worktree created.")
    return worktree, branch


def step_implement(worktree, specs, model, max_parallel, git_root):
    """Step 2: Launch implementer agents in parallel."""
    print(f"\n{'='*60}")
    print(f"STEP 2: Implement ({len(specs)} specs)")
    print(f"{'='*60}")

    tasks = []
    for spec in specs:
        # Extract files to read and modify from the spec
        prompt = dedent(f"""\
            You are implementing a spec in a visionOS project worktree.
            Write code, nothing else.

            WORKING DIRECTORY: {worktree}
            All file operations MUST use absolute paths under this directory.

            ## Spec
            {spec['content']}

            ## Rules
            - Read the existing source files in the worktree before modifying.
            - Write code in the worktree directory only.
            - Follow existing code style and patterns (Swift 6, @MainActor, RealityKit ECS).
            - Do not run builds or tests — a separate step handles that.
            - Do not explore files outside the spec scope.
            - Do not refactor or improve code you weren't asked to touch.
            - If creating a new file, make sure it's in the correct subdirectory.
        """)

        tasks.append({
            "prompt": prompt,
            "model": model,
            "profile": "writer",
            "working_dir": worktree,
            "add_dirs": [worktree, git_root],
            "label": f"impl-{spec['name']}",
        })

    results = run_parallel_claude(tasks, max_workers=max_parallel)

    for i, (spec, result) in enumerate(zip(specs, results)):
        if result.get("is_error"):
            print(f"  FAIL: {spec['name']}: {result.get('error', 'unknown')}")
        else:
            print(f"  OK: {spec['name']}")

    failed = [s["name"] for s, r in zip(specs, results) if r.get("is_error")]
    if failed:
        print(f"\n  Implementation failed for: {', '.join(failed)}")
        return False
    return True


def step_build(worktree, build_cmd, model=BUILD_MODEL):
    """Step 3: Build verification with retry loop."""
    print(f"\n{'='*60}")
    print(f"STEP 3: Build verification")
    print(f"{'='*60}")

    for attempt in range(1, MAX_BUILD_RETRIES + 2):
        prompt = dedent(f"""\
            Run the build command and report results. Nothing else.

            WORKING DIRECTORY: {worktree}

            ## Build Command
            cd "{worktree}" && {build_cmd}

            ## Output
            Write results to: {worktree}/.orchestrate/build-result.json

            Format:
            {{
              "status": "passed" or "failed",
              "exit_code": <number>,
              "error_count": <number>,
              "warning_count": <number>,
              "errors": ["file:line: error message", ...],
              "warnings_summary": "N warnings (types)"
            }}

            ## Rules
            - Run the build command once.
            - If project.yml exists, run xcodegen generate before xcodebuild.
            - Capture errors accurately — do not invent or omit errors.
            - Write the JSON file even if the build passes.
            - Do not fix code. Do not modify any source files.
        """)

        result = run_claude(
            prompt, model=model,
            profile="reader",
            working_dir=worktree,
            add_dirs=[worktree],
            label=f"build-{attempt}",
        )

        build_data = gate_build_result(worktree)

        if build_data is None:
            print(f"  Build result file missing (attempt {attempt})")
            if attempt > MAX_BUILD_RETRIES:
                return None
            continue

        if build_data.get("status") == "passed":
            return build_data

        if attempt > MAX_BUILD_RETRIES:
            print(f"  Build failed after {MAX_BUILD_RETRIES + 1} attempts")
            return build_data

        # Launch fixer
        errors = build_data.get("errors", [])
        print(f"  Build failed with {len(errors)} errors, launching fixer...")
        fix_prompt = dedent(f"""\
            Fix the build errors listed below. Only fix what's broken — do not refactor.

            WORKING DIRECTORY: {worktree}

            ## Build Errors
            {chr(10).join(errors[:20])}

            ## Rules
            - Fix ONLY the listed errors.
            - Do not change code that isn't related to the errors.
            - If a file is missing from the project and a project.yml exists,
              verify the file's directory is listed in project.yml sources.
            - Do not run the build yourself — a separate step will verify.
        """)
        run_claude(
            fix_prompt, model=model,
            profile="writer",
            working_dir=worktree,
            add_dirs=[worktree],
            label=f"fix-build-{attempt}",
        )

    return None


def step_review(worktree, changed_files, model=REVIEW_MODEL):
    """Step 4: Three parallel review agents with artifact gates."""
    print(f"\n{'='*60}")
    print(f"STEP 4: Reviews (3 parallel agents)")
    print(f"{'='*60}")

    file_list = "\n".join(f"- {f}" for f in changed_files["create"] + changed_files["modify"])

    review_configs = [
        {
            "name": "test-review",
            "focus": "test quality",
            "instructions": dedent("""\
                Evaluate: coverage gaps, assertion strength, edge cases, error paths.
                Severity guide:
                - P0: Missing tests for critical paths (data loss, security, crash)
                - P1: No tests at all for a new public type or function
                - P2: Weak assertions (testing existence but not correctness)
                - P3: Minor gaps (edge cases, naming)
            """),
        },
        {
            "name": "code-review",
            "focus": "code quality",
            "instructions": dedent("""\
                Evaluate: SOLID principles, security, error handling, naming, architecture.
                Severity guide:
                - P0: Security vulnerability, data loss risk, crash in production
                - P1: Logic error, missing error handling on external input, concurrency issue
                - P2: Code smell, unnecessary complexity, poor naming
                - P3: Style nit, minor improvement opportunity
            """),
        },
        {
            "name": "perf-review",
            "focus": "performance",
            "instructions": dedent("""\
                Evaluate: runtime efficiency, memory allocation, unnecessary work,
                N+1 patterns, main thread blocking, resource leaks.
                Severity guide:
                - P0: Main thread blocking, unbounded allocation, O(n²) on large input
                - P1: Unnecessary repeated work, missing caching for expensive ops
                - P2: Suboptimal but not harmful (could be faster, not urgent)
                - P3: Micro-optimization opportunity
            """),
        },
    ]

    tasks = []
    for cfg in review_configs:
        prompt = dedent(f"""\
            Review {cfg['focus']} for changes in this worktree. Write findings to a file.

            WORKING DIRECTORY: {worktree}

            ## What Changed This Phase
            {file_list}

            ## Instructions
            1. Read the source files that were created or modified this phase.
            2. Read any related test files that exist for those sources.
            3. {cfg['instructions']}
            4. Write your findings to: {worktree}/.orchestrate/{cfg['name']}.md

            ## Output Format
            The file MUST start with this header block:

            ## Summary
            - P0: {{count}}
            - P1: {{count}}
            - P2: {{count}}
            - P3: {{count}}
            - verdict: {{clean|p2_p3_only|p0_p1_found}}

            Then list each finding with severity, file, line, description, and recommended fix.

            ## Rules
            - Only review files changed in this phase.
            - Do not modify any code.
            - Write the file even if everything is clean (just zeros in the header).
        """)

        tasks.append({
            "prompt": prompt,
            "model": model,
            "profile": "reader",
            "working_dir": worktree,
            "add_dirs": [worktree],
            "label": cfg["name"],
        })

    run_parallel_claude(tasks, max_workers=3)

    reviews = gate_reviews(worktree)
    return reviews


def _extract_findings_by_severity(worktree, severity):
    """Extract findings of a specific severity (P0/P1/P2/P3) from review files."""
    findings = []
    for name in ["test-review", "code-review", "perf-review"]:
        path = Path(worktree) / ".orchestrate" / f"{name}.md"
        if not path.exists():
            continue
        content = path.read_text()
        # Split into sections and collect those matching the severity
        lines = content.split("\n")
        in_section = False
        section_lines = []
        for line in lines:
            # Match headers like "### P1-1", "### P1-01", "### P2-1 —"
            if re.match(rf"###\s+{severity}[-\s]", line):
                in_section = True
                section_lines.append(line)
            elif line.startswith("### ") and in_section:
                in_section = False
            elif in_section:
                section_lines.append(line)
        if section_lines:
            findings.append(f"### From {name}:\n" + "\n".join(section_lines))
    return findings


def _run_severity_fix(worktree, severity, findings, model, label):
    """Run a fixer agent for a single severity level."""
    prompt = dedent(f"""\
        Fix the {severity} findings from code review. Only fix {severity} items.

        WORKING DIRECTORY: {worktree}
        All file operations MUST use absolute paths under this directory.

        ## {severity} Findings to Fix
        {chr(10).join(findings)}

        ## Rules
        - Fix ONLY the {severity} items listed above.
        - Do not fix other severity levels.
        - Do not refactor or improve code beyond the findings.
        - Read each file before modifying it.
        - For new test files, use Swift Testing framework (@Test, #expect).
        - Follow existing code patterns (Swift 6, @MainActor, RealityKit ECS).
        - If an item is already fixed in the current code, note it in the report and skip.
        - Write a brief report to: {worktree}/.orchestrate/fix-report-{severity.lower()}.md
          listing what you changed and why.
    """)

    return run_claude(
        prompt, model=model,
        profile="writer",
        working_dir=worktree,
        add_dirs=[worktree],
        label=label,
    )


def step_fix_findings(worktree, reviews, changed_files, model=DEFAULT_MODEL):
    """Step 5: Fix review findings in three sequential passes — P1, P2, P3.

    Each severity gets its own subprocess agent. Sequential so later fixers
    see changes from earlier ones (P1 fixes may resolve some P2/P3 items).
    P0 runs with P1 if present.
    """
    total_p0 = sum(r["p0"] for r in reviews.values())
    total_p1 = sum(r["p1"] for r in reviews.values())
    total_p2 = sum(r["p2"] for r in reviews.values())
    total_p3 = sum(r["p3"] for r in reviews.values())
    total = total_p0 + total_p1 + total_p2 + total_p3

    if total == 0:
        print(f"\n  No findings — skipping fix step.")
        return reviews

    print(f"\n{'='*60}")
    print(f"STEP 5: Fix findings ({total_p0} P0, {total_p1} P1, {total_p2} P2, {total_p3} P3)")
    print(f"{'='*60}")

    # Pass 1: P0 + P1 (combined — both are critical)
    if total_p0 + total_p1 > 0:
        p0_findings = _extract_findings_by_severity(worktree, "P0")
        p1_findings = _extract_findings_by_severity(worktree, "P1")
        combined = p0_findings + p1_findings
        if combined:
            print(f"\n  --- Pass 1: P0/P1 ({total_p0 + total_p1} items) ---")
            _run_severity_fix(worktree, "P0/P1", combined, model, "fix-p0p1")

    # Pass 2: P2
    if total_p2 > 0:
        p2_findings = _extract_findings_by_severity(worktree, "P2")
        if p2_findings:
            print(f"\n  --- Pass 2: P2 ({total_p2} items) ---")
            _run_severity_fix(worktree, "P2", p2_findings, model, "fix-p2")

    # Pass 3: P3
    if total_p3 > 0:
        p3_findings = _extract_findings_by_severity(worktree, "P3")
        if p3_findings:
            print(f"\n  --- Pass 3: P3 ({total_p3} items) ---")
            _run_severity_fix(worktree, "P3", p3_findings, model, "fix-p3")

    # Re-run all reviews to verify fixes
    print(f"\n  Re-running all reviews to verify fixes...")
    new_reviews = step_review(worktree, changed_files, model=model)
    if new_reviews:
        reviews.update(new_reviews)

    return reviews


def step_commit(worktree, phase_num, specs, commit_msg=None):
    """Step 6: Commit changes."""
    print(f"\n{'='*60}")
    print(f"STEP 6: Commit")
    print(f"{'='*60}")

    # Remove orchestrate artifacts
    orch_dir = Path(worktree) / ".orchestrate"
    if orch_dir.exists():
        import shutil
        shutil.rmtree(orch_dir)

    # Stage and commit
    subprocess.run(["git", "-C", worktree, "add", "-A"], check=True)

    # Check if there are changes to commit
    status = subprocess.run(
        ["git", "-C", worktree, "status", "--porcelain"],
        capture_output=True, text=True,
    )
    if not status.stdout.strip():
        # Check if there are staged changes
        diff = subprocess.run(
            ["git", "-C", worktree, "diff", "--cached", "--stat"],
            capture_output=True, text=True,
        )
        if not diff.stdout.strip():
            print("  No changes to commit.")
            return None

    if commit_msg is None:
        spec_names = [s["name"] for s in specs]
        spec_refs = ", ".join(f"docs/plans/specs/{n}-spec.md" for n in spec_names)
        commit_msg = (
            f"orchestrate(phase-{phase_num}/sprint-1): {' + '.join(spec_names)}\n\n"
            f"Specs: {spec_refs}\n\n"
            f"Co-Authored-By: Claude <noreply@anthropic.com>"
        )

    result = subprocess.run(
        ["git", "-C", worktree, "commit", "-m", commit_msg],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  Commit failed: {result.stderr}")
        return None

    # Get commit hash
    sha = subprocess.run(
        ["git", "-C", worktree, "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
    print(f"  Committed: {sha}")
    return sha


def step_merge(git_root, branch, worktree, phase_num, phase_title):
    """Step 7: Merge and cleanup."""
    print(f"\n{'='*60}")
    print(f"STEP 7: Merge + cleanup")
    print(f"{'='*60}")

    result = subprocess.run(
        ["git", "-C", git_root, "merge", branch, "--no-ff",
         "-m", f"Merge orchestrate phase {phase_num}: {phase_title}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        if "CONFLICT" in result.stderr or "CONFLICT" in result.stdout:
            print(f"  MERGE CONFLICT — resolve manually.")
            print(result.stdout)
            return False
        print(f"  Merge failed: {result.stderr}")
        return False

    merge_sha = subprocess.run(
        ["git", "-C", git_root, "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
    print(f"  Merged: {merge_sha}")

    # Cleanup
    subprocess.run(
        ["git", "-C", git_root, "worktree", "remove", worktree, "--force"],
        capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", git_root, "branch", "-d", branch],
        capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", git_root, "worktree", "prune"],
        capture_output=True, text=True,
    )
    print("  Worktree cleaned up.")
    return True


def step_progress(plan_dir, phase_num, specs, reviews, commit_sha, build_status):
    """Step 9: Update progress.md and manifest.md."""
    print(f"\n{'='*60}")
    print(f"STEP 9: Update progress")
    print(f"{'='*60}")

    spec_names = [s["name"] for s in specs]

    # Build review summary
    review_lines = []
    if reviews:
        for name, r in reviews.items():
            review_lines.append(
                f"  - **{name}:** P0:{r['p0']} P1:{r['p1']} P2:{r['p2']} P3:{r['p3']}"
            )
    else:
        review_lines.append("  - Reviews not run")

    # Compute overall verdict
    if reviews:
        total_p0 = sum(r["p0"] for r in reviews.values())
        total_p1 = sum(r["p1"] for r in reviews.values())
        if total_p0 + total_p1 > 0:
            verdict = "p0_p1_found"
        elif any(r["p2"] + r["p3"] > 0 for r in reviews.values()):
            verdict = "p2_p3_only"
        else:
            verdict = "clean"
    else:
        verdict = "not_run"

    today = time.strftime("%Y-%m-%d")

    progress_entry = dedent(f"""\

        ### Phase {phase_num}, Sprint 1: {' + '.join(spec_names)} (completed {today})
        - **Status:** completed
        - **Commit:** {commit_sha or 'none'}
        - **Specs:** {', '.join(spec_names)}
        - **Build:** {build_status or 'unknown'}
        - **Review verdict:** {verdict}
        {chr(10).join(review_lines)}
    """)

    progress_path = Path(plan_dir) / "progress.md"
    if progress_path.exists():
        content = progress_path.read_text()
        # Append before the "## 5-Question Reboot Check" if it exists
        if "## 5-Question Reboot Check" in content:
            content = content.replace(
                "## 5-Question Reboot Check",
                progress_entry + "\n## 5-Question Reboot Check",
            )
        else:
            content += progress_entry
        progress_path.write_text(content)
        print(f"  Updated progress.md")

    # Update manifest.md — change spec statuses from draft to completed
    manifest_path = Path(plan_dir) / "manifest.md"
    if manifest_path.exists():
        content = manifest_path.read_text()
        for spec_name in spec_names:
            content = content.replace(
                f"| {spec_name} | yes", f"| {spec_name} | yes"
            )
            # Replace status column (last column before |)
            content = re.sub(
                rf"(\| {re.escape(spec_name)} \|.*?\| )(draft|pending)(\s*\|?\s*)$",
                rf"\1completed\3",
                content,
                flags=re.MULTILINE,
            )
        manifest_path.write_text(content)
        print(f"  Updated manifest.md")


# ── Main pipeline ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Script-driven phase runner")
    parser.add_argument("--phase", type=int, required=True, help="Phase number")
    parser.add_argument("--plan-dir", required=True, help="Path to plan directory")
    parser.add_argument("--git-root", help="Git root (auto-detected if not set)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model for agents")
    parser.add_argument("--max-parallel", type=int, default=MAX_PARALLEL)
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    parser.add_argument(
        "--step", choices=["implement", "build", "review", "fix", "commit", "merge", "all"],
        default="all", help="Run only a specific step (for debugging/resume)",
    )
    parser.add_argument("--worktree", help="Existing worktree path (skip step 1)")
    parser.add_argument("--branch", help="Existing branch name (skip step 1)")
    args = parser.parse_args()

    # Resolve paths
    plan_dir = str(Path(args.plan_dir).resolve())
    git_root = args.git_root or subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    ).stdout.strip()

    if not git_root:
        sys.exit("Error: not in a git repository")

    # Parse specs
    specs = parse_specs_for_phase(plan_dir, args.phase)
    if not specs:
        sys.exit(f"Error: no pending specs found for phase {args.phase}")

    changed_files = extract_changed_files(specs)
    build_cmd = detect_build_command(git_root)

    # Compute phase slug
    slug_parts = [s["name"] for s in specs[:2]]
    phase_slug = "-".join(slug_parts)[:30]
    phase_title = " + ".join(s["name"] for s in specs)

    print(f"\n{'#'*60}")
    print(f"# Phase Runner — Phase {args.phase}: {phase_title}")
    print(f"# Specs: {len(specs)} | Model: {args.model}")
    print(f"# Build: {build_cmd or 'auto-detect'}")
    print(f"# Files: {len(changed_files['create'])} create, {len(changed_files['modify'])} modify")
    print(f"{'#'*60}")

    if args.dry_run:
        print("\n[DRY RUN] Would execute steps 1-9. Exiting.")
        for i, spec in enumerate(specs, 1):
            print(f"  Spec {i}: {spec['name']} ({spec['status']})")
        for f in changed_files["create"]:
            print(f"  + {f}")
        for f in changed_files["modify"]:
            print(f"  ~ {f}")
        return

    total_cost = 0.0
    t_start = time.time()

    # Step 1: Worktree
    if args.worktree and args.branch:
        worktree, branch = args.worktree, args.branch
    else:
        if args.step != "all" and args.step != "implement":
            sys.exit("Error: --worktree and --branch required when using --step")
        worktree, branch = step_worktree(git_root, args.phase, phase_slug)

    run_steps = args.step

    # Step 2: Implement
    if run_steps in ("all", "implement"):
        ok = step_implement(worktree, specs, args.model, args.max_parallel, git_root)
        if not ok:
            sys.exit("Implementation failed.")

    # Step 3: Build
    build_data = None
    if run_steps in ("all", "build"):
        build_data = step_build(worktree, build_cmd, model=BUILD_MODEL)
        if build_data is None or build_data.get("status") != "passed":
            sys.exit("Build failed — check errors and retry with --step build")

    # Step 4: Reviews
    reviews = None
    if run_steps in ("all", "review"):
        reviews = step_review(worktree, changed_files, model=REVIEW_MODEL)
        if reviews is None:
            print("  WARNING: Some review files missing. Retrying...")
            reviews = step_review(worktree, changed_files, model=REVIEW_MODEL)
            if reviews is None:
                sys.exit("Reviews failed — review files not created after retry")

    # Step 5: Fix P0/P1
    if run_steps in ("all", "fix") and reviews:
        reviews = step_fix_findings(worktree, reviews, changed_files, model=args.model)

    # Step 6: Commit
    commit_sha = None
    if run_steps in ("all", "commit"):
        commit_sha = step_commit(worktree, args.phase, specs)

    # Step 7: Merge
    if run_steps in ("all", "merge"):
        ok = step_merge(git_root, branch, worktree, args.phase, phase_title)
        if not ok:
            sys.exit("Merge failed — resolve conflicts and retry")

    # Step 9: Progress
    if run_steps == "all":
        build_status = build_data.get("status") if build_data else "unknown"
        step_progress(plan_dir, args.phase, specs, reviews, commit_sha, build_status)

    elapsed = time.time() - t_start
    print(f"\n{'#'*60}")
    print(f"# Phase {args.phase} complete in {elapsed/60:.1f} minutes")
    if reviews:
        total_p0 = sum(r["p0"] for r in reviews.values())
        total_p1 = sum(r["p1"] for r in reviews.values())
        total_p2 = sum(r["p2"] for r in reviews.values())
        total_p3 = sum(r["p3"] for r in reviews.values())
        print(f"# Reviews: P0={total_p0} P1={total_p1} P2={total_p2} P3={total_p3}")
    print(f"# Commit: {commit_sha or 'none'}")
    print(f"# Total cost: ${_total_cost:.4f}")
    print(f"{'#'*60}")


if __name__ == "__main__":
    main()
