---
name: phase-runner
description: Coordinator protocol that chains sub-agents through implement → build → review → fix → commit → merge, each in its own context window
---

# Phase Runner Protocol

The phase-runner is a **coordinator** that chains sub-agents. Each sub-agent gets its own context window, does one job, writes results to `.orchestrate/` files, and exits. The coordinator reads short summaries, decides what's next, and launches the next agent.

This keeps every step structurally unskippable — each is a separate Agent tool call.

## Input (provided in the orchestrator's prompt)

```
PHASE_MANIFEST    — phase number, title, tasks, files, acceptance criteria
SKILLS            — agent type + skill list from skill-matcher
CHEAT_SHEETS      — tech reference content from Stage 4 research
PROJECT_CONTEXT   — conventions, architecture, CLAUDE.md summary
DISPATCH_MODE     — "classic" or "team"
MAX_PARALLEL      — max agents per batch
MODEL             — model for sub-agents
GIT_ROOT          — absolute path to project git root
PLAN_DIR          — absolute path to plan directory
BUILD_CMD         — project build command (e.g. "xcodegen generate && xcodebuild ...")
TEST_CMD          — project test command (e.g. "/orbit test" or "swift test")
SPEC_DRIVEN       — true/false
SPEC_INFO         — if spec-driven: spec name, sprint number, requirements list
WORKFLOW_CONFIG   — execution settings from workflow.md or null
PROMPT_TEMPLATES  — rendered phase/continuation prompt templates or null
HANDOFF_PATH      — absolute path to handoff.md or null
PROGRESS_LOG_PATH — absolute path to progress-log.md or null
ATTEMPT_NUMBER    — 1 for first run, 2+ for retries
PREVIOUS_RESULT   — null for first run, or {status, error} from prior failed attempt
```

---

## Step 0: Read Handoff (coordinator does this)

```
if HANDOFF_PATH exists and file exists at that path:
    Read: HANDOFF_PATH
    Extract: LAST_PHASE, ARCH_DECISIONS, WORKSPACE_STATE
else:
    LAST_PHASE = null, ARCH_DECISIONS = []
```

If PROMPT_TEMPLATES exist and ATTEMPT_NUMBER == 1, render the phase template.
If ATTEMPT_NUMBER > 1, render the continuation template.
Store RENDERED_PROMPT for Step 2 (substitute WORKTREE_PATH after Step 1).

---

## Step 1: Create Worktree (coordinator does this)

```bash
GIT_ROOT={provided}
PROJECT_NAME=$(basename "$GIT_ROOT")
PHASE_NUM={phase.phase}
PHASE_SLUG=$(echo "{phase.title}" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 30)
BRANCH_NAME="orchestrate/phase-${PHASE_NUM}-${PHASE_SLUG}"
WORKTREE_PATH="${GIT_ROOT}/../${PROJECT_NAME}-phase-${PHASE_NUM}"

git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"

# Symlink .claude for skill/command access
if [ -d "${GIT_ROOT}/.claude" ] && [ ! -L "${WORKTREE_PATH}/.claude" ]; then
    ln -s "${GIT_ROOT}/.claude" "${WORKTREE_PATH}/.claude"
fi

# Copy CLAUDE.md
if [ -f "${GIT_ROOT}/CLAUDE.md" ] && [ ! -f "${WORKTREE_PATH}/CLAUDE.md" ]; then
    cp "${GIT_ROOT}/CLAUDE.md" "${WORKTREE_PATH}/CLAUDE.md"
fi

# Create artifact directory
mkdir -p "${WORKTREE_PATH}/.orchestrate"
```

If worktree or branch already exists → check for prior commits on the branch (resume case).

---

## Step 2: Implement (sub-agent)

Launch implementer agent(s) in the worktree. This is the only step that writes application code.

### Classic Mode

```python
batches = chunk(tasks, size=MAX_PARALLEL)
for batch in batches:
    for task in batch:
        Agent(
            description = f"Implement: {task.title}",
            subagent_type = "{agent_type}",  # from skill-matcher
            prompt = IMPLEMENTER_PROMPT(task),
            model = MODEL,
            run_in_background = True,
        )
    # Wait for batch to complete
```

### Team Mode

```python
TeamCreate(team_name="orchestrate-phase-{N}-{slug}")
for task in phase.tasks:
    TaskCreate(subject=task.title, description=task.description)
for task in phase.tasks:
    Agent(
        name = f"worker-{task.id}",
        subagent_type = "{agent_type}",
        team_name = "orchestrate-phase-{N}-{slug}",
        prompt = IMPLEMENTER_PROMPT(task),
        model = MODEL,
    )
# Wait for completion, then TeamDelete()
```

### IMPLEMENTER_PROMPT Template

```
You are implementing a task in a worktree. Write code, nothing else.

WORKING DIRECTORY: {WORKTREE_PATH}
All file operations MUST use this path.

## Task
{task.title}
{task.description}

## Files to Create/Modify
{task.files table}

## Acceptance Criteria
{task.acceptance_criteria}

## Technical Approach
{task.technical_approach}

## Cheat Sheets
{relevant cheat sheets from Stage 4}

## Project Conventions
{abbreviated CLAUDE.md + conventions}

## Rules
- Write code in the worktree directory only.
- Follow existing code style and patterns.
- Do not run builds or tests — a separate agent handles that.
- Do not explore files outside the task scope.
- Do not refactor or improve code you weren't asked to touch.
```

---

## Step 3: Build Verification (sub-agent)

Launch a build-verifier agent that runs the build command and writes results to a file.

```python
Agent(
    description = "Build verification",
    prompt = BUILD_VERIFIER_PROMPT,
    model = "haiku",  # build verification is mechanical
)
```

### BUILD_VERIFIER_PROMPT Template

```
Run the build command and report results. Nothing else.

WORKING DIRECTORY: {WORKTREE_PATH}

## Build Command
{BUILD_CMD}

If BUILD_CMD is empty, try these in order:
1. If project.yml exists: xcodegen generate && xcodebuild -scheme {scheme} -destination '{destination}' build
2. If Package.swift exists: swift build
3. If package.json exists: npm run build

## Output
Write results to: {WORKTREE_PATH}/.orchestrate/build-result.json

Format:
{
  "status": "passed" or "failed",
  "exit_code": <number>,
  "error_count": <number>,
  "warning_count": <number>,
  "errors": ["file:line: error message", ...],  // max 20
  "warnings_summary": "N warnings (comma spacing, unused vars, etc.)"
}

## Rules
- Run the build command once.
- If xcodegen/project.yml exists, ALWAYS run xcodegen generate before xcodebuild.
- Capture errors accurately — do not invent or omit errors.
- Write the JSON file even if the build passes.
- Do not fix code. Do not modify any source files.
```

### Build Retry Loop (coordinator logic)

```python
build_result = read_json(f"{WORKTREE_PATH}/.orchestrate/build-result.json")

retry = 0
while build_result.status == "failed" and retry < 2:
    retry += 1
    # Launch fixer agent with the error list
    Agent(
        description = f"Fix build errors (attempt {retry})",
        subagent_type = "{agent_type}",
        prompt = BUILD_FIXER_PROMPT(build_result.errors),
        model = MODEL,
    )
    # Re-run build verification
    Agent(
        description = "Rebuild after fix",
        prompt = BUILD_VERIFIER_PROMPT,
        model = "haiku",
    )
    build_result = read_json(f"{WORKTREE_PATH}/.orchestrate/build-result.json")

if build_result.status == "failed":
    return PHASE_RESULT(status="needs_user_input", error="Build failed after 2 fix attempts")
```

### BUILD_FIXER_PROMPT Template

```
Fix the build errors listed below. Only fix what's broken — do not refactor.

WORKING DIRECTORY: {WORKTREE_PATH}

## Build Errors
{errors from build-result.json}

## Rules
- Fix ONLY the listed errors.
- Do not change code that isn't related to the errors.
- If a file is missing from the project file and a project.yml exists,
  verify the file's directory is listed in project.yml sources.
- Do not run the build yourself — a separate agent will verify.
```

---

## Step 4: Reviews (3 sub-agents IN PARALLEL)

After build passes, launch all three review agents simultaneously. Each runs its review skill and writes findings to a file. Running them in parallel saves time since they're independent read-only analyses.

```python
# Launch all 3 in a single message (parallel Agent calls)
Agent(
    description = "Test quality review",
    prompt = TEST_REVIEW_PROMPT,
    model = MODEL,
    run_in_background = True,
)
Agent(
    description = "Code review",
    prompt = CODE_REVIEW_PROMPT,
    model = MODEL,
    run_in_background = True,
)
Agent(
    description = "Performance review",
    prompt = PERF_REVIEW_PROMPT,
    model = MODEL,
    run_in_background = True,
)
# Wait for all 3
```

### TEST_REVIEW_PROMPT Template

```
Review test quality for the code in this worktree. Write findings to a file.

WORKING DIRECTORY: {WORKTREE_PATH}

## What Changed This Phase
{list of created/modified files from phase manifest}

## Instructions
1. Read the source files that were created or modified this phase.
2. Read any test files that exist for those sources.
3. Evaluate: coverage gaps, assertion strength, edge cases, error paths.
4. Write your findings to: {WORKTREE_PATH}/.orchestrate/test-review.md

## Output Format (.orchestrate/test-review.md)
The file MUST start with this header block:

```
## Summary
- P0: {count}
- P1: {count}
- P2: {count}
- P3: {count}
- verdict: {clean|p2_p3_only|p0_p1_found}
```

Then list each finding with severity, file, line, description, and recommended fix.

## Severity Guide
- P0: Missing tests for critical paths (data loss, security, crash scenarios)
- P1: No tests at all for a new public type or function
- P2: Weak assertions (testing existence but not correctness)
- P3: Minor gaps (edge cases, naming)

## Rules
- Only review files changed in this phase.
- Do not modify any code.
- Do not run tests.
- Write the file even if everything is clean (just zeros in the header).
```

### CODE_REVIEW_PROMPT Template

```
Review code quality for changes in this worktree. Write findings to a file.

WORKING DIRECTORY: {WORKTREE_PATH}

## What Changed This Phase
{list of created/modified files from phase manifest}

## Instructions
1. Read the source files that were created or modified this phase.
2. Evaluate: SOLID principles, security, error handling, naming, architecture.
3. Write your findings to: {WORKTREE_PATH}/.orchestrate/code-review.md

## Output Format (.orchestrate/code-review.md)
The file MUST start with this header block:

```
## Summary
- P0: {count}
- P1: {count}
- P2: {count}
- P3: {count}
- verdict: {clean|p2_p3_only|p0_p1_found}
```

Then list each finding with severity, file, line, description, options, and recommendation.

## Severity Guide
- P0: Security vulnerability, data loss risk, crash in production
- P1: Logic error, missing error handling on external input, concurrency issue
- P2: Code smell, unnecessary complexity, poor naming
- P3: Style nit, minor improvement opportunity

## Rules
- Only review files changed in this phase.
- Do not modify any code.
- Write the file even if everything is clean.
```

### PERF_REVIEW_PROMPT Template

```
Review performance for changes in this worktree. Write findings to a file.

WORKING DIRECTORY: {WORKTREE_PATH}

## What Changed This Phase
{list of created/modified files from phase manifest}

## Instructions
1. Read the source files that were created or modified this phase.
2. Evaluate: runtime efficiency, memory allocation, unnecessary work, N+1 patterns,
   main thread blocking, resource leaks.
3. Write your findings to: {WORKTREE_PATH}/.orchestrate/perf-review.md

## Output Format (.orchestrate/perf-review.md)
The file MUST start with this header block:

```
## Summary
- P0: {count}
- P1: {count}
- P2: {count}
- P3: {count}
- verdict: {clean|p2_p3_only|p0_p1_found}
```

Then list each finding with severity, file, line, description, and recommendation.

## Severity Guide
- P0: Main thread blocking, unbounded allocation, O(n²) on large input
- P1: Unnecessary repeated work, missing caching for expensive ops
- P2: Suboptimal but not harmful (could be faster, not urgent)
- P3: Micro-optimization opportunity

## Rules
- Only review files changed in this phase.
- Do not modify any code.
- Write the file even if everything is clean.
```

---

## Step 5: Fix All Findings (3 sequential passes)

The coordinator reads the 3 review summary headers from `.orchestrate/`, then fixes
findings in three sequential passes. Sequential so later fixers see changes from earlier
ones — P1 fixes often resolve P2/P3 items, and the later agents correctly skip those.

```python
# Read summaries
test_review = parse_summary(f"{WORKTREE_PATH}/.orchestrate/test-review.md")
code_review = parse_summary(f"{WORKTREE_PATH}/.orchestrate/code-review.md")
perf_review = parse_summary(f"{WORKTREE_PATH}/.orchestrate/perf-review.md")

total_p0 = test_review.p0 + code_review.p0 + perf_review.p0
total_p1 = test_review.p1 + code_review.p1 + perf_review.p1
total_p2 = test_review.p2 + code_review.p2 + perf_review.p2
total_p3 = test_review.p3 + code_review.p3 + perf_review.p3

# Pass 1: P0 + P1 (critical — combined since both are urgent)
if total_p0 + total_p1 > 0:
    p0p1_findings = extract_findings_by_severity(["P0", "P1"])
    run_fixer(p0p1_findings, label="fix-p0p1", report="fix-report-p0p1.md")

# Pass 2: P2 (code smells, complexity — sees P1 fixes already applied)
if total_p2 > 0:
    p2_findings = extract_findings_by_severity(["P2"])
    run_fixer(p2_findings, label="fix-p2", report="fix-report-p2.md")

# Pass 3: P3 (nits, minor improvements — sees P1 + P2 fixes already applied)
if total_p3 > 0:
    p3_findings = extract_findings_by_severity(["P3"])
    run_fixer(p3_findings, label="fix-p3", report="fix-report-p3.md")

# Re-run all reviews to verify
new_reviews = step_review(...)
if still_has_p0_p1(new_reviews):
    return PHASE_RESULT(status="needs_user_input",
        error="P0/P1 findings persist after fix attempt")
```

### Why 3 Passes, Not 1

| Approach | Problem |
|----------|---------|
| Single agent, all severities | Times out at ~16 items (>10 min). Skips lower-severity items. |
| Parallel by severity | P2 fixer doesn't see P1 changes — tries to fix already-resolved items, causes conflicts. |
| Sequential by severity | Each pass sees prior changes. ~5-8 items per agent. Fits in timeout. Later agents skip resolved items. |

### REVIEW_FIXER_PROMPT Template (per severity)

```
Fix the {SEVERITY} findings from code review. Only fix {SEVERITY} items.

WORKING DIRECTORY: {WORKTREE_PATH}

## {SEVERITY} Findings to Fix
{extracted findings for this severity from all 3 review files}

## Rules
- Fix ONLY the {SEVERITY} items listed above.
- Do not fix other severity levels.
- Do not refactor or improve code beyond the findings.
- Read each file before modifying it.
- For new test files, use Swift Testing framework (@Test, #expect).
- If an item is already fixed in the current code, note it in the report and skip.
- Write a brief report to: {WORKTREE_PATH}/.orchestrate/fix-report-{severity}.md
  listing what you changed and why.
```

### Subprocess Implementation

When using `.claude/scripts/phase-runner.py`, each pass is a separate `claude -p` call.
The `_extract_findings_by_severity()` function parses review files and pulls only the
sections matching the target severity (e.g., `### P2-1`, `### P2-02`). The script's
artifact gate verifies fix reports exist before proceeding to the next pass.

---

## Step 6: Commit (coordinator does this)

```bash
cd "$WORKTREE_PATH"

# Remove .orchestrate/ artifacts before committing
rm -rf .orchestrate/

git add -A
```

Standard mode:
```bash
git commit -m "orchestrate(phase-{N}): {phase.title}

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Spec-driven mode:
```bash
git commit -m "orchestrate(phase-{N}/sprint-{M}): {spec.name} — {spec.overview}

Spec: docs/plans/specs/{spec.name}-spec.md
Requirements completed: {REQ-1, REQ-2, ...}

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Record the commit hash(es).

---

## Step 7: Merge + Cleanup (coordinator does this)

```bash
cd "$GIT_ROOT"
git merge "$BRANCH_NAME" --no-ff -m "Merge orchestrate phase ${PHASE_NUM}: {phase.title}"
```

If merge conflict → do NOT auto-resolve. Return `needs_user_input` with conflict file list.

On success:
```bash
git worktree remove "$WORKTREE_PATH" --force
git branch -d "$BRANCH_NAME"
git worktree prune
```

### 7b. Write Handoff (if HANDOFF_PATH is not null)

Overwrite HANDOFF_PATH with current state. Format:

```markdown
# Handoff: {project name}

## Architecture Decisions
{carry forward existing + append new from this phase}

## Last Completed Phase
name: {this phase title}
status: completed
summary: {2-3 sentences}
key_files: {from git diff --name-only}

## Current Phase
name: {next phase title or "none"}
status: ready

## Workspace State
branch: {current branch}
last_commit: {merge commit hash}
build_status: passing
```

Size guard: if >150 lines, keep only the 10 most recent architecture decisions.

### 7c. Append to Progress Log (if PROGRESS_LOG_PATH is not null)

Prepend session entry at the top of `## Sessions`:

```markdown
### Session {N} — Phase {phase.number}: {phase.title}
- **status**: completed
- **build**: passed
- **review_code**: {P0/P1/P2/P3 counts}
- **review_test**: {counts}
- **review_perf**: {counts}
- **fixes_applied**: {count}
- **commits**: {hashes}
- **next**: {what next phase should pick up}
```

---

## Step 8: Documentation Refresh (sub-agent, conditional)

Launch a doc-refresh agent to update codebase maps and tech docs. This runs on the main branch post-merge.

```python
# Only if mercator or chronicler exist
has_mercator = file_exists(f"{GIT_ROOT}/docs/.mercator.json")
has_chronicler = file_exists(f"{GIT_ROOT}/.chronicler/INDEX.md")

if has_mercator or has_chronicler:
    Agent(
        description = "Refresh docs post-merge",
        model = "sonnet",
        prompt = DOC_REFRESH_PROMPT,
    )
```

### DOC_REFRESH_PROMPT Template

```
Update project documentation after a phase merge.

WORKING DIRECTORY: {GIT_ROOT}

## Mercator
If docs/.mercator.json exists:
- Check structural changes: new/removed modules
- If changes detected: run `Skill: mercator-ai` with `Args: --diff`
- If no changes: skip

## Chronicler
If .chronicler/INDEX.md exists:
- Run `Skill: chronicler:regenerate`
- If >15 files changed, batch to the 10 most important

Report what was updated. Doc failures are non-blocking.
```

---

## Step 9: Update Progress (coordinator does this)

Append to `{PLAN_DIR}/progress.md`:

```markdown
### Phase {N}: {title}
- **Status:** completed
- **Build:** passed
- **Tests:** {passed/failed/skipped} ({X passing})
- **Review (code):** P0:{n} P1:{n} P2:{n} P3:{n}
- **Review (test):** P0:{n} P1:{n} P2:{n} P3:{n}
- **Review (perf):** P0:{n} P1:{n} P2:{n} P3:{n}
- **Fixes applied:** {count}
- **Commits:** {sha_list}
- **Docs:** mercator: {updated|skipped|n/a}, chronicler: {N files|skipped|n/a}
- **Deferred:** {P2/P3 items or "none"}
```

If spec-driven, also update manifest.md status and spec frontmatter.

---

## Step 10: Return PHASE_RESULT (coordinator does this)

```
## PHASE_RESULT
- status: completed|failed|needs_user_input
- phase: {N}
- title: {phase.title}
- commits: {comma-separated sha list, or "none"}
- build: passed|failed
- tests: passed|failed|skipped
- test_count: {X passing, Y failing}
- review_test: {P0: N, P1: N, P2: N, P3: N}
- review_code: {P0: N, P1: N, P2: N, P3: N}
- review_perf: {P0: N, P1: N, P2: N, P3: N}
- review_verdict: clean|p2_p3_only|p0_p1_found
- fixes_applied: {count}
- deferred_items: {count}
- mercator: updated|skipped|not_installed|error
- chronicler: {N}_files_regenerated|skipped|not_initialized|error
- error: {description if failed/needs_user_input, otherwise "none"}
- conflict_files: {list if merge conflict, otherwise "none"}
- duration: {approx minutes}
- handoff_updated: true|false|skipped
- progress_log_updated: true|false|skipped
- architecture_decisions: {count of new decisions}
```

This is the ONLY part the main orchestrator reads.

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Worktree creation fails | Return failed + error |
| All implementer agents fail | Return failed + error |
| Build fails after 2 fix attempts | Return needs_user_input + errors |
| P0/P1 persists after 1 fix cycle | Return needs_user_input + findings |
| Merge conflict | Return needs_user_input + conflict files |
| Review agent fails to write file | Re-launch that review agent once. If still no file → treat as P0 (review could not complete) |
| Doc refresh fails | Log error, do not block phase completion |

---

## Context Budget

The coordinator's context stays small because heavy work is in sub-agents:

| Step | Coordinator cost | Sub-agent cost (discarded) |
|------|-----------------|---------------------------|
| Worktree setup | ~500 tokens | — |
| Implement dispatch | ~1k tokens (agent launch + short result) | 15-30k per implementer |
| Build verify | ~500 tokens (launch + read JSON) | 2-5k per build run |
| 3 reviews | ~1.5k tokens (3 launches + 3 summary reads) | 5-10k per reviewer |
| Fix cycle | ~800 tokens (launch + read report) | 10-15k per fixer |
| Commit/merge | ~500 tokens | — |
| Doc refresh | ~500 tokens | 5-15k per doc tool |
| Progress update | ~300 tokens | — |

**Total coordinator: ~5-6k tokens per phase.** The orchestrator sees ~800 tokens of PHASE_RESULT. A 5-phase plan fits comfortably in one main context session.

---

## Dispatch Mode Details

### Classic Mode

Implementer agents run in parallel batches (max MAX_PARALLEL). Each gets its own task. The coordinator waits per batch.

### Team Mode

Uses Agent Teams for the implementation step only. The coordinator creates a team, spawns a lead + teammates, waits for completion, then shuts down the team. All subsequent steps (build, reviews, fixes) still use classic single-agent dispatch since they're sequential.

| Aspect | Classic | Team |
|--------|---------|------|
| Communication | Fire-and-forget | Inter-agent messaging |
| Coordination | Batch-wait | Lead relays findings |
| When to use | Independent tasks, no shared files | Shared files, task dependencies |
| Cost | Lower | Higher |
