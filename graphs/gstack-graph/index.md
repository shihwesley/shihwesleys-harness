---
description: "Hub MOC for gstack — Garry Tan's engineering workflow toolkit. QA testing, code review, planning, shipping, retrospectives, and design systems."
updated: 2026-03-16
domains: [qa, code-review, shipping, planning, design, retro, browser-testing]
source: "https://github.com/garrytan/gstack"
---

# gstack Skill Graph

Workflow toolkit built around a fast headless browser. Covers the full dev cycle: plan review, QA testing, code review, shipping, documentation, retrospectives, and design systems. Navigate by reading this index, then following the MOC that matches your task.

## Browser Engine (Core)

- [[browser.md]] — Headless Chromium browser (`$B` commands). Persistent sessions, ~100ms per command. Snapshot system with @ref element selection, annotated screenshots, diff-based verification. Foundation for all QA and design skills.

## QA & Testing

- [[qa-testing.md]] — QA workflows: test-fix-verify loops, report-only mode, design-specific audits. Diff-aware mode for feature branches, health scoring, severity tiers, responsive layout testing.

## Planning & Review

- [[planning.md]] — Plan review skills: CEO/founder mode (scope expansion/reduction), engineering manager mode (architecture + test coverage), design review (visual audit with letter grades).

## Code Review & Shipping

- [[shipping.md]] — Pre-landing review, ship workflow (test → review → version → changelog → PR), post-ship documentation updates. Greptile integration for automated comment triage.

## Design Systems

- [[design.md]] — Design consultation: product context → research → proposal → preview → DESIGN.md. Design audit with 80-item checklist across 10 categories.

## Retrospectives

- [[retro.md]] — Weekly engineering retrospective. Commit analysis, work session detection, code quality metrics, team-aware breakdowns, persistent history with trend tracking.

## Setup & Utilities

- [[utilities.md]] — Browser cookie import, gstack self-upgrade, contributor mode field reports.

---

## Navigation Protocol

1. Read this index (you're here) — pick the MOC matching your task
2. Read the MOC — understand which gstack skill to invoke
3. Invoke the skill — `/<skill-name>` (all are user-invocable slash commands)

Skills are installed at: `shihwesleys-harness/skills/gstack/<skill-name>/SKILL.md`

Do not load all MOCs. Do not read files you won't use. The graph saves tokens by being selective.
