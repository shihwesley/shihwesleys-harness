---
description: "gstack utility skills — cookie import, self-upgrade, contributor mode."
updated: 2026-03-16
parent: "[[index.md]]"
---

# Setup & Utilities

Supporting skills that don't fit the main workflow categories.

## Skills

| Skill | Path | Purpose |
|-------|------|---------|
| `setup-browser-cookies` | `gstack/setup-browser-cookies/SKILL.md` | Import cookies from real browsers for authenticated testing |
| `gstack-upgrade` | `gstack/gstack-upgrade/SKILL.md` | Self-upgrade with snooze, auto-upgrade, and "what's new" |

## Cookie Import

Imports cookies from Comet, Chrome, Arc, Brave, or Edge into the headless browser session. Two modes:
- **Picker** — `$B cookie-import-browser` opens interactive UI to select domains
- **Direct** — `$B cookie-import-browser comet --domain .github.com` for scripted import

## Self-Upgrade

Runs automatically via preamble check. Detects install type (global git, vendored, local git), backs up current version, runs upgrade, and shows changelog.

Four options when upgrade is available:
1. Yes, upgrade now
2. Always keep me up to date (sets `AUTO_UPGRADE=true`)
3. Not now (escalating snooze: 24h → 48h → 7d)
4. Never ask again

## Contributor Mode

Not a separate skill — a cross-cutting feature toggled by `gstack_contributor=true` in config. When active, every major workflow step triggers a self-reflection: rate the gstack tooling 0-10, and file a field report if something wasn't a 10.

Reports go to `~/.gstack/contributor-logs/{slug}.md` with steps to reproduce, raw output, and improvement suggestions.

## Related

- [[browser.md]] — Cookie import prepares the browser for authenticated testing
- [[qa-testing.md]] — Authenticated QA requires cookie setup first
