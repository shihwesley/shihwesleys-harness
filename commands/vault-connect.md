---
name: vault-connect
description: Find hidden connections between notes. Suggests wikilinks, related ideas, and threads worth exploring. Use when user says /vault-connect, wants to discover links between notes, find related ideas, or strengthen their knowledge graph.
---

# /vault-connect — Find Connections in Your Vault

You surface connections between notes that the user might have missed, suggest threads worth exploring, and generate "idea reports" on demand.

## Prerequisites

Load the `obsidian-markdown` skill before suggesting any note content to ensure correct Obsidian-flavored markdown syntax.

## Vault location

`~/Claude/vault/`

## Modes

### Default: Connection scan
Scan recent notes (last 2 weeks by modification date) and find:
- Notes that discuss similar themes but aren't linked
- Ideas that build on each other across time
- Contradictions or tensions worth exploring
- Threads started but not followed up on

### With argument: Focused analysis
`/vault-connect #craft` — find connections among notes with a specific tag
`/vault-connect "note title"` — find what connects to a specific note

### "idea report" mode
If the user says something like "what should I work on" or "idea report":

1. Read `Polaris/Top of Mind.md` for current priorities
2. Scan recent Daily notes for patterns and uncommitted tasks
3. Scan Commonplace for ideas that haven't been developed
4. Cross-reference with Outputs to see what's in progress

Output format:
```
## Idea Report — YYYY-MM-DD

### Build
Things worth building or prototyping based on recent thinking.
- [suggestion with [[linked notes]]]

### Write
Ideas ripe enough to become an Output.
- [suggestion with [[linked notes]]]

### Explore
Threads worth pulling on — incomplete thoughts, open questions.
- [suggestion with [[linked notes]]]

### Connect
People to reach out to, conversations to have.
- [suggestion with [[linked notes]]]

### Revisit
Notes or commitments that may have gone stale.
- [suggestion with [[linked notes]]]
```

## Process

1. Build a note index (titles + tags + first 5 lines of content)
2. Read `Polaris/` folder for priorities and values
3. Identify clusters of related notes
4. Find gaps — things mentioned but not explored
5. Present connections as suggestions with specific note references

## Rules

- Always reference specific notes by `[[wikilink]]`
- Don't fabricate connections. Only surface real overlaps in the user's writing.
- Bias toward actionable suggestions over abstract observations.
- Read the Polaris folder every time — it anchors relevance.
