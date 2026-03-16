---
name: init
version: "2.0.0"
description: Initialize a project with lean CLAUDE.md + codebase map (mercator-ai). Handles fresh and existing codebases.
user-invocable: true
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "AskUserQuestion", "Skill", "Task"]
---

# Project Initialization

Creates a **lean, focused** CLAUDE.md + codebase map following the two-layer pattern:

- **Global `~/.claude/CLAUDE.md`** — universal patterns across all projects (writing style, context management, tool rules)
- **Per-project `CLAUDE.md`** — map reference + project-specific conventions only

## When to Use

| Scenario | Use |
|----------|-----|
| New or existing project | `/init` (this skill) |
| Re-map after major refactor | `/mercator-ai` directly |
| Update existing CLAUDE.md | `/revise-claude-md` |

## Core Philosophy: Progressive Disclosure + Map-First

> "Give agents only what they need now, pointing elsewhere for detailed guidance."
> "Every problem with coding agents can be solved by informing them." — cartographer pattern

**Token budget:** 60 lines max. Every token loads on EVERY request.

### What Goes Inline vs Linked Out

| Content | Inline in CLAUDE.md | Link to separate doc |
|---|---|---|
| One-sentence description | yes | — |
| Build command (1-2 lines) | yes | — |
| 2-3 critical conventions | yes | — |
| Codebase map reference | yes (1 line) | `docs/CODEBASE_MAP.md` |
| Detailed architecture | no | `docs/ARCHITECTURE.md` |
| Testing strategy (>5 lines) | no | `docs/TESTING.md` |
| File listings | **never** (go stale) | — |
| Standard patterns | **never** (agent knows) | — |

## Process

### 1. Detect Project State

**Check project type:**
- `package.json` → Node.js/TypeScript
- `*.xcodeproj` or `Package.swift` → Swift/iOS
- `requirements.txt` or `pyproject.toml` → Python
- `Cargo.toml` → Rust
- `go.mod` → Go
- `Gemfile` → Ruby

**Check codebase maturity:**

```bash
# Count source files (excluding config, docs, planning files)
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
  -o -name "*.py" -o -name "*.swift" -o -name "*.rs" -o -name "*.go" -o -name "*.rb" \) \
  -not -path "*/node_modules/*" -not -path "*/.build/*" -not -path "*/venv/*" | wc -l
```

Classify:
- **0 source files** → `fresh` (empty or planning-only project)
- **1+ source files** → `mappable` (has code to map)

Also check: does `docs/CODEBASE_MAP.md` or `docs/.mercator.json` already exist? If yes → `already-mapped`.

### 2. Ask Key Questions

```
AskUserQuestion (all projects):
- "One-sentence project description?"
- "Non-standard build commands?" (if standard detected, skip)

AskUserQuestion (project-specific patterns — THE KEY QUESTION):
- "Any patterns you want enforced or avoided in THIS codebase?"
  description: "Things like: 'no classes, only functions', 'always use Result type for errors',
  'fetch calls go through the API layer only', or annoyances you've hit with agents before.
  These go in your per-project CLAUDE.md. Universal rules belong in ~/.claude/CLAUDE.md."
  options:
    1. "I'll list some now"
    2. "None yet, I'll add them as I go"
    3. "Let me think — skip for now"
```

If user provides patterns, include them in the Conventions section (max 5 items — if they give more, put the rest in `docs/CONVENTIONS.md`).

### 3. Generate Lean CLAUDE.md

**Template structure (max ~50 lines):**

```markdown
# CLAUDE.md

[One-sentence project description]

## Build

[Only if non-standard — otherwise omit entirely]
`[build command]`

## Exploration

Read `docs/CODEBASE_MAP.md` before scanning files. Use manifest (`docs/.mercator.json`) for targeted reads.
[If fresh project: "No map yet — run `/mercator-ai` after initial scaffold is created."]

## Conventions

[Project-specific rules from user input — things that would break if ignored]
[These are patterns unique to THIS codebase, not universal rules]

## Documentation

For [topic], see `docs/[TOPIC].md`
```

**After writing, verify:** `wc -l CLAUDE.md` — must be under 60.

**Anti-patterns — do NOT include in per-project CLAUDE.md:**
- Context window management (already in global)
- Writing style rules (already in global)
- Tool path rules (already in global)
- `Context Awareness` boilerplate (already in global)
- Standard framework patterns (agent knows these)
- File listings (go stale — the map handles this)

### 4. Create docs/ Directory Structure (if needed)

Only create separate docs for topics that need >10 lines of explanation:

```
docs/
├── CODEBASE_MAP.md    # Created by mercator-ai (Step 5)
├── ARCHITECTURE.md    # Only if complex
├── TESTING.md         # Only if non-standard
└── API.md             # Only if has API
```

### 5. Generate Codebase Map

**Based on project state from Step 1:**

#### If `mappable` (has source files):

Chain directly to mercator-ai:

```
Invoke Skill tool: mercator-ai
```

This runs the full mercator workflow:
1. Scans codebase (`scan-codebase.py`)
2. Spawns Sonnet subagents to read and document modules
3. Writes `docs/CODEBASE_MAP.md` + `docs/.mercator.json`
4. Updates CLAUDE.md with codebase overview summary

The `PostToolUse:Bash` hook on `git commit` keeps the manifest fresh automatically after this. Only structural changes (new/removed modules) need a manual `/mercator-ai` re-run.

#### If `fresh` (no source files yet):

Skip mercator scan. The CLAUDE.md already has the stub:
```
Read `docs/CODEBASE_MAP.md` before scanning files.
No map yet — run `/mercator-ai` after initial scaffold is created.
```

**Check for planning files:** If `.claude/plans/` or `specs/` exist (from `/interactive-planning`), mention them in the CLAUDE.md:
```
## Planning

Implementation plan at `.claude/plans/[plan-file]`. Follow phase order.
```

#### If `already-mapped`:

Skip mercator scan. The map already exists and the hook keeps it fresh.
Tell the user: "Map already exists at `docs/CODEBASE_MAP.md`. Run `/mercator-ai` to refresh if needed."

### 6. Initialize Orbit Environment

```
Invoke Skill tool: orbit with args: "init"
```

Chains to `/orbit init` which detects project type and creates `.orbit/config.json`.
If Orbit detects an unsupported project type (Swift/Xcode), it skips gracefully.

## Example Outputs

**Existing Node.js project (mappable):**
```markdown
# CLAUDE.md

Real-time collaborative whiteboard using WebSockets.

## Build

`pnpm install && pnpm dev`

## Exploration

Read `docs/CODEBASE_MAP.md` before scanning files. Use manifest (`docs/.mercator.json`) for targeted reads.

## Conventions

- WebSocket messages go through `src/protocol/` — no raw ws.send() elsewhere
- All canvas operations are CRDT-based — never mutate state directly
- Use `Result<T>` pattern for all service-layer returns
```

**Fresh project (planning only):**
```markdown
# CLAUDE.md

iOS app for tracking indoor climbing progress with AR route visualization.

## Exploration

No map yet — run `/mercator-ai` after initial scaffold is created.

## Planning

Implementation plan at `.claude/plans/climbing-app.md`. Follow phase order.

## Conventions

- SwiftUI only, no UIKit unless wrapping hardware APIs
- All persistence through GRDB, no Core Data
```

## Post-Init Checklist

- [ ] CLAUDE.md is under 60 lines
- [ ] No duplication of global CLAUDE.md content (context mgmt, writing style, tool rules)
- [ ] Project-specific patterns captured (or user deferred)
- [ ] Exploration section points to map (or has "run mercator" stub)
- [ ] Map generated (if code exists) or stub placed (if fresh)
- [ ] Orbit initialized (or skipped for unsupported types)
