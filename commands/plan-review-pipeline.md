---
name: plan-review-pipeline
description: |
  Multi-lens plan review pipeline. Runs CEO/founder review then eng manager review
  sequentially on interactive-planning spec files, modifying them in place. Optionally
  runs TLA verification on stateful specs. Use when asked to "review the plan",
  "plan review pipeline", "CEO and eng review", or after /interactive-planning produces
  specs and before /orchestrate executes them.
user-invocable: true
---

# /plan-review-pipeline

Multi-lens review pipeline that enriches `/interactive-planning` spec files before `/orchestrate` execution.

## Usage

```
/plan-review-pipeline [--skip-ceo] [--skip-eng] [--skip-tla] [--plan-dir <path>]
```

- Default: runs CEO → Eng → TLA (conditional) in sequence
- `--skip-ceo`: skip the CEO/founder review
- `--skip-eng`: skip the eng manager review
- `--skip-tla`: skip TLA verification even if stateful specs exist
- `--plan-dir`: override plan directory (default: `docs/plans/`)

## What it does

Spawns a single agent (`plan-review-pipeline`) that runs three review lenses sequentially, modifying the spec files in place:

1. **CEO Review** — Challenges premises, validates scope, adds failure modes, dream state analysis
2. **Eng Review** — Locks architecture, adds test plans, diagrams, edge cases, performance analysis
3. **TLA Verification** — Verifies state machines in specs that describe stateful behavior (conditional)

Each review reads the spec files, runs its analysis interactively (AskUserQuestion per issue), and writes findings back into the spec files as new sections.

## Prerequisites

- `docs/plans/manifest.md` must exist (produced by `/interactive-planning`)
- At least one spec file in `docs/plans/specs/`
- Specs should be in `draft` status

## Invoke

```
Use the Agent tool to spawn the plan-review-pipeline agent:
- agent: plan-review-pipeline
- prompt: "Run the plan review pipeline on docs/plans/"
- Pass any flags from the user's invocation
```

Read the agent definition at `~/.claude/agents/plan-review-pipeline.md` if you need to understand the full protocol.
