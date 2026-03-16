#!/bin/bash
# Logs each tool call to temp file for per-turn counting.
# Paired with optimization-hints.sh (UserPromptSubmit) which reads + clears.

LOG="/tmp/.claude-tool-calls"
INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null || echo "unknown")
echo "$TOOL" >> "$LOG"
