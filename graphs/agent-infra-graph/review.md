---
description: "Quality gates: plan-reviewer (pre-execution) and code-review-pro (post-execution)"
keywords: [plan-reviewer, code-review-pro, quality, review, severity, p0-p3]
---

# Quality Gates

Two review checkpoints: one before agents execute (plan review), one after (code review).

## Pre-Execution: Plan Review

- **Skill: `plan-reviewer`** → `.claude/skills/orchestrator/plan-reviewer.md`
  Quality-gates the ingested plan before skill matching:

  - **Phase sizing** — splits phases with >5 tasks or >3 module spread (e.g., phase 3 → 3a, 3b)
  - **Gap detection** — cross-references plan against project docs to find missing work
  - **Task enrichment** — expands vague task descriptions with specific file targets and acceptance criteria

  **Input**: raw phase array (from `plan-ingester`)
  **Output**: reviewed/enriched phase array → feeds into [[orchestration.md]] (skill-matcher)

## Post-Execution: Code Review

- **Skill: `/code-review-pro`** → `.claude/commands/code-review-pro.md`
  Multi-agent deep code review with parallel specialist analysis:

  - Spawns parallel sub-agents (SOLID, security, quality) via Task tool
  - Produces severity-classified findings: P0 (critical) → P3 (nit)
  - Confidence scoring per finding
  - Called by `phase-finisher` after Orbit tests pass

  **Input**: PR number or `'local'` for working changes
  **Output**: structured review report

## Review in the Pipeline

```
plan-ingester output
       ↓
  plan-reviewer (pre-execution gate)    ← you are here
       ↓
  skill-matcher → dispatch → agents
       ↓
  code-review-pro (post-execution gate) ← you are here
       ↓
  commit-split → merge
```

Plan review catches structural problems *before* agents burn tokens. Code review catches implementation problems *before* code ships.

## Cross-References

- Plan review feeds into skill matching → [[orchestration.md]]
- Code review is called by phase-finisher → [[completion.md]]
- Plans come from interactive-planning → [[planning.md]]
