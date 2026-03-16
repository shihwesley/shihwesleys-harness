---
name: chronicle-sync
description: Sync Chronicler INDEX.md files into the Obsidian vault as lightweight project references. Use when user says /chronicle-sync, wants to import chronicler indexes into Obsidian, or sync project documentation to their vault.
---

# /chronicle-sync — Bridge Chronicler to Obsidian Vault

Sync Chronicler project indexes into the Obsidian vault at `~/Claude/vault/References/Tech/` without copying the bulk `.tech.md` files.

## What gets synced

**Only INDEX.md files** — one per project. These are small markdown tables (~50-200 lines) listing every component with a one-line purpose. They give Obsidian users a browsable overview of each project's architecture.

**Never sync .tech.md files.** Those stay in their project's `.chronicler/` directory. Claude Code reads them directly when needed. Obsidian doesn't need them — they'd bloat the vault and dilute the knowledge graph.

## Process

### 1. Discover projects with Chronicler output

```bash
find ~/Source -maxdepth 3 -path "*/.chronicler/INDEX.md" -type f 2>/dev/null
```

### 2. For each found INDEX.md

Create a vault-friendly reference note at `~/Claude/vault/References/Tech/{project-name}.md` that:

a) Has proper Obsidian frontmatter:
```yaml
---
date: "YYYY-MM-DD"
tags:
  - references
  - tech-docs
  - projects/{project-name-lowercase}
source: "chronicler"
chronicler_path: "/full/path/to/.chronicler/"
---
```

b) Includes a header with project name and path
c) Embeds the INDEX.md content (copy, not symlink — symlinks cause Obsidian issues on some platforms)
d) Adds a footer note: "Full .tech.md docs at `{project}/.chronicler/`. Use Claude Code to query them."

### 3. Freshness check

Before overwriting, compare the existing vault file's date against the INDEX.md's modification time. Only update if the source is newer.

### 4. Report

```
Synced: 5 projects
- MagicCarpet (73 components, updated)
- Chronicler (42 components, already fresh)
- ShopAssist (31 components, new)
Skipped: 2 projects (no .chronicler/ found)
```

## Options

`/chronicle-sync` — sync all projects
`/chronicle-sync MagicCarpet` — sync one project
`/chronicle-sync --clean` — remove vault references for projects that no longer have .chronicler/

## Rules

- Never copy .tech.md files into the vault
- Never create symlinks (they cause cross-platform issues with Obsidian sync)
- Always use the `obsidian-markdown` skill for proper formatting
- Keep the vault reference note under 300 lines — truncate the INDEX table if needed and add "see full index at ..."
