# Changelog

All notable changes to shihwesleys-harness will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/).
Versioning follows [Conventional Commits](https://www.conventionalcommits.org/) via `/release`.

## [1.4.0] - 2026-03-17

### Added
- `install.sh` sub-skill promotion — nested skill dirs with their own `SKILL.md` are symlinked as independent top-level skills

### Fixed
- TLDR read enforcer now bypasses image files (png, jpg, heic, webp, etc.) and PDFs so simulator screenshots and visual assets are read natively by Claude's multimodal reader

## [1.3.0] - 2026-03-16

### Added
- `/plan-review-pipeline` command — multi-lens review pipeline bridging `/interactive-planning` and `/orchestrate`
- `plan-review-pipeline` agent — runs CEO/founder review then eng manager review sequentially on spec files, modifying them in place; optionally extracts state models for TLA verification

## [1.2.0] - 2026-03-16

### Added
- gstack skill pack from `garrytan/gstack` (v1.1.0) — 14 sub-skills: browse, qa, qa-only, qa-design-review, plan-ceo-review, plan-eng-review, plan-design-review, review, ship, document-release, retro, design-consultation, setup-browser-cookies, gstack-upgrade
- gstack skill graph (8 MOC files) at `graphs/gstack-graph/`
- Anthropic skill guide audit for all gstack skills
- Trigger phrases added to 5 gstack skill descriptions (design-consultation, document-release, plan-eng-review, ship, review)

### Fixed
- `install.sh` graph symlinks now loop all `graphs/*/` directories instead of hardcoding swift-graph and agent-infra-graph

## [1.1.0] - 2026-03-16

### Added
- `skills/` directory in harness — modern multi-file skill format with `SKILL.md` + `references/`
- 11 skills migrated from orphaned `~/.claude/skills/` into harness management
- `tla-spec` skill — TLA+ formal verification for state machines (generate, verify, audit, drift)
- `tla-verifier` agent — TLC model checker runner (Sonnet, 40 turns)
- Post-commit hook auto-runs `install.sh` after every harness commit

### Changed
- `install.sh` now handles `skills/` directory symlinks to `~/.claude/skills/`
- `/agent-reverse install` writes to harness first, then symlinks (never directly to `~/.claude/`)

### Fixed
- 14 duplicate skills (same skill in both `commands/` and `skills/`) removed
- 25 orphaned skills in `~/.claude/skills/` that weren't backed up to git

## [1.0.0] - 2026-03-16

### Added
- 35 skills (markdown command files for Claude Code)
- 6 directory-based skills (defuddle, json-canvas, obsidian-bases, obsidian-cli, obsidian-markdown, sim-debug)
- 7 agent definitions (ios-specialist, visionos-specialist, sim-debugger, phase-runner, etc.)
- 9 custom scripts (self-learn, phase-runner, vault utilities, swift-graph validator)
- 18 custom hooks (session management, build checks, learning pipeline, worktree enforcement)
- 3 chronicler hooks
- Swift skill graph (13 MOC files)
- Agent infrastructure graph (6 MOC files)
- install.sh / uninstall.sh for symlink management
