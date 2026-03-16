---
name: orchestrator
description: "Automated plan execution pipeline. Use when running /orchestrate on an /interactive-planning output. Handles plan ingestion, review, skill matching, tech research, user gating, and phased execution with worktree isolation, testing, code review, and incremental commits."
metadata:
  author: shihwesley
  version: 2.0.0
user-invocable: true
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Write", "Edit", "Task", "AskUserQuestion", "TaskCreate", "TaskUpdate", "TaskList", "Skill", "ToolSearch", "WebSearch"]
---

# Orchestrator

Takes `/interactive-planning` output and executes it through a 6-stage pipeline: ingest, review, skill-match, research, user gate, and phased execution with worktree isolation.

## When to Use

- After `/interactive-planning` produces a plan directory with `task_plan.md` or `manifest.md`
- When you need automated, isolated execution of a multi-phase plan
- When resuming an interrupted orchestration (`--resume`)

## Pipeline Stages

1. **INGEST** -- read plan files (`task_plan.md` or `manifest.md` + specs), discover project docs (CLAUDE.md, codebase map)
2. **REVIEW** -- agent checks phase sizing, gaps, clarity, dependencies, confidence (skipped on `--resume`)
3. **MATCH** -- resolve skills per phase via registry lookup, AgentReverse fallback, web search fallback, or general-purpose default
4. **RESEARCH** -- fetch official docs for unfamiliar tech (Context7, knowledge store, web), produce cheat sheets
5. **GATE** -- present full execution plan to user for approval
6. **EXECUTE** -- run phases using the subprocess phase-runner script

## Execution Modes

### Subprocess Phase Runner (preferred)

Stage 6 uses `.claude/scripts/phase-runner.py` — a Python script that runs each protocol step as a separate `claude -p` subprocess. Artifact gates between steps make every step structurally unskippable.

```bash
python3 .claude/scripts/phase-runner.py --phase N --plan-dir docs/plans
```

Each step gets its own context window. The script controls flow, not prompt instructions. This prevents the known failure mode where a single agent skips review steps.

**Protocol steps (each a separate subprocess):**
1. Create worktree
2. Implement specs (parallel `claude -p` calls per spec)
3. Build verification (with retry loop)
4. Reviews (3 parallel: test-review, code-review, perf-review)
5. Fix findings (3 sequential passes: P1, P2, P3 — each its own subprocess)
6. Commit
7. Merge + cleanup
8. Update progress

**Fix step detail:** Findings are fixed in three sequential passes so later fixers see earlier changes. P0 runs with P1.

| Pass | Severity | Why sequential |
|------|----------|---------------|
| 1 | P0 + P1 | Critical fixes first |
| 2 | P2 | Sees P1 fixes, skips items already resolved |
| 3 | P3 | Sees P1 + P2 fixes, skips items already resolved |

### Agent-Based Phase Runner (fallback)

If the subprocess runner is unavailable, Stage 6 falls back to launching a `phase-runner` subagent per phase. This is the original architecture — each phase-runner gets its own context window but controls its own step execution via prompt instructions. Known limitation: single agents tend to skip review steps.

## Dispatch Modes

The orchestrator picks classic or team mode per-phase based on task count, shared files, and dependencies:

| Condition | Mode |
|-----------|------|
| 1-2 tasks | classic |
| 3+ tasks, all independent | classic |
| 4+ tasks with shared files or deps | team |
| Low/medium confidence, 3+ tasks | team |
| `--team` flag | team (forced) |
| `--no-team` flag | classic (forced) |

## Flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Run stages 1-4, show plan at stage 5, stop |
| `--resume` | Skip completed phases, skip stage 2 review |
| `--max-parallel N` | Max agents per batch (default: 3) |
| `--model sonnet\|opus\|haiku` | Model for dispatched agents |
| `--phase N` | Execute only phase N |
| `--team` | Force Agent Teams mode |
| `--no-team` | Force classic Task dispatch |
| `--subprocess` | Force subprocess phase-runner (default when script exists) |
| `--no-subprocess` | Force agent-based phase-runner |

## Component Files

All component specifications live in `references/`:

| File | Role |
|------|------|
| `references/plan-ingester.md` | Parse plan files, handle spec-driven and task-based modes |
| `references/plan-reviewer.md` | Review and restructure plans (sizing, gaps, clarity) |
| `references/skill-matcher.md` | 3-step skill resolution cascade |
| `references/tech-researcher.md` | Fetch docs, produce cheat sheets, manage knowledge store |
| `references/skill-registry.json` | Keyword-to-skill/agent mappings |
| `references/worktree-manager.md` | Worktree lifecycle per phase |
| `references/agent-dispatcher.md` | Dual-mode dispatch (team or classic) |
| `references/team-lead.md` | Agent Teams lead coordination protocol |
| `references/phase-runner.md` | Protocol spec for one phase (used by both modes) |
| `references/phase-finisher.md` | Test, review, commit chain (runs inside phase-runner) |

Script:

| File | Role |
|------|------|
| `.claude/scripts/phase-runner.py` | Subprocess executor — enforces protocol via artifact gates |

## Context Window Design

**Subprocess mode:** Zero main-context cost per phase. The script runs outside the conversation entirely. The orchestrator calls it via `Bash` and reads the exit code + progress.md updates.

**Agent mode (fallback):** ~800 tokens per phase in main context. Each phase-runner subagent gets its own context window and returns a ~20-line structured result.

## Examples

```bash
# Standard execution (subprocess mode, auto-detected)
/orchestrate ./plans/my-feature

# Preview without executing
/orchestrate --dry-run ./plans/my-feature

# Resume after interruption
/orchestrate --resume ./plans/my-feature

# Execute specific phase with limited parallelism
/orchestrate --phase 2 --max-parallel 2 ./plans/my-feature

# Force agent-based execution (skip subprocess)
/orchestrate --no-subprocess ./plans/my-feature

# Run phase-runner script directly (outside orchestrator)
python3 .claude/scripts/phase-runner.py --phase 4 --plan-dir docs/plans
python3 .claude/scripts/phase-runner.py --phase 4 --plan-dir docs/plans --dry-run
python3 .claude/scripts/phase-runner.py --phase 4 --plan-dir docs/plans --step review
```

## Common Issues

- **Plan file not found**: The orchestrator resolves `PLAN_DIR` to an absolute path via `realpath`. Make sure the directory exists and contains `task_plan.md` or `manifest.md`.
- **No skills matched**: Falls back to `general-purpose` agent type with a warning. Add keywords to your plan's task descriptions to improve matching.
- **Phase-runner fails after retries**: You get four options: fix manually, skip the phase, abort, or retry from scratch. The phase-runner's error message usually points to the root cause.
- **Subprocess timeout**: Default is 600s (10 min) per step. For large specs (>8 items), the script splits work across parallel or sequential agents automatically.
- **Merge conflicts**: The orchestrator pauses and asks you to resolve manually. It won't force-merge.
