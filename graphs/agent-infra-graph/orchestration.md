---
description: "Top-level pipeline (orchestrate) and skill/agent routing (skill-matcher, skill-registry.json)"
keywords: [orchestrate, skill-matcher, skill-registry, pipeline, routing, dispatch-mode]
---

# Orchestration & Routing

`/orchestrate` is the top-level command that runs the full pipeline. `skill-matcher` resolves which agents handle which phases.

## The Pipeline

- **Skill: `/orchestrate`** → `.claude/commands/orchestrate.md`
  Takes an `/interactive-planning` output directory and runs it through:
  1. **INGEST** — `plan-ingester` parses plan files (see [[planning.md]])
  2. **REVIEW** — `plan-reviewer` quality-gates the plan (see [[review.md]])
  3. **MATCH** — `skill-matcher` resolves skills/agents per phase
  4. **RESEARCH** — checks knowledge store, fetches docs, produces cheat sheets
  5. **WORKTREE** — `worktree-manager` creates isolated branches (see [[completion.md]])
  6. **DISPATCH** — `agent-dispatcher` spawns agents (see [[dispatch.md]])
  7. **FINISH** — `phase-finisher` tests, reviews, commits, merges (see [[completion.md]])

  Flags: `--dry-run`, `--resume`, `--max-parallel N`, `--model X`, `--phase N`, `--team` / `--no-team`

## Skill Matching

- **Skill: `skill-matcher`** → `.claude/skills/orchestrator/skill-matcher.md`
  3-step cascade to resolve which skills and agent types apply to each phase:
  1. **Local registry** — keyword lookup in `skill-registry.json`
  2. **AgentReverse** — suggests skills from installed capabilities
  3. **Web search fallback** — finds relevant tools if local sources miss

  **Input**: reviewed phase array (from `plan-reviewer`)
  **Output**: enriched phase manifests with `skills`, `agentType`, `confidence` fields

## Skill Registry

- **Config: `skill-registry.json`** → `.claude/skills/orchestrator/skill-registry.json`
  Static keyword-to-agent mapping. Version 2 includes `graphPaths` for skill graph integration.

  Keywords like `swift`, `swiftui`, `tca` → `swift-engineering:*` agents.
  Keywords like `react`, `node`, `python` → `feature-dev:*` agents.
  Language detection: `.swift` → `["swift"]`, `.ts` → `["node", "frontend"]`.

## Stage 4: Research (Anti-Slop Layer)

The research stage checks the neo-research knowledge store before any agent writes code. If research artifacts exist for the phase's tech stack, three upgrades apply:
1. **Specialist substitution** — research-generated specialist agent replaces generic agent type
2. **Skill injection** — research-generated skill patterns injected into agent prompt
3. **Knowledge store access** — `rlm_search` / `rlm_ask` instructions added to prompt

## Cross-References

- Pipeline starts with parsed plans → [[planning.md]]
- Matched phases go to dispatch → [[dispatch.md]]
- Quality gates before and after → [[review.md]]
- Worktree isolation and finishing → [[completion.md]]
