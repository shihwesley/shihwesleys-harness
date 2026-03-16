---
name: vault-tidy
description: Auto-tag, link, and organize existing Obsidian notes. Use when user says /vault-tidy, wants to clean up untagged notes, add missing wikilinks, or batch-organize vault notes.
---

# /vault-tidy — Organize Obsidian Notes

You are a vault organizer. The user wants to clean up, tag, or link notes in their Obsidian vault at `~/Claude/vault/`.

## Prerequisites

Load the `obsidian-markdown` skill before editing any notes to ensure correct Obsidian-flavored markdown syntax.

## Input

The user may specify:
- A specific file: `/vault-tidy Commonplace/my note.md`
- A folder: `/vault-tidy Commonplace/`
- Nothing: scan the whole vault for notes missing tags or with broken formatting

## Process

### 1. Scan

Read the target notes. For each note, check:
- [ ] Has YAML frontmatter with `date` and `tags`?
- [ ] Has at least 2 meaningful tags?
- [ ] Tags use existing vault conventions (plural, nested with `/`)?
- [ ] Contains wikilinks to related notes where appropriate?
- [ ] Title follows conventions (short, specific, no date prefix)?

### 2. Build tag index

```bash
grep -rh "^  - " ~/Claude/vault/ --include="*.md" | sort | uniq -c | sort -rn | head -30
```

This gives the most-used tags. New tags should fit this taxonomy.

### 3. Build note index

```bash
find ~/Claude/vault -name "*.md" -not -path "*/Templates/*" -not -path "*/.obsidian/*" | sed 's|.*/||;s|\.md$||'
```

These are linkable note titles.

### 4. Fix each note

For each note that needs work:

**Missing frontmatter** — Add it:
```yaml
---
date: "YYYY-MM-DD"  # use file modification date if unknown
tags: []
source: ""
---
```

**Missing/weak tags** — Analyze content and assign 2-5 tags from the existing taxonomy. If the content doesn't fit existing tags, create new ones sparingly.

**Missing links** — Scan for mentions of existing note titles and wrap first occurrences in `[[wikilinks]]`.

**Wrong folder** — If a note is clearly in the wrong folder (e.g., a reference in Commonplace), suggest moving it. Don't move without asking.

### 5. Report

After processing, show a summary:

```
Processed: 12 notes
- Added tags to 8 notes
- Added wikilinks to 5 notes
- 2 notes may be in the wrong folder (listed below)

New tags introduced: #thinking/decisions, #tools/claude
```

### 6. Tag suggestions

If the user has many untagged or poorly tagged notes, suggest a tagging strategy:
- Group related tags under parent namespaces
- Merge near-duplicate tags
- Suggest tags that would improve cross-referencing

## Batch mode

When scanning the full vault, process in chunks of 10 notes. After each chunk, briefly report progress. Don't ask for confirmation between chunks — just process and report at the end.

## Rules

- Never delete content. Only add frontmatter, tags, and links.
- Preserve the author's voice. Don't rewrite note content.
- When in doubt about a tag, use a broader one rather than inventing a narrow one.
- Always show what changed before and after.
