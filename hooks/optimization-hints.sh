#!/bin/bash
# UserPromptSubmit hook: if 8+ tool calls in previous turn, emit one
# optimization hint (skill, cache, memory, or workflow suggestion).
# Skips when the user's prompt looks exploratory.

LOG="/tmp/.claude-tool-calls"
[[ ! -s "$LOG" ]] && exit 0

# Read tool log, clear for next turn
TOOLS=$(cat "$LOG")
: > "$LOG"

COUNT=$(echo "$TOOLS" | wc -l | tr -d ' ')
[[ "$COUNT" -lt 8 ]] && exit 0

# Try to read user's prompt (JSON or plain text on stdin)
PROMPT=""
while IFS= read -r -t 1 line; do
  PROMPT+="$line "
done

# Extract from JSON if structured
if [[ "$PROMPT" == "{"* ]]; then
  EXTRACTED=$(echo "$PROMPT" | jq -r '.prompt // .message // .content // empty' 2>/dev/null)
  [[ -n "$EXTRACTED" ]] && PROMPT="$EXTRACTED"
fi

# Skip exploratory prompts
if [[ -n "$PROMPT" ]] && echo "$PROMPT" | grep -qiE '^\s*(what |how |why |explain|describe|show |tell me|list |where |can you)'; then
  exit 0
fi

# Count by tool category
SEARCH_N=$(echo "$TOOLS" | grep -cE 'Grep|Glob' 2>/dev/null || echo 0)
READ_N=$(echo "$TOOLS" | grep -c 'Read' 2>/dev/null || echo 0)
EDIT_N=$(echo "$TOOLS" | grep -cE 'Edit|Write' 2>/dev/null || echo 0)
BASH_N=$(echo "$TOOLS" | grep -c 'Bash' 2>/dev/null || echo 0)
TASK_N=$(echo "$TOOLS" | grep -c 'Task' 2>/dev/null || echo 0)

# Find dominant category
MAX=$SEARCH_N; CAT="search"
[[ "$READ_N" -gt "$MAX" ]] && MAX=$READ_N && CAT="read"
[[ "$EDIT_N" -gt "$MAX" ]] && MAX=$EDIT_N && CAT="edit"
[[ "$BASH_N" -gt "$MAX" ]] && MAX=$BASH_N && CAT="bash"
[[ "$TASK_N" -gt "$MAX" ]] && MAX=$TASK_N && CAT="task"

case "$CAT" in
  search) echo "Hint: ${COUNT} tool calls last turn (${SEARCH_N} searches) — try Explore agent or TLDR cache for broad scans." ;;
  read)   echo "Hint: ${COUNT} tool calls last turn (${READ_N} reads) — check CODEBASE_MAP or .chronicler summaries before reading source." ;;
  edit)   echo "Hint: ${COUNT} tool calls last turn (${EDIT_N} edits) — if repetitive, extract a reusable skill to batch them." ;;
  bash)   echo "Hint: ${COUNT} tool calls last turn (${BASH_N} shell calls) — wrap repeated commands in a hook or alias." ;;
  task)   echo "Hint: ${COUNT} tool calls last turn (${TASK_N} agents) — try a broader prompt to one agent instead of multiple spawns." ;;
  *)      echo "Hint: ${COUNT} tool calls last turn — look for a skill, cache, or memory pattern to compress this." ;;
esac
