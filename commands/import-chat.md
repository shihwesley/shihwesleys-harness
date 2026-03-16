---
name: import-chat
description: Import content from a Claude.ai web conversation into the Obsidian vault. Use when user says /import-chat, wants to save a Claude.ai conversation to Obsidian, or import chat history into their vault.
---

# /import-chat — Import Claude.ai Web Chat into Vault

The user has content from a Claude.ai web conversation (or any chat) they want to save to their Obsidian vault at `~/Claude/vault/`.

## Prerequisites

Load the `obsidian-markdown` skill for proper Obsidian syntax.

## Input

The user will paste one of:
- **Raw chat transcript** — extract the useful parts, discard the back-and-forth
- **A summary they wrote** — format and file it
- **A recipe, how-to, or reference** — structure it properly
- **A grocery/shopping list** — format as a checklist note

If no content is pasted, ask: "Paste the content from your chat, or describe what you want to save."

## Process

### 1. Detect content type and route

| Content type | Folder | Format |
|---|---|---|
| Recipe | `References/Cooking/` | Ingredients checklist + method + tips |
| How-to / tutorial | `References/` | Step-by-step with context |
| Grocery / shopping list | `Commonplace/` | Checklist with `- [ ]` items |
| General knowledge | `Commonplace/` | Prose with key points |
| Decision / recommendation | `Commonplace/` | What was decided and why |
| Creative writing / draft | `Outputs/` | As-is with light formatting |

### 2. Extract signal from noise

Chat transcripts have a lot of back-and-forth. Extract only:
- The final, refined answer (not early drafts)
- Key decisions and reasoning
- Actionable items (recipes, steps, lists)
- Skip: greetings, "let me think about that", corrections, tangents

### 3. Structure as Obsidian note

Every note gets frontmatter:
```yaml
---
date: "YYYY-MM-DD"
tags: []
source: "claude-chat"
project: ""  # e.g., "chef", "coding", etc.
---
```

For recipes specifically:
```yaml
---
date: "YYYY-MM-DD"
tags:
  - cooking/recipes
  - cooking/{cuisine}
source: "claude-chat"
project: "chef"
servings: 4
prep_time: ""
cook_time: ""
---
```

Recipe format:
```markdown
# {Dish Name}

## Ingredients
- [ ] 400g spaghetti
- [ ] 200g guanciale
...

## Method
1. Step one
2. Step two
...

## Tips
- Key insight from the conversation
```

Grocery list format:
```markdown
# Grocery List — {date or context}

## Produce
- [ ] item

## Dairy
- [ ] item

## Pantry
- [ ] item
```

### 4. Auto-tag and link

Scan vault for existing tags and note titles. Apply consistent tags.
For cooking notes, use nested tags: `cooking/recipes`, `cooking/italian`, `cooking/techniques`, `cooking/ingredients`.

### 5. Duplicate check

Before writing, scan the vault for notes with similar titles:
```bash
find ~/Claude/vault -name "*.md" | xargs grep -li "{key terms}" 2>/dev/null | head -5
```

If a similar note exists, ask: "Found an existing note on {topic}. Want me to update it or create a new one?"

### 6. Write and confirm

Save the note. Report file path, tags, and any wikilinks created.

## Examples

User: `/import-chat` then pastes a carbonara recipe conversation
→ Creates `References/Cooking/pasta carbonara.md` with ingredients as checkboxes, tagged `#cooking/recipes`, `#cooking/italian`

User: `/import-chat` then pastes a grocery list from a meal planning chat
→ Creates `Commonplace/grocery list 2026-03-04.md` with categorized checkboxes

User: `/import-chat` then pastes a long debugging conversation
→ Extracts the solution, creates `Commonplace/fixing xcode build cache.md` with the key steps
