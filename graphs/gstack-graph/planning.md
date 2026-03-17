---
description: "gstack planning and review skills — CEO mode, eng manager mode, design review."
updated: 2026-03-16
parent: "[[index.md]]"
---

# Planning & Review

Three plan review skills, each with a different lens. All follow the same interactive pattern: present findings one at a time via AskUserQuestion, get user input before proceeding.

## Skills

| Skill | Path | Lens | Key Trait |
|-------|------|------|-----------|
| `/plan-ceo-review` | `gstack/plan-ceo-review/SKILL.md` | CEO/founder | Challenges premises, finds the 10-star product |
| `/plan-eng-review` | `gstack/plan-eng-review/SKILL.md` | Engineering manager | Architecture, data flow, test coverage, performance |
| `/plan-design-review` | `gstack/plan-design-review/SKILL.md` | Designer's eye | Visual audit with annotated screenshots, letter grades |

## CEO Review Modes

Three scope modes selected after initial analysis:
- **SCOPE EXPANSION** — Dream big, find the 10-star version
- **HOLD SCOPE** — Maximum rigor on the existing plan
- **SCOPE REDUCTION** — Strip to essentials

10 review sections: Architecture, Error & Rescue Map, Security & Threat Model, Data Flow & Edge Cases, Code Quality, Test Review, and more.

## Eng Review Structure

1. **Step 0: Scope Challenge** — Should this be bigger or smaller?
2. **Architecture review** — Data models, API design, dependencies
3. **Code quality review** — Patterns, naming, DRY
4. **Test review** — Coverage, edge cases → generates test plan artifact
5. **Performance review** — N+1s, memory, latency

Outputs: "NOT in scope" section, "What already exists" section, TODOS.md updates, Mermaid diagrams.

## Design Review

Uses the browse engine to audit a live site. 10 categories (~80 items): typography, color, spacing, hierarchy, interaction feel, responsive, accessibility, and more. Produces a prioritized report with annotated screenshots.

Modes: Full, Quick (`--quick`), Deep (`--deep`), Diff-aware, Regression.

## Related

- [[browser.md]] — Used by `/plan-design-review` for screenshots
- [[shipping.md]] — `/ship` includes a pre-landing review step
- [[qa-testing.md]] — `/qa-design-review` is the fix-loop version of `/plan-design-review`
