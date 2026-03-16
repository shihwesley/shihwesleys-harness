#!/bin/bash
# Blackboard Writer - Captures agent outputs for cross-agent sharing
# Enables code-explorer, code-architect, code-reviewer to share findings
# Location: /Users/quartershots/Source/.claude/hooks/blackboard-writer.sh

set -euo pipefail

CLAUDE_DIR="/Users/quartershots/Source/.claude"
CACHE_DIR="$CLAUDE_DIR/cache"
BLACKBOARD="$CACHE_DIR/blackboard.json"

# Read hook input
INPUT=$(cat)

# Extract agent info - try multiple possible field names
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // .id // "unknown"')
AGENT_TYPE=$(echo "$INPUT" | jq -r '.subagent_type // .agent_type // .type // "unknown"')

# Try multiple output field names and handle nested structures
AGENT_OUTPUT=$(echo "$INPUT" | jq -r '
  .output // .result // .message // .content //
  (if .tool_result then .tool_result.content else "" end) //
  ""
' 2>/dev/null || echo "")

# If output is empty, try to stringify the whole input for debugging
if [[ -z "$AGENT_OUTPUT" ]] || [[ "$AGENT_OUTPUT" == "null" ]]; then
  AGENT_OUTPUT=$(echo "$INPUT" | jq -r 'to_entries | map("\(.key): \(.value | tostring | .[0:100])") | join("\n")' 2>/dev/null || echo "")
fi
TIMESTAMP=$(date +%s)

# Initialize blackboard if doesn't exist
if [[ ! -f "$BLACKBOARD" ]]; then
  echo '{"session_id":"","messages":[]}' > "$BLACKBOARD"
fi

# Extract key files from agent output (file:line patterns)
KEY_FILES=$(echo "$AGENT_OUTPUT" | grep -oE '[a-zA-Z0-9_/.-]+\.(ts|tsx|js|jsx|py|swift|go|rs|java|cpp|c|h):[0-9]+' | head -15 | sort -u || echo "")

# Extract patterns/insights (lines with key phrases)
PATTERNS=$(echo "$AGENT_OUTPUT" | grep -i "pattern\|convention\|approach\|architecture\|uses\|implements" | head -5 || echo "")

# Extract recommendations
RECOMMENDATIONS=$(echo "$AGENT_OUTPUT" | grep -i "recommend\|suggest\|should\|consider\|prefer" | head -5 || echo "")

# Determine message type based on agent
case "$AGENT_TYPE" in
  *explorer*|*Explore*|Explore)
    MSG_TYPE="discovery"
    ;;
  *architect*|*Plan*)
    MSG_TYPE="design"
    ;;
  *reviewer*|*review*)
    MSG_TYPE="review"
    ;;
  *)
    MSG_TYPE="general"
    ;;
esac

# Create message object
MESSAGE=$(jq -n \
  --arg from "$AGENT_TYPE" \
  --arg id "$AGENT_ID" \
  --arg type "$MSG_TYPE" \
  --arg files "$KEY_FILES" \
  --arg patterns "$PATTERNS" \
  --arg recs "$RECOMMENDATIONS" \
  --arg time "$TIMESTAMP" \
  '{
    "from": $from,
    "agent_id": $id,
    "type": $type,
    "timestamp": ($time | tonumber),
    "data": {
      "key_files": ($files | split("\n") | map(select(length > 0))),
      "patterns": ($patterns | split("\n") | map(select(length > 0))),
      "recommendations": ($recs | split("\n") | map(select(length > 0)))
    }
  }')

# Auto-expire messages older than 2 hours and append new message
CUTOFF=$(($(date +%s) - 7200))
UPDATED=$(jq --argjson msg "$MESSAGE" --arg cutoff "$CUTOFF" '
  .messages = (.messages | map(select(.timestamp > ($cutoff | tonumber)))) |
  .messages += [$msg] |
  .messages = .messages[-20:] |
  .last_updated = now
' "$BLACKBOARD")

echo "$UPDATED" > "$BLACKBOARD"

# Log what was captured (only if meaningful)
FILE_COUNT=$(echo "$KEY_FILES" | grep -c . || echo 0)
[[ $FILE_COUNT -gt 0 ]] && echo "Blackboard: captured $FILE_COUNT files from $AGENT_TYPE agent" >&2

exit 0
