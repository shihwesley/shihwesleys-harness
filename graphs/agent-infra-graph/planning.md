---
description: "Plan creation and parsing: interactive-planning produces plan files, plan-ingester parses them into phase manifests for orchestration"
keywords: [planning, interactive-planning, plan-ingester, manifest, task-plan, specs]
---

# Planning

Two files handle plan lifecycle: `interactive-planning` creates plans through user interaction, `plan-ingester` parses them into machine-readable phase manifests.

## Plan Creation

- **Skill: `/interactive-planning`** → `.claude/skills/interactive-planning.md`
  File-based planning with interactive gates. Two modes:
  - **Task-based**: single `task_plan.md` for straightforward work
  - **Spec-driven**: `manifest.md` + `specs/*.md` for multi-domain projects

  Produces a plan directory with: `task_plan.md` or `manifest.md`, `findings.md`, `progress.md`, and optionally `specs/` directory.

  Phase 0.5 does research discovery (scans `~/.claude/research/` for existing expertise). Phases 1-3 walk through interactive gates: mode selection, priority, requirements, approach. Phase 4 optionally sets up a worktree.

## Plan Parsing

- **Skill: `plan-ingester`** → `.claude/skills/orchestrator/plan-ingester.md`
  Reads the plan directory and produces an array of raw phase objects + a project context object. Handles both task-based and spec-driven layouts. Auto-discovers `CLAUDE.md`, `docs/`, `README.md` for context injection.

  **Input**: plan directory (from interactive-planning)
  **Output**: raw phase array → feeds into [[review.md]] (plan-reviewer)

## Plan File Formats

**task_plan.md** (task-based mode):
```markdown
# Phase 1: <title>
## Tasks
- [ ] Task description (files: path/to/file.swift)
## Acceptance Criteria
- Criterion 1
```

**manifest.md** (spec-driven mode):
```markdown
# Manifest
## Phases
1. Phase title → specs/phase-1-spec.md
   Dependencies: none
2. Phase title → specs/phase-2-spec.md
   Dependencies: Phase 1
```

## Cross-References

- Plans feed into the orchestration pipeline → [[orchestration.md]]
- Plan quality is checked before execution → [[review.md]]
