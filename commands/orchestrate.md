---
name: orchestrate
description: "Orchestrate plan execution through a 6-stage pipeline: plan review, skill matching, worktree isolation, agent dispatch, testing, and code review. Use when user says /orchestrate, has a completed plan to execute, or wants to run a multi-phase implementation with parallel agents."
argument-hint: "[plan-directory or project-path]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Write", "Edit", "Task", "AskUserQuestion", "TaskCreate", "TaskUpdate", "TaskList", "Skill", "ToolSearch", "WebSearch"]
---

# Orchestrate

Automated pipeline that takes an `/interactive-planning` output and executes it through:
**Plan Review → Skill Matching → Worktree Isolation → Agent Dispatch → Orbit Testing → Code Review → Incremental Commits**

**Target:** "$ARGUMENTS" (defaults to current directory if empty)

---

## Argument Parsing

Parse `$ARGUMENTS` for flags and plan directory:

```
ARGS = "$ARGUMENTS"

# Extract flags
DRY_RUN = "--dry-run" in ARGS
RESUME = "--resume" in ARGS
MAX_PARALLEL = extract "--max-parallel N" (default: 3)
MODEL = extract "--model X" (default: "sonnet")
PHASE_ONLY = extract "--phase N" (default: null = all phases)
FORCE_TEAM = "--team" in ARGS
FORCE_NO_TEAM = "--no-team" in ARGS
FORCE_SUBPROCESS = "--subprocess" in ARGS
FORCE_NO_SUBPROCESS = "--no-subprocess" in ARGS

# Remaining argument is the plan directory
PLAN_DIR = first non-flag argument, or current directory
```

**Supported flags:**
| Flag | Description |
|------|-------------|
| `--dry-run` | Show full execution plan without running anything |
| `--resume` | Resume from last completed phase (reads progress.md) |
| `--max-parallel N` | Max agents per batch (default: 3) |
| `--model sonnet\|opus\|haiku` | Model for dispatched agents |
| `--phase N` | Execute only phase N (skip others) |
| `--team` | Force Agent Teams mode (requires experimental flag enabled) |
| `--no-team` | Force classic Task-based dispatch |
| `--subprocess` | Force subprocess phase-runner (default when script exists) |
| `--no-subprocess` | Force agent-based phase-runner (original architecture) |

**Examples:**
```
/orchestrate ./plans/my-feature
/orchestrate --dry-run ./plans/my-feature
/orchestrate --resume ./plans/my-feature
/orchestrate --phase 2 --max-parallel 2 ./plans/my-feature
/orchestrate --team ./plans/my-feature
/orchestrate --no-team --model opus ./plans/my-feature
```

---

## Mode Resolution

Check Agent Teams availability and resolve dispatch mode:

```
AGENT_TEAMS_ENABLED = env CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS == "1"

Resolution:
- FORCE_TEAM + not AGENT_TEAMS_ENABLED
  → ERROR: "Agent Teams not enabled. Add CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 to settings.json"
- FORCE_NO_TEAM
  → DISPATCH_MODE = "classic" (regardless of env)
- AGENT_TEAMS_ENABLED + not FORCE_NO_TEAM
  → DISPATCH_MODE = "team" (default when available)
- not AGENT_TEAMS_ENABLED + no flag
  → DISPATCH_MODE = "classic"
```

Store `DISPATCH_MODE` — passed to agent-dispatcher and displayed in Stage 5 gate.

---

## Dry-Run Mode

When `--dry-run` is set, run Stages 1-4 (ingest, review, match, research) then stop at Stage 5. The Stage 5 gate already shows the full execution plan — dry-run just prevents proceeding past it. No worktrees, no agents, no changes.

---

## Resume Mode

When `--resume` is set:

1. **TLDR-first progress scan** — let the TLDR hook summarize `progress.md` to get the ToC
   with phase headings and status markers. Don't read the full file.
2. From the TLDR summary, identify:
   - Completed phases (Status: completed) → skip
   - Resume point: first phase with Status: in_progress/pending/missing
   - Line number of the resume point for targeted offset read
3. **Targeted tail read** — read only from the last completed phase onward (~50-60 lines)
   to capture learnings, commit hashes, and any gotchas from recent work.
4. Check for orphaned worktrees from interrupted runs:
   ```bash
   git worktree list | grep "orchestrate/"
   ```
   If found → ask user: "Found orphaned worktree from previous run. Resume it or remove and restart?"
5. **Skip Stage 2 (REVIEW)** — the plan was already reviewed on the initial run.
   Jump straight from Stage 1 (INGEST) → Stage 3 (MATCH) for remaining phases only.
6. **Skip findings.md and project docs** — these don't change between phases.
7. Proceed with remaining phases from that point

### Spec-Driven Resume Enhancements

When `--resume` detects spec-driven mode (manifest.md exists in plan directory),
the resume path is significantly shorter than task-based:

1. **Read manifest.md** (always small, ~50 lines) → get the full spec map with statuses
2. **Git-log cross-reference** — verify completed specs against actual commits:
   ```bash
   git log --oneline --grep="orchestrate(" --format="%s"
   ```
   Parse spec names from commit messages. Any spec with a merged commit
   is definitively completed, regardless of progress.md state.
   Handles: crash before progress.md write, /clear before finisher ran, etc.

3. **Determine next spec** — first unblocked, uncommitted spec from manifest
4. **Read ONE spec file** — `docs/plans/specs/{next-spec}-spec.md`
5. **Stage skip behavior on spec-driven resume:**
   - Stage 2 (REVIEW): skip (same as task-based resume)
   - Stage 3 (MATCH): re-run for the single spec only (fast — one spec's keywords)
   - Stage 4 (RESEARCH): check if this spec's tech was already cached in `.claude/docs/`

6. **Context budget comparison:**
   ```
   Task-based resume:  ~300-500 lines (TLDR scans + offset reads of 2 files)
   Spec-driven resume: ~110-140 lines (manifest + progress tail + one spec)
   ```

7. **Proceed to Stage 6** for the current spec only.
   After the spec completes (test → review → commit → merge),
   update manifest.md status and progress.md for that spec.
   The user can then either:
   - Continue to the next spec in the same session, OR
   - `/clear` and `/orchestrate --resume` again (loads fresh, lean context)

---

## Pipeline Overview

```
/orchestrate [plan-dir]
  │
  ├─ Stage 1: INGEST   — Read plan files + project docs
  ├─ Stage 2: REVIEW   — Check phase quality, split/merge/enrich [SKIP on resume]
  ├─ Stage 3: MATCH    — Resolve skills per phase (registry → AgentReverse → web)
  ├─ Stage 4: RESEARCH — Fetch official docs for unfamiliar tech (Context7 → web → GitHub)
  ├─ Stage 5: GATE     — Show summary + research results, get user approval
  │
  └─ Stage 6: EXECUTE  — For each phase (sequential):
       ├─ 6a. Create worktree
       ├─ 6b. Dispatch agents (2-3 parallel, with doc context)
       ├─ 6c. /orbit test + test quality review
       ├─ 6d. /code-review-pro local (auto-fix P0/P1)
       ├─ 6d-1. Performance review
       ├─ 6e. Incremental commit + merge worktree
       └─ 6f. Cleanup + next phase
```

---

## Stage 1: INGEST

### Step 0: Resolve PLAN_DIR (always do this first)

```
RAW_DIR = first non-flag argument from ARGUMENTS, or current directory
# CRITICAL: Glob/Read tools require absolute paths. ~ is NOT expanded.
# Resolve immediately:
PLAN_DIR = Bash("realpath ${RAW_DIR}")  # e.g. /Users/quartershots/Source/neo-research/docs/plans
```

All subsequent file reads and globs MUST use this resolved absolute path.
If PLAN_DIR equals CWD, omit the `path` parameter from Glob calls (it defaults to CWD).

### Step 1: List plan directory contents

```
Bash("ls {PLAN_DIR}")   # one call — see what exists before searching
```

This tells you immediately whether you have `manifest.md` (spec-driven) or `task_plan.md` (task-based) and avoids blind globbing.

### Step 2: Ingest plan files

Follow `.claude/skills/orchestrator/references/plan-ingester.md` — it handles both spec-driven and task-based modes. Do NOT re-specify file discovery order here; the ingester's mode detection (manifest.md first, then task_plan.md) is authoritative.

### Step 3: Discover project docs

From the git root (use `git rev-parse --show-toplevel` for the absolute path):
```
Glob: **/CLAUDE.md (root + nested)
Glob: docs/**/*.md
Glob: docs/CODEBASE_MAP.md
```

### Step 4: Output

Raw phase array + project context object (format defined in plan-ingester.md).

### Resume-Aware Ingest (--resume)

**Step 0 still applies** — resolve PLAN_DIR to absolute path before any file access.

When `RESUME == true`, follow the Resume Ingest path in `.claude/skills/orchestrator/references/plan-ingester.md` (Steps R1–R5). Key rules:

1. TLDR-scan progress.md for the ToC, then targeted offset read (~50 lines from resume point)
2. For task-based: offset-read only pending phases from task_plan.md
3. For spec-driven: read manifest.md + single next spec file (3 small reads total)
4. Skip findings.md and project docs (already consumed on first run)
5. Output filtered phase array (pending/in_progress only) + minimal context

### Step 5: Extract Workflow Contract

If the plan-ingester output includes a `workflow` object:

```
WORKFLOW = context.workflow
if WORKFLOW:
    EXECUTION_CONFIG = WORKFLOW.execution
    PROMPT_TEMPLATES = WORKFLOW.templates
    HANDOFF_PATH = resolve_path(WORKFLOW.handoff.file, GIT_ROOT)
    PROGRESS_LOG_PATH = resolve_path(WORKFLOW.progress.file, GIT_ROOT)
else:
    # Backward compatible: no workflow.md, use defaults
    EXECUTION_CONFIG = {
        phase_runner: "subagent",
        max_phase_retries: 2,
        continuation_prompt: true,
        progress_enforcement: "strict",
        gates: { between_phases: "auto", on_failure: "retry" }
    }
    PROMPT_TEMPLATES = null
    HANDOFF_PATH = null
    PROGRESS_LOG_PATH = null
```

---

## Stage 2: REVIEW

**Skip condition:** If `RESUME == true` and progress.md has at least one phase with `Status: completed`, skip this stage entirely. The plan was already reviewed on the initial run — re-reviewing mid-execution is redundant and wastes tokens. Jump directly to Stage 3 (MATCH) for remaining phases only.

Follow `.claude/skills/orchestrator/references/plan-reviewer.md`:

Launch a **Plan agent** (subagent_type=Plan) with the ingested data. The agent:

1. Checks each phase for:
   - **Sizing**: >5 tasks or >3 modules → split
   - **Gaps**: Missing setup/migration/test/doc phases → insert
   - **Clarity**: Vague tasks → enrich with file targets from CODEBASE_MAP
   - **Dependencies**: Validate ordering, find parallelizable phases
   - **Confidence**: Score each phase high/medium/low

2. Produces:
   - Revised phase manifest (JSON-structured)
   - Change summary (what was modified and why)
   - Flagged items needing user clarification

---

## Stage 3: MATCH

Follow `.claude/skills/orchestrator/references/skill-matcher.md`:

For each reviewed phase:

1. **Registry lookup**: Read `.claude/skills/orchestrator/references/skill-registry.json`
   - Match phase keywords (languages, domains, file extensions) against registry
   - Select highest-priority skill set and agent type

2. **AgentReverse fallback** (if no registry match):
   - Call `mcp__agent-reverse__suggester_check`
   - If suggestion found → install permanently

3. **Web search fallback** (if AgentReverse has nothing):
   - `WebSearch("claude code skill {keywords}")`
   - If GitHub repo found → `agent-reverse analyze` → `install_capability`
   - Register repo: `suggester_add_repo`

4. **Final fallback**: `general-purpose` agent type

Output: skill assignment table per phase.

---

## Stage 4: RESEARCH

Follow `.claude/skills/orchestrator/references/tech-researcher.md`:

**Purpose**: Before any agent writes code, fetch official documentation for every unfamiliar technology in the plan. This is the **anti-slop layer** — it prevents agents from hallucinating APIs.

**Context offloading**: This stage uses the neo-research knowledge store to keep the main context clean. Heavy doc content goes into the `.mv2` store; only cheat sheets (compact summaries) come back into agent prompts.

### 4a. Identify Technologies

For each phase, extract technology names from:
- Task descriptions and file targets
- Language/domain fields in phase manifest
- findings.md technical decisions
- import statements or package references in existing code

### 4b. Check What's Known (knowledge store first)

For each technology, check (in order):
1. **Knowledge store**: Load `rlm_search` via ToolSearch, query `rlm_search(query="{tech} API", top_k=3)`. If results exist and are recent → mark as "store-cached", skip fetching
2. **Local cache**: `.claude/docs/{tech-name}/` — if exists and <7 days old → skip
3. **Loaded skills**: If skill-matcher assigned a specialized skill (e.g., `swift-engineering:grdb`) → the skill IS the docs, skip
4. **Known library**: Load `rlm_research` via ToolSearch, try `rlm_research(topic="{tech}")`. If it resolves (25+ libraries have hardcoded URLs) → fetches + auto-indexes in one call. Mark done.
5. **Context7**: Call `mcp__context7__resolve-library-id` → if found, mark for Context7 fetch (hook auto-indexes into store)
6. **Unknown**: Mark for web search

### 4c. Fetch Docs (parallel, max 2-3 research agents)

Launch `rlm-researcher` agents in parallel to research unfamiliar technologies. These agents have the neo-research MCP server loaded and can call `rlm_fetch`, `rlm_research`, and `rlm_ingest` directly — no CLI path issues, no context pollution.

**For known-library tech (step 4b.4 resolved it):**
Already indexed. Skip to 4d.

**For Context7-available tech:**
```
mcp__context7__resolve-library-id(libraryName: "{tech}", query: "API reference for {tech}")
mcp__context7__query-docs(libraryId: "...", query: "Getting started and basic usage")
mcp__context7__query-docs(libraryId: "...", query: "Complete API reference, all methods")
mcp__context7__query-docs(libraryId: "...", query: "Best practices and common pitfalls")
```
The `context7-to-mv2.sh` hook auto-indexes each Context7 response into the knowledge store.

**For web-only tech:**
Spawn `rlm-researcher` agent:
```
Task(
  subagent_type = "rlm-researcher",
  prompt = "Research {tech}. Use rlm_fetch for official doc URLs. Use WebSearch to find docs if URLs unknown. Index everything into the knowledge store. Return only an indexing report.",
  run_in_background = true
)
```
The agent indexes full content into the store — nothing comes back into the main context except a short report.

### 4d. Produce Cheat Sheets (from knowledge store)

For each researched technology, query the knowledge store to build a compact agent reference:
```
# Pull key information from the store (not from raw fetches)
rlm_ask(question="What are the core API methods, signatures, and usage patterns for {tech}?", top_k=10)
rlm_ask(question="What are common pitfalls and version-specific notes for {tech}?", top_k=5)
```

Write the cheat sheet:
```
Write: .claude/docs/{tech}/cheat-sheet.md

Contents:
- Installation / setup
- Core API (classes, methods, signatures)
- 3-5 usage patterns with code
- Common pitfalls
- Version notes
```

These cheat sheets are injected into agent prompts during Stage 6b (dispatch). They're typically 200-400 lines — far smaller than the full docs sitting in the knowledge store.

### 4e. Research Summary

Include in the user gate (Stage 5):
```markdown
## Tech Research
| Technology | Source | Status | Store |
|-----------|--------|--------|-------|
| memvid | rlm_research | Cheat sheet created | 12 pages indexed |
| GRDB | Loaded skill | Known — skipped | — |
| Vapor | Context7 (auto-indexed) | 3 pages cached | 3 pages indexed |
| custom-lib | rlm-researcher agent | Indexed from web | 8 pages indexed |
```

**Tip:** If agents later need deeper context during Stage 6, they can query `rlm_search` / `rlm_ask` directly from their worktree context. The full docs are in the store — cheat sheets are just the starting point.

---

## Stage 5: GATE — User Approval

Present the complete orchestration plan:

```markdown
## Orchestration Plan

### Plan Review Changes
[from Stage 2 change summary]

### Phase Execution Plan
| Phase | Title | Tasks | Agent Type | Skills | Confidence | Dispatch |
|-------|-------|-------|-----------|--------|------------|----------|
| 1 | ... | 3 | swift-engineer | swift-engineer, swift-arch | HIGH | classic |
| 2 | ... | 4 | feature-dev | code-architect | MEDIUM | team (shared files) |
...

### Research Artifacts Available
{from Stage 4 research summary}
| Topic | Artifacts | Usage |
|-------|-----------|-------|
| {slug} | expertise + store + skill + agent | Agents query via rlm_search(project="{slug}") |
| {slug} | expertise + store | Cheat sheet derived from expertise.md |
| — | None | Standard Context7/web research |

### Execution Config
- Phase executor: `.claude/agents/phase-runner.md` (dedicated agent, strict protocol)
- Dispatch mode: Per-phase auto-selection (see table above), override with --team/--no-team
- Dispatch: Sequential phases, parallel tasks within phase (max {MAX_PARALLEL} agents)
- Testing: /orbit test per phase
- Review: /code-review-pro per phase
- Commits: Incremental per phase via /commit-split
- Knowledge store: Agents use rlm_search for API lookups (no full doc reads)

### Workflow Contract
| Setting | Value |
|---------|-------|
| Source | {plan_dir}/workflow.md (or "none — using defaults") |
| Project type | {WORKFLOW.project.type or "unknown"} |
| Phase retries | {EXECUTION_CONFIG.max_phase_retries} |
| Between-phase gates | {EXECUTION_CONFIG.gates.between_phases} |
| Failure handling | {EXECUTION_CONFIG.gates.on_failure} |
| Progress enforcement | {EXECUTION_CONFIG.progress_enforcement} |
| Handoff file | {HANDOFF_PATH or "none"} |
| Prompt template | {"custom" if PROMPT_TEMPLATES else "built-in"} |
```

Use AskUserQuestion:
```
question: "Orchestration plan ready. How to proceed?"
options:
  - "Execute all phases" → proceed to Stage 5
  - "Execute specific phase" → ask which phase number
  - "Adjust plan" → go back to Stage 2
  - "Dry-run only" → show what would happen without executing
```

If any phases have confidence=low or need-clarification → ask specific questions first.

---

## Stage 6: EXECUTE (Phase-Runner Architecture)

### Execution Mode Resolution

```python
PHASE_RUNNER_SCRIPT = f"{GIT_ROOT}/.claude/scripts/phase-runner.py"
SCRIPT_EXISTS = file_exists(PHASE_RUNNER_SCRIPT)

if FORCE_NO_SUBPROCESS:
    EXEC_MODE = "agent"     # fallback to agent-based phase-runner
elif FORCE_SUBPROCESS or SCRIPT_EXISTS:
    EXEC_MODE = "subprocess"  # preferred — artifact-gated enforcement
else:
    EXEC_MODE = "agent"     # no script available
```

### Subprocess Mode (preferred)

When `EXEC_MODE == "subprocess"`, Stage 6 calls the phase-runner script via Bash.
The script runs each protocol step as a separate `claude -p` subprocess with artifact
gates between steps. No single agent can skip reviews, builds, or fixes.

```python
for phase in phases:
    result = Bash(
        f'python3 {PHASE_RUNNER_SCRIPT} '
        f'--phase {phase.phase} '
        f'--plan-dir {PLAN_DIR} '
        f'--git-root {GIT_ROOT} '
        f'--model {MODEL} '
        f'--max-parallel {MAX_PARALLEL}'
    )
    # Script updates progress.md and manifest.md directly
    # Parse exit code for success/failure
    if result.exit_code != 0:
        handle_phase_failure(phase, result.stderr)
```

**Fix step runs 3 sequential passes:** P0/P1 first, then P2, then P3. Each pass is a
separate subprocess. Later passes see earlier changes and skip already-resolved items.

**Zero main-context cost.** The script runs entirely outside the conversation window.
The orchestrator only sees the Bash exit code and can read progress.md for details.

### Agent Mode (fallback)

When `EXEC_MODE == "agent"`, the original agent-based phase-runner is used. Each phase
runs inside a subagent with its own context window. Known limitation: single agents
tend to skip review steps. Use `--no-subprocess` to force this mode.

**Key design:** Each phase runs inside a **subagent with its own context window**. The main
orchestrator is a thin dispatch loop — it builds a prompt, launches the agent, and reads a
~20-line structured result. This keeps the main context at ~800 tokens per phase instead of
~15-30k, so a 5-phase plan can complete without hitting the context limit.

The heavy work (worktree lifecycle, agent dispatch, test/review/fix retry loops, commit, merge,
cleanup) all happens inside the phase-runner agent. Details are in
`.claude/skills/orchestrator/references/phase-runner.md`.

### Initialize State

```bash
GIT_ROOT=$(git rev-parse --show-toplevel)
SESSION_ID=$(date +%s)
STATE_DIR="$SCRATCHPAD_DIR/orchestrate/$SESSION_ID"
mkdir -p "$STATE_DIR"
```

### Per-Phase Dispatch Mode Selection

If the user passed `--team` or `--no-team`, that overrides everything. Otherwise, the
orchestrator picks the mode per-phase based on these signals:

```python
def select_dispatch_mode(phase, global_mode):
    # User override takes priority
    if FORCE_TEAM:
        return "team"
    if FORCE_NO_TEAM:
        return "classic"

    # Auto-select based on phase characteristics
    task_count = len(phase.tasks)
    has_shared_types = any(
        set(t1.files) & set(t2.files)
        for t1, t2 in combinations(phase.tasks, 2)
    )
    has_dependencies = any(t.dependsOn for t in phase.tasks)

    # Team mode triggers
    if task_count >= 4 and (has_shared_types or has_dependencies):
        return "team"   # enough tasks + cross-talk justifies coordination overhead
    if phase.confidence in ("low", "medium") and task_count >= 3:
        return "team"   # plan approval gate is valuable for uncertain phases

    # Classic mode (default)
    return "classic"    # simpler, cheaper, sufficient for independent tasks
```

| Condition | Mode | Reason |
|-----------|------|--------|
| 1-2 tasks | classic | No coordination needed |
| 3+ tasks, all independent files | classic | Cheaper, no cross-talk |
| 4+ tasks with shared files or deps | team | Lead relays file changes between workers |
| Low/medium confidence, 3+ tasks | team | Plan approval gate prevents wasted work |
| User passed `--team` | team | Explicit override |
| User passed `--no-team` | classic | Explicit override |

### Phase Loop

```python
for phase in phases:
    # 1. Select dispatch mode for this phase
    phase_dispatch_mode = select_dispatch_mode(phase, DISPATCH_MODE)

    # 2. Build the phase-runner prompt (read cheat sheets, project context)
    cheat_sheets = read_cheat_sheets(phase.technologies)  # from Stage 4
    prompt = build_phase_runner_prompt(
        phase_manifest = phase,
        skills = phase.skills,
        agent_type = phase.agentType,
        cheat_sheets = cheat_sheets,
        project_context = project_context,
        dispatch_mode = phase_dispatch_mode,
        max_parallel = MAX_PARALLEL,
        model = MODEL,
        git_root = GIT_ROOT,
        plan_dir = PLAN_DIR,
        spec_driven = SPEC_DRIVEN,
        spec_info = phase.spec_info if SPEC_DRIVEN else None,
        workflow_config = EXECUTION_CONFIG,
        prompt_templates = PROMPT_TEMPLATES,
        handoff_path = HANDOFF_PATH,
        progress_log_path = PROGRESS_LOG_PATH,
        attempt_number = 1,
        previous_result = None,
    )

    # 3. Launch the dedicated phase-runner agent
    #    Uses .claude/agents/phase-runner.md — a strict executor that follows
    #    the protocol exactly and always returns PHASE_RESULT.
    agent = Agent(
        description = f"Execute phase {phase.phase}: {phase.title}",
        subagent_type = "phase-runner",
        prompt = prompt,
        model = MODEL,
    )

    # 3. Parse the PHASE_RESULT block from agent output
    result = parse_phase_result(agent.output)

    # 4. Handle result
    if result.status == "completed":
        # Log success, proceed to next phase
        log_phase_complete(phase, result)

    elif result.status in ("failed", "needs_user_input"):
        # Retry logic using workflow config
        max_retries = EXECUTION_CONFIG.get("max_phase_retries", 2)
        on_failure = EXECUTION_CONFIG.get("gates", {}).get("on_failure", "retry")
        retry_count = 0

        while retry_count < max_retries and on_failure == "retry":
            retry_count += 1
            # Re-launch with continuation prompt
            retry_prompt = build_phase_runner_prompt(
                phase_manifest = phase,
                skills = phase.skills,
                agent_type = phase.agentType,
                cheat_sheets = cheat_sheets,
                project_context = project_context,
                dispatch_mode = phase_dispatch_mode,
                max_parallel = MAX_PARALLEL,
                model = MODEL,
                git_root = GIT_ROOT,
                plan_dir = PLAN_DIR,
                spec_driven = SPEC_DRIVEN,
                spec_info = phase.spec_info if SPEC_DRIVEN else None,
                workflow_config = EXECUTION_CONFIG,
                prompt_templates = PROMPT_TEMPLATES,
                handoff_path = HANDOFF_PATH,
                progress_log_path = PROGRESS_LOG_PATH,
                attempt_number = retry_count + 1,
                previous_result = {"status": result.status, "error": result.error},
            )

            agent = Agent(
                description = f"Retry phase {phase.phase}: {phase.title} (attempt {retry_count + 1})",
                subagent_type = "phase-runner",
                prompt = retry_prompt,
                model = MODEL,
            )
            result = parse_phase_result(agent.output)
            if result.status == "completed":
                break

        if result.status != "completed":
            # Exhausted retries or on_failure != "retry"
            user_choice = AskUserQuestion(
                question = f"Phase {phase.phase} failed after {retry_count + 1} attempt(s): {result.error}",
                options = [
                    "Fix manually and resume",
                    "Skip this phase",
                    "Abort orchestration",
                    "Retry phase from scratch",
                ]
            )
            handle_user_choice(user_choice, phase)

    # 5. Map refresh (conditional — only if structural changes)
    check_map_refresh(GIT_ROOT, phase)

    # 6. Between-phase gate (from workflow config)
    gate_mode = EXECUTION_CONFIG.get("gates", {}).get("between_phases", "auto")

    if gate_mode == "manual" and next_phase_exists:
        user_choice = AskUserQuestion(
            question = f"Phase {phase.phase} complete. Proceed to Phase {next_phase.phase}: {next_phase.title}?",
            header = "Phase Gate",
            options = [
                {"label": "Continue", "description": "Proceed to next phase"},
                {"label": "Review changes first", "description": "I want to inspect the code before continuing"},
                {"label": "Stop here", "description": "End orchestration at this point"}
            ]
        )
        if user_choice == "Stop here":
            break

    elif gate_mode == "review" and next_phase_exists:
        # Show what changed
        diff_summary = Bash(f"cd {GIT_ROOT} && git log --oneline -5")
        user_choice = AskUserQuestion(
            question = f"Phase {phase.phase} complete.\n\nRecent commits:\n{diff_summary}\n\nProceed to Phase {next_phase.phase}?",
            header = "Phase Gate (Review)",
            options = [
                {"label": "Continue", "description": "Looks good, proceed"},
                {"label": "Adjust", "description": "I need to make changes first"},
                {"label": "Stop", "description": "End orchestration"}
            ]
        )
        if user_choice == "Stop":
            break

    # "auto" → proceed without asking (default)
```

### Phase-Runner Prompt Construction

The orchestrator reads these files and injects their content into the prompt:

1. **Phase manifest** — title, tasks, files, acceptance criteria (from Stage 2/3)
2. **Cheat sheets** — `.claude/docs/{tech}/cheat-sheet.md` for each technology (from Stage 4)
3. **Project conventions** — abbreviated CLAUDE.md + CODEBASE_MAP section
4. **Execution instructions** — the full phase-runner protocol from `.claude/skills/orchestrator/references/phase-runner.md`
5. **Dispatch config** — mode, max parallel, model, git root, plan dir

The prompt tells the phase-runner agent to follow the phase-runner skill step-by-step and end its response with the `## PHASE_RESULT` structured block.

### What the Main Context Sees Per Phase

```
→ Agent launched: "Execute phase 2: Authentication module" (~1k tokens prompt reference)
← Agent returned: (~500 tokens)

## PHASE_RESULT
- status: completed
- phase: 2
- title: Authentication module
- commits: abc1234, def5678
- tests: passed
- test_count: 24 passing, 0 failing
- review: p2_p3_only
- deferred_items: 2
- error: none
- conflict_files: none
- duration: ~8 minutes
```

Total main context cost: ~800 tokens per phase. A 5-phase plan uses ~4k tokens for execution,
leaving the rest for Stages 1-5 and user interaction.

### Handling Failures and Retries

When a phase-runner returns `failed` or `needs_user_input`, the orchestrator uses the workflow
contract's retry logic. It re-launches the phase-runner up to `EXECUTION_CONFIG.max_phase_retries`
times (default: 2) with `attempt_number` incremented and `previous_result` populated. This gives
the retry agent context about what went wrong.

If retries are exhausted (or `on_failure` is not `"retry"`), the user gets four options:
1. "Fix manually and resume" → pause, user resolves, then re-launch phase-runner with `--resume` context
2. "Skip this phase" → mark phase as skipped in progress.md, continue
3. "Abort orchestration" → stop, report final status
4. "Retry phase from scratch" → re-launch the same phase-runner prompt (fresh agent, fresh context)

### Map Refresh (post-phase)

After each successful phase merge, check if the codebase map needs updating:

```bash
MANIFEST="docs/.mercator.json"
if [ -f "$MANIFEST" ]; then
  DIFF=$(python3 "$SCANNER" . --diff "$MANIFEST" 2>/dev/null)
  ADDED=$(echo "$DIFF" | jq '.added | length')
  REMOVED=$(echo "$DIFF" | jq '.removed | length')
fi
```

| Condition | Action |
|-----------|--------|
| No manifest + first phase | Run `/mercator-ai` |
| Manifest exists, 0 added/removed | Skip |
| Manifest exists, added > 0 OR removed > 0 | Run `/mercator-ai --diff` |

### Final Summary (after all phases)

```markdown
## Orchestration Complete

| Phase | Status | Tests | Review | Commits |
|-------|--------|-------|--------|---------|
| 1 | completed | passed | clean | abc1234 |
| 2 | completed | passed | 2 P2 | def5678 |
| 3 | skipped | — | — | — |

### Deferred Items
- Phase 2: P2 — "Consider extracting helper" (src/utils.ts:45)

### Next Steps
1. Review deferred P2/P3 items
2. Run full test suite: /orbit test
3. Create PR
```

### Why This Works

The context window problem was structural: the old Stage 6 ran all phase work (dispatch, tests,
reviews, commits) in the main conversation. Each phase added 15-30k tokens of tool calls, test
output, and review findings. Two phases filled the window.

The fix separates **coordination** from **execution**:
- Main context = coordinator. Builds prompts, reads results, handles user input. ~800 tokens/phase.
- Phase-runner agent = executor. Does all the heavy work in its own context. Discarded after each phase.
- Files = shared state. progress.md, worktrees, commits persist across agents. No context needed.

This is the same pattern that makes the Agent Teams dispatch mode work — each teammate has its own
context. The phase-runner just applies that principle at the phase level.

---

## Issue Reporting Format

All review steps (test quality, code review, performance review) run inside the phase-runner agent and must report findings in this structured format. This applies to every specific issue — bug, smell, design concern, or risk. These reports stay inside the phase-runner's context; only the severity summary (P0/P1/P2/P3 counts) surfaces to the main orchestrator via the PHASE_RESULT block.

For each issue:

1. **Describe the problem concretely** with file and line references. No vague "this might be a problem" — state what's wrong and what scenario triggers it.

2. **Present 2-3 options**, always including "do nothing" where that's reasonable:
   ```
   Option A: [Fix description]
     - Effort: [low/medium/high]
     - Risk: [what could go wrong]
     - Impact: [what other code is affected]
     - Maintenance: [ongoing burden]

   Option B: [Alternative fix]
     - Effort: ...
     - Risk: ...
     - Impact: ...
     - Maintenance: ...

   Option C: Do nothing
     - Risk: [what happens if we leave it]
     - When this bites: [the scenario where it becomes a real problem]
   ```

3. **Recommend one option and explain why**, tied to the project's existing patterns and conventions (from CLAUDE.md, codebase style, architecture decisions).

Review agents compile their findings into a single report per step. The orchestrator aggregates all reports before presenting to the user at the review gate.

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Plan file not found | Stop with clear error message |
| No skills matched (all fallback) | Warn user, proceed with general-purpose |
| Agent fails mid-task | Log error, skip task, continue batch |
| All agents in batch fail | Pause, ask user |
| Tests fail after 2 retries | Pause, ask user: skip phase / fix manually / abort |
| Review finds P0 after retry | Pause, ask user: fix manually / skip review / abort |
| Worktree create fails | Check for conflicts, suggest resolution |
| Merge conflict | Pause, ask user to resolve manually |

## Resume Support

If orchestration is interrupted:
- TLDR hook summarizes progress.md → ToC with phase statuses and line numbers
- Targeted offset read from the resume point (~50 lines, not full file)
- task_plan.md also read via TLDR first, then only the pending phases section
- findings.md and project docs are skipped entirely on resume
- `/orchestrate --resume {plan-dir}` skips completed phases, stages, and unnecessary reads

With the phase-runner architecture, resume is simpler: the main context never accumulated
phase execution details, so there's less to recover. The orchestrator just reads progress.md,
identifies which phases are done (by parsing status lines or cross-referencing git log), and
starts the phase loop from the first incomplete phase. Each phase-runner gets a fresh context.

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Skip the review stage on first run | Always review on fresh runs — even well-written plans have gaps (skipped automatically on `--resume`) |
| Run >3 agents at once | Batch to 2-3 max — more causes context thrashing |
| Commit without testing | Always /orbit test before commit |
| Force-merge on conflict | Pause and ask user |
| Install skills without recording | Always use AgentReverse manifest for traceability |
| Skip user gate | Always show plan summary before executing |

---

## Agent Teams Integration

When `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is enabled, the phase-runner agent uses
Agent Teams internally for task dispatch. See `.claude/skills/orchestrator/references/team-lead.md`
for the lead's coordination protocol.

The phase-runner architecture makes team mode cheaper: the team coordination overhead stays
inside the phase-runner's context window, not the main orchestrator's. The main context sees
the same ~800-token PHASE_RESULT regardless of whether the phase used classic or team dispatch.

### Classic vs Team Mode

| Aspect | Classic (Task) | Team (Agent Teams) |
|--------|---------------|-------------------|
| Communication | Fire-and-forget | Inter-agent messaging |
| Coordination | Batch-wait | Shared task list + self-claim |
| Discovery sharing | None | Lead relays findings |
| Plan approval | None | For medium/low confidence phases |
| Context | Phase-runner context | Each teammate has own context |
| Token cost | Lower | Higher (separate instances) |
| Error recovery | Log + continue | Lead redirects or replaces |

### What stays the same across modes
- Plan ingestion, skill matching (Stages 1, 3-4; Stage 2 skipped on resume)
- Phase-runner wraps all execution (test → review → commit)
- Worktree isolation per phase
- Skill registry and AgentReverse discovery
- `/orchestrate` command interface and flags
- PHASE_RESULT format (main orchestrator is mode-agnostic)

### Limitations (experimental)
- No session resumption for teammates
- One team per phase-runner per phase
- No nested teams
- Lead cannot be changed mid-phase
- `--resume` restarts the current phase's team from scratch
