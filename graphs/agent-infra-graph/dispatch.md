---
description: "Agent spawning: dual-mode dispatcher (teams vs classic), team-lead coordination, prompt templates, skill graph injection"
keywords: [agent-dispatcher, team-lead, agent-teams, classic-dispatch, prompt-template, parallel]
---

# Agent Dispatch

How agents get spawned, configured, and coordinated. Two modes with the same output format.

## The Dispatcher

- **Skill: `agent-dispatcher`** → `.claude/skills/orchestrator/agent-dispatcher.md`
  Receives enriched phase manifests (from `skill-matcher`) and spawns agents.

  Mode determined by `/orchestrate` flags (`--team` / `--no-team`):
  - **Team mode** → Section B: Agent Teams with coordinating lead
  - **Classic mode** → Section C: fire-and-forget Task dispatch (default)

  Max parallel agents: 2-3 (configurable via `--max-parallel`).

## Classic Mode

Batches phase tasks, launches agents in parallel via `Task` tool:
```
for batch in batches (size = MAX_PARALLEL):
    launch all agents in batch simultaneously
    wait for batch completion
    proceed to next batch
```

Each agent gets the structured prompt template with: task context, files to modify, acceptance criteria, project conventions, architecture context, skill graph instructions (for Swift), and knowledge store access.

## Team Mode

- **Skill: `team-lead`** → `.claude/skills/orchestrator/team-lead.md`
  Creates an Agent Teams instance per phase:
  - **Lead**: delegate mode (coordinates, never writes code)
  - **Teammates**: one per task or tightly-coupled module group

  Lead responsibilities:
  - Spawn teammates with worktree paths + cheat sheets
  - Plan approval gate for `confidence: medium/low` phases
  - Discovery relay (teammate A finds something that affects teammate B → lead relays)
  - Collect results when all tasks complete
  - Shutdown teammates and return aggregated results

  Output format matches classic mode — `phase-finisher` doesn't need to know which mode was used.

## Prompt Template

Every agent (both modes) receives:
- Phase context (number, title, working directory, branch)
- Task description + files to modify + acceptance criteria
- Project conventions (from CLAUDE.md)
- Architecture context (from CODEBASE_MAP.md)
- **Swift Skill Graph block** (conditional: if agentType is `swift-engineering:*`)
- Knowledge store access (conditional: if research artifacts exist)
- Instructions (scope constraints, convention adherence, summary format)

## Skill Loading

- Plugin agents (`swift-engineering:*`, `feature-dev:*`) have built-in skills
- Custom skills (via AgentReverse) get injected directly into the prompt
- Research-generated specialists may replace generic agent types

## Cross-References

- Dispatch receives matched phases from → [[orchestration.md]]
- Team mode uses the team-lead protocol → this file
- After dispatch, results go to → [[completion.md]]
- Quality gate before dispatch → [[review.md]]
