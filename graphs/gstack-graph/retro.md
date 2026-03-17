---
description: "gstack retrospective skill — weekly engineering retro with commit analysis and trend tracking."
updated: 2026-03-16
parent: "[[index.md]]"
---

# Retrospectives

Single skill that produces data-driven weekly engineering retrospectives.

## Skills

| Skill | Path | Purpose |
|-------|------|---------|
| `/retro` | `gstack/retro/SKILL.md` | Weekly engineering retrospective with metrics and trends |

## Arguments

- `<N>d` / `<N>h` / `<N>w` — Custom time window (default: 7d)
- `compare` — Compare current period to previous
- `compare <N>d` — Compare with custom window

## Data Collection (Step 1)

9 git/project data sources:
1. All commits with timestamps, author, files changed, insertions/deletions
2. Per-commit test vs production LOC breakdown by author
3. Commit timestamps for session detection (Pacific time)
4. File hotspot analysis (most frequently changed)
5. PR numbers from commit messages
6. Per-author file hotspots
7. Per-author commit counts
8. Greptile triage history (if available)
9. TODOS.md backlog (if available)

## Metrics Computed

- Lines added/removed, net change, test coverage ratio
- Work session detection (deep 50+ min, medium 20-50 min, micro <20 min)
- Commit time distribution (hourly histogram)
- Commit type breakdown (feat/fix/refactor/test/chore)
- Per-author contributions with praise and growth areas
- Greptile signal ratio (if history exists)
- Backlog health from TODOS.md

## Related

- [[shipping.md]] — Retro analyzes what was shipped
- [[planning.md]] — Retro findings inform next sprint planning
