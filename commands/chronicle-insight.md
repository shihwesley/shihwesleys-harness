---
name: chronicle-insight
description: Extract architectural insights from Chronicler .tech.md files and create proper vault notes. Use when user wants to turn .tech.md documentation into Obsidian vault notes, extract architecture patterns, or create insight notes from chronicler output.
---

# /chronicle-insight — Turn Tech Docs into Thinking Notes

Extract architectural patterns, decisions, and insights from Chronicler `.tech.md` files and create proper Obsidian vault notes. This bridges the gap between auto-generated technical documentation and your personal knowledge graph.

## Why this exists

Chronicler's `.tech.md` files are machine-friendly technical docs — YAML frontmatter, component maps, dependency edges. They're for Claude Code to navigate codebases. But sometimes you discover something worth *thinking about* — an architectural pattern, a design decision, a lesson learned. That belongs in your vault as a note you authored, not as a raw tech dump.

## Process

### 1. Determine what to extract

The user will say something like:
- `/chronicle-insight MagicCarpet` — scan the project for notable patterns
- `/chronicle-insight the tile streaming architecture` — extract insight about a specific area
- `/chronicle-insight` — extract from the current working directory's project

### 2. Read the Chronicler output

Read the project's `.chronicler/INDEX.md` for overview, then read relevant `.tech.md` files for the specific components mentioned.

### 3. Identify what's worth noting

Look for:
- **Architectural decisions** — why was X chosen over Y?
- **Patterns** — recurring approaches across components
- **Dependencies** — surprising or important relationships
- **Complexity hotspots** — components with many edges
- **Lessons** — things that went wrong or were refactored

### 4. Write vault notes

For each insight worth capturing, create a note in `~/Claude/vault/Commonplace/` using the `/capture` skill's conventions:

- Proper frontmatter with date, tags, source: "chronicler/{project}"
- Written in the user's voice, not in tech-doc style
- Wikilinks to existing vault notes where relevant
- Brief — 5-15 lines. The insight, not the implementation details.

### 5. Confirm

Show what was created and suggest connections to existing notes.

## Examples

User: `/chronicle-insight MagicCarpet`

Output: Creates 2-3 notes like:
- `Commonplace/tile streaming as lazy evaluation.md` — connecting the LOD pattern to a broader CS concept
- `Commonplace/magiccarpet dependency graph.md` — noting that the core has surprisingly few dependencies

User: `/chronicle-insight the auth flow is interesting`

Output: Reads auth-related .tech.md files, creates a note about what makes the auth pattern notable.

## Rules

- Never dump raw .tech.md content into the vault
- Write insights, not documentation. "The tile cache uses LRU with a 500MB cap" is documentation. "LRU works here because tile access is spatially correlated — nearby tiles get reused" is an insight.
- 2-5 notes max per invocation. Quality over quantity.
- Always load `obsidian-markdown` skill for proper Obsidian syntax.
- Tag with both `#projects/{name}` and a thinking tag like `#thinking/architecture` or `#thinking/patterns`.
