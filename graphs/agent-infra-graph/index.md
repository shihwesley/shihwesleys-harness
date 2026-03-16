---
description: "Hub MOC for the agent orchestration infrastructure. Entry point for understanding how plans become executed code."
updated: 2026-02-20
domains: [orchestration, planning, dispatch, review, worktree, agent-teams]
---

# Agent Infrastructure Graph

The pipeline that turns a plan into committed code. Five stages, each with its own MOC.

## Planning

- [[planning.md]] — Creating and parsing plans. `/interactive-planning` produces plan files; `plan-ingester` parses them into phase manifests.

## Orchestration & Routing

- [[orchestration.md]] — The top-level pipeline (`/orchestrate`) and how phases get matched to skills/agents via `skill-matcher` and `skill-registry.json`.

## Agent Dispatch

- [[dispatch.md]] — Spawning agents for work. Two modes: Agent Teams (coordinated via `team-lead`) or classic fire-and-forget. Prompt template, skill loading, research artifact injection.

## Quality Gates

- [[review.md]] — Plan review (`plan-reviewer`) and code review (`code-review-pro`). Quality checks before and after execution.

## Completion & Isolation

- [[completion.md]] — Finishing work: `phase-finisher` chains test → review → commit → merge. `worktree-manager` handles git isolation. `commit-split` breaks large changes into atomic commits.

---

## Data Flow

```
interactive-planning
       ↓
  plan-ingester        ← [[planning.md]]
       ↓
  plan-reviewer        ← [[review.md]]
       ↓
  skill-matcher        ← [[orchestration.md]]
       ↓
  agent-dispatcher     ← [[dispatch.md]]
     ↙       ↘
team-lead   classic
     ↓         ↓
  phase-finisher       ← [[completion.md]]
   ↓    ↓    ↓
 orbit review commit
```

## Navigation Protocol

Same as the Swift skill graph: read this index, pick the MOC matching your question, read only what you need. Full traversal protocol: `.claude/docs/swift-graph/traverse.md` (protocol is domain-agnostic).
