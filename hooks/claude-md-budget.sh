#!/bin/bash
# CLAUDE.md Budget Enforcer
# PostToolUse hook: warns when CLAUDE.md exceeds 60-line budget
# Progressive disclosure: keep CLAUDE.md lean, link out for detail

set -e

FILE_PATH="${CLAUDE_FILE_PATH:-}"

# Only care about CLAUDE.md files
[[ -z "$FILE_PATH" ]] && exit 0
BASENAME=$(basename "$FILE_PATH")
[[ "$BASENAME" != "CLAUDE.md" && "$BASENAME" != "claude.md" ]] && exit 0

# Skip files that don't exist yet (Write creating new file)
[[ ! -f "$FILE_PATH" ]] && exit 0

# Count lines
LINE_COUNT=$(wc -l < "$FILE_PATH" | tr -d ' ')
BUDGET=60

if [[ $LINE_COUNT -gt $BUDGET ]]; then
    OVER=$(( LINE_COUNT - BUDGET ))
    cat <<EOF
# CLAUDE.md Budget Warning

**$FILE_PATH** is $LINE_COUNT lines ($OVER over the $BUDGET-line budget).

Progressive disclosure rule: CLAUDE.md loads on EVERY request. Keep it lean.

**To fix — move content to separate docs:**
- Sections >10 lines → \`docs/TOPIC.md\` with one-line link in CLAUDE.md
- File listings → delete (they go stale)
- Standard patterns → delete (agent knows them)
- Detailed docs references → \`.claude/docs/\` directory

Run: \`wc -l $FILE_PATH\` to verify after trimming.
EOF
fi

exit 0
