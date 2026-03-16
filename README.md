# shihwesleys-harness

Custom Claude Code harness — skills, agents, hooks, scripts, and skill graphs that make the AI engineering workflow tick.

This repo is the source of truth for all non-plugin Claude Code customizations. Files are symlinked into `~/.claude/` so edits here are live immediately.

## What's inside

| Directory | Count | Description |
|-----------|-------|-------------|
| `commands/` | 41 | Skills (slash commands + agent-only) |
| `agents/` | 7 | Specialized subagent definitions |
| `scripts/` | 9 | Shell/Python utilities (learning pipeline, validators, vault tools) |
| `hooks/` | 21 | Session hooks, build checks, context management, worktree enforcement |
| `graphs/swift-graph/` | 13 | Swift/iOS/visionOS skill navigation graph |
| `graphs/agent-infra-graph/` | 6 | Agent orchestration infrastructure graph |

## Setup

```bash
git clone git@github.com:shihwesley/shihwesleys-harness.git ~/Source/shihwesleys-harness
cd ~/Source/shihwesleys-harness
chmod +x install.sh uninstall.sh
./install.sh
```

This creates symlinks from `~/.claude/{commands,agents,scripts,hooks}` and `~/Source/.claude/docs/{swift-graph,agent-infra-graph}` into this repo.

To remove all symlinks:
```bash
./uninstall.sh
```

## Making changes

Edit files directly in this repo. Symlinks mean changes are live instantly — no copy step.

```bash
# Edit a skill
vim commands/humanizer.md

# Commit and push
git add -A && git commit -m "feat(skills): add new pattern to humanizer"
git push
```

## Releasing

This repo uses [Conventional Commits](https://www.conventionalcommits.org/) and the `/release` skill for versioning.

```
feat(skills): ...   → minor bump
fix(hooks): ...     → patch bump
feat!: ...          → major bump
```

Run `/release` in Claude Code to tag, generate changelog, and create a GitHub Release.

## Related

- [shihwesley-plugins](https://github.com/shihwesley/shihwesley-plugins) — Claude Code plugins (runtime extensions, MCP servers). The `release.md` skill lives there and is symlinked separately.

## Architecture

```
~/.claude/
├── commands/  → symlinks to shihwesleys-harness/commands/
├── agents/    → symlinks to shihwesleys-harness/agents/
├── scripts/   → symlinks to shihwesleys-harness/scripts/
├── hooks/     → symlinks to shihwesleys-harness/hooks/
└── plugins/   → managed by shihwesley-plugins (separate repo)

~/Source/.claude/docs/
├── swift-graph/       → symlinks to shihwesleys-harness/graphs/swift-graph/
└── agent-infra-graph/ → symlinks to shihwesleys-harness/graphs/agent-infra-graph/
```

## Not included

- **Plugins** — managed by [shihwesley-plugins](https://github.com/shihwesley/shihwesley-plugins)
- **release.md skill** — lives in shihwesley-plugins, symlinked from there
- **CLAUDE.md files** — project-specific, stay in their respective repos
- **Memory (.mv2)** — backed up via `/mind-backup`
- **Plugin cache** — auto-managed by Claude Code plugin system
