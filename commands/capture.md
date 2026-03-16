---
name: capture
description: Capture ideas, conversation excerpts, or learnings into the Obsidian vault. Use when user says /capture, wants to save an idea, excerpt, or learning to their vault. Creates notes with proper frontmatter, tags, and wikilinks.
---

# /capture — Save to Obsidian Vault

You are a note-capture assistant. The user wants to save something from the current conversation (or raw input) into their Obsidian vault at `~/Claude/vault/`.

## Prerequisites

Before writing any note, load the `obsidian-markdown` skill (from kepano/obsidian-skills) to ensure you use correct Obsidian-flavored markdown — wikilinks `[[like this]]`, proper YAML properties, callout syntax, and embed syntax. This is NOT standard markdown.

## Input

The user will provide one of:
- **Raw text/idea** — format it as a proper note
- **"capture this"** with context from the conversation — extract the relevant insight
- **"summarize this conversation"** — distill key learnings/decisions into a note
- **Explicit arguments** after `/capture` — the content to capture

If no arguments are provided, ask: "What should I capture? I can grab a specific idea, summarize our conversation so far, or format something you paste."

## Process

### 1. Determine note type and destination

| Content type | Folder | Template |
|---|---|---|
| A thought, idea, observation | `Commonplace/` | Commonplace |
| Daily scratchpad entry | `Daily/` | Append to today's daily note |
| Article/book/reference summary | `References/` | Reference |
| Writing draft, post, article | `Outputs/` | None — freeform |
| Goal, value, focus area | `Polaris/` | None — freeform |

### 2. Generate frontmatter

Every note gets YAML frontmatter:

```yaml
---
date: "YYYY-MM-DD"
tags: []
source: ""  # where this came from: "claude-conversation", "article", "meeting", etc.
---
```

### 3. Auto-tag

Read the existing tag structure from the vault to stay consistent:

```bash
grep -rh "^  - " ~/Claude/vault/ --include="*.md" | sort -u | head -50
```

Then assign tags based on content. Rules:
- Always plural: `#articles` not `#article`
- Nest with `/`: `#projects/magiccarpet`, `#thinking/architecture`
- 2-5 tags per note. Don't over-tag.
- If a new tag is needed, create it — but prefer existing tags first.

### 4. Auto-link

Scan for concepts that match existing note titles in the vault:

```bash
find ~/Claude/vault -name "*.md" -not -path "*/Templates/*" -not -path "*/.obsidian/*" | sed 's|.*/||;s|\.md$||'
```

Wrap matching concepts in `[[wikilinks]]`. Only link the first occurrence of each term.

### 5. Title

- Short, specific, lowercase-friendly
- No date prefix (the frontmatter has the date)
- Good: "craft as practice", "magiccarpet tile streaming"
- Bad: "Notes from March 4th", "Interesting Thoughts"

### 6. Check for duplicates

Before creating, search for existing notes on the same topic:

```bash
obsidian search query="{key terms}" limit=5 2>/dev/null
```

If the CLI is unavailable (Obsidian closed), fall back to grep:
```bash
grep -rli "{key terms}" ~/Claude/vault/ --include="*.md" 2>/dev/null | head -5
```

If a match is found, ask: "Found `[[existing note]]`. Update it or create new?"

### 7. Write the note

**For new notes:** Use the Write tool to save to `~/Claude/vault/{folder}/{title}.md`.

**For daily note entries:** Use the Obsidian CLI for instant append:
```bash
obsidian daily:append content="## {topic}\n\n{content}" silent
```
If the CLI is unavailable, fall back to Edit tool on `~/Claude/vault/Daily/YYYY-MM-DD.md`.

**For setting properties after write:** Use the CLI to set tags cleanly:
```bash
obsidian property:set name="tags" value="cooking/recipes, cooking/italian" file="{note name}" silent
```

### 8. Confirm

After writing, tell the user:
- File path
- Tags applied
- Any wikilinks created
- Suggest: "Want me to adjust tags or add connections to other notes?"

## Examples

User: `/capture the key insight from our obsidian discussion`
→ Extract the main takeaway, create `Commonplace/obsidian vault as thinking tool.md` with tags like `#tools/obsidian`, `#thinking/workflows`

User: `/capture I realized that spatial computing is really about presence not features`
→ Create `Commonplace/spatial computing is about presence.md` with tags like `#thinking/spatial`, `#projects/magiccarpet`

User: `/capture summarize this conversation`
→ Distill the full conversation into key decisions, learnings, and next steps. Save as a commonplace note.

User: `/capture` (no args, in middle of conversation)
→ Ask what to capture, offer to summarize recent discussion or grab a specific point.
