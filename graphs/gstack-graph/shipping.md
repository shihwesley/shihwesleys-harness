---
description: "gstack shipping workflow — code review, ship pipeline, post-ship documentation."
updated: 2026-03-16
parent: "[[index.md]]"
---

# Code Review & Shipping

Three skills that cover the path from "code is done on a branch" to "merged with docs updated."

## Skills

| Skill | Path | Purpose |
|-------|------|---------|
| `/review` | `gstack/review/SKILL.md` | Pre-landing PR review — diff analysis for bugs, security, enum completeness |
| `/ship` | `gstack/ship/SKILL.md` | Full ship pipeline: merge base → test → review → version → changelog → PR |
| `/document-release` | `gstack/document-release/SKILL.md` | Post-ship documentation update across README, ARCHITECTURE, CONTRIBUTING, CHANGELOG |

## Review Focus Areas

- SQL safety (injection, raw queries)
- LLM trust boundary violations
- Conditional side effects
- Enum & value completeness (reads outside the diff)
- Greptile comment triage (VALID, ALREADY FIXED, FALSE POSITIVE, SUPPRESSED)

Fix-first approach: every finding gets classified as AUTO-FIX or ASK, then resolved before moving on.

## Ship Pipeline (9 steps)

1. Pre-flight checks
2. Merge base branch (auto-resolve simple conflicts)
3. Run tests (stop on failure)
4. Eval suites (conditional)
5. Pre-landing review (same as `/review`)
6. Greptile comment resolution
7. VERSION bump (auto-decide based on changes)
8. CHANGELOG generation + TODOS.md cleanup
9. Commit → Push → Create PR

Only stops for: test failures, merge conflicts, security issues, user-facing behavior changes.

## Document Release

Post-ship workflow that reads all project docs, cross-references the diff, and updates:
- README.md — Features, usage, examples
- ARCHITECTURE.md — System design, data flow
- CONTRIBUTING.md — Dev setup, test patterns
- CLAUDE.md — AI assistant instructions
- CHANGELOG — Voice polish
- TODOS.md — Remove completed items
- VERSION — Optional bump

## Related

- [[qa-testing.md]] — QA before shipping
- [[planning.md]] — Plan review before coding
- [[retro.md]] — Retrospective after shipping
