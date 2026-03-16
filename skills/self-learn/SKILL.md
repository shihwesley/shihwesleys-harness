---
name: self-learn
description: Trigger self-learning synthesis on demand. Analyzes recent session learnings, clusters patterns, and updates MEMORY.md with verified insights. Use when user says /self-learn, wants to consolidate learnings, or needs to manually trigger the synthesis that normally runs on session end.
user-invocable: true
arguments:
  - name: force
    description: Run even if below the 5-learning threshold
    required: false
---

# Self-Learning Protocol

Trigger the self-learning synthesis to analyze recent session learnings and update MEMORY.md.

## What It Does

1. **Aggregates** learnings from `learnings.db` (patterns, gotchas, decisions, tool errors, pivots)
2. **Checks threshold** — only runs if ≥5 new learnings since last synthesis (unless `--force`)
3. **Synthesizes** insights using Claude Haiku (~$0.01-0.03 per run)
4. **Updates** MEMORY.md with actionable patterns, pitfalls, and recommendations

## Usage

```
/self-learn          # Normal run (respects 5-learning threshold)
/self-learn --force  # Force run even below threshold
```

## When to Use

- After a productive session with many discoveries
- When you want to review accumulated patterns
- Before starting a new project (to recall cross-project learnings)
- When the periodic scheduler hasn't run recently

## Implementation

Run this command:

```bash
bash /Users/quartershots/Source/.claude/scripts/self-learn.sh $ARGS
```

Where `$ARGS` is `--force` if the user specified force.

## Periodic Schedule

A LaunchAgent runs this every 12 hours automatically (threshold-gated):
- Location: `~/Library/LaunchAgents/com.claude.self-learn.plist`
- Load: `launchctl load ~/Library/LaunchAgents/com.claude.self-learn.plist`
- Unload: `launchctl unload ~/Library/LaunchAgents/com.claude.self-learn.plist`
- Status: `launchctl list | grep self-learn`

## Output

Updates `/Users/quartershots/Source/.claude/projects/-Users-quartershots-Source/memory/MEMORY.md` with:
- Top patterns observed
- Common pitfalls to avoid
- Workflow recommendations
- Tool performance notes
