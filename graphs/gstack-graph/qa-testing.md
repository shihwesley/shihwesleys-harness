---
description: "gstack QA testing skills — test-fix-verify loops, report-only mode, design-specific audits."
updated: 2026-03-16
parent: "[[index.md]]"
---

# QA & Testing

Three QA skills with different levels of intervention. All use the browse engine and support diff-aware mode (auto-scopes to changed files on feature branches).

## Skills

| Skill | Path | Mode | Fixes Code? |
|-------|------|------|-------------|
| `/qa` | `gstack/qa/SKILL.md` | Test → Fix → Verify loop | Yes — atomic commits per fix |
| `/qa-only` | `gstack/qa-only/SKILL.md` | Report only — structured bug report | No |
| `/qa-design-review` | `gstack/qa-design-review/SKILL.md` | Design-focused QA with fix loop | Yes — design/CSS fixes |

## Workflow Phases (shared across all three)

1. **Initialize** — Parse URL/branch, detect mode, find browse binary
2. **Authenticate** — Import cookies if testing authenticated pages
3. **Orient** — First snapshot, console check, network check
4. **Explore** — Systematic testing by category (visual, functional, UX, content, performance, accessibility)
5. **Document** — Health score, bug report with screenshots and repro steps
6. **Wrap Up** — Ship-readiness summary, before/after comparison

## Modes

- **Diff-aware** (default on feature branches) — Scopes testing to changed files via `git diff`
- **Full** (default with URL) — Tests entire site
- **Quick** (`--quick`) — Critical + high severity only
- **Regression** (`--regression`) — Compare against previous baseline

## Health Score

Weighted across 8 categories: Console (15%), Links (10%), Visual/Functional/UX/Content/Performance/Accessibility (variable weights). Letter grades A-F.

## Severity Tiers

| Tier | Fixes |
|------|-------|
| Quick | Critical + high only |
| Standard | + medium (default) |
| Exhaustive | + low/cosmetic |

## Related

- [[browser.md]] — Browse engine used for all testing
- [[design.md]] — `/design-consultation` creates the DESIGN.md that `/qa-design-review` checks against
- [[shipping.md]] — `/ship` runs QA as part of the ship workflow
