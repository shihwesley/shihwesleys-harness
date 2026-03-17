---
description: "gstack browse — headless Chromium browser engine. Core tool used by QA, design, and shipping skills."
updated: 2026-03-16
parent: "[[index.md]]"
---

# Browser Engine

The `browse` skill is the backbone of gstack. A persistent headless Chromium instance with ~100ms command latency.

## Skills

| Skill | Path | Purpose |
|-------|------|---------|
| `browse` | `gstack/browse/SKILL.md` | Direct browser control — goto, snapshot, click, fill, screenshot, assertions |
| `setup-browser-cookies` | `gstack/setup-browser-cookies/SKILL.md` | Import cookies from Chrome/Arc/Brave/Edge for authenticated testing |

## Key Concepts

- **Snapshot system** — Accessibility tree with `@e` refs for element selection. Flags: `-i` interactive, `-D` diff, `-a` annotated screenshot, `-C` cursor-interactive.
- **Persistence** — Browser stays alive between calls. Cookies, tabs, sessions carry over. Auto-shutdown after 30 min idle.
- **$B binary** — Compiled Bun binary at `browse/dist/browse`. First call auto-starts (~3s), then ~100ms per command.
- **Chain command** — Batch multiple commands via JSON stdin to reduce CLI overhead.

## Common Patterns

- `$B goto <url>` → `$B snapshot -i` → `$B click @e3` → `$B snapshot -D` (navigate → inspect → interact → verify)
- `$B responsive /tmp/layout` — Quick mobile/tablet/desktop screenshots
- `$B diff <url1> <url2>` — Compare two pages/environments
- `$B is visible ".selector"` — Assertion checks (visible/hidden/enabled/disabled/checked/focused)

## Related

- [[qa-testing.md]] — Uses browse for automated QA
- [[design.md]] — Uses browse for design audits
- [[utilities.md]] — Cookie setup before authenticated testing
