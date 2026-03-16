#!/bin/bash
# Session Start Context Injector
# Loads continuity ledger, blackboard, and learnings into new sessions
# Location: /Users/quartershots/Source/.claude/hooks/session-start-context.sh

set -euo pipefail

CLAUDE_DIR="/Users/quartershots/Source/.claude"
CACHE_DIR="$CLAUDE_DIR/cache"
THOUGHTS_DIR="$CLAUDE_DIR/thoughts"
BLACKBOARD="$CACHE_DIR/blackboard.json"
LEDGER="$THOUGHTS_DIR/RALPH_LEDGER.md"
LEARNINGS_DB="$CACHE_DIR/learnings.db"
RALPH_STATE=".claude/ralph-loop.local.md"

OUTPUT=""

# === RALPH LOOP CONTEXT ===
if [[ -f "$RALPH_STATE" ]]; then
  ITERATION=$(sed -n 's/^iteration: //p' "$RALPH_STATE" 2>/dev/null || echo "?")
  OUTPUT+="## Active Ralph Loop (Iteration $ITERATION)\n\n"

  # Include last 3 iterations from ledger
  if [[ -f "$LEDGER" ]]; then
    RECENT_LEDGER=$(tail -100 "$LEDGER" | grep -A 20 "## Iteration" | tail -60)
    OUTPUT+="### Recent Iteration History\n\`\`\`\n$RECENT_LEDGER\n\`\`\`\n\n"
  fi
fi

# === BLACKBOARD CONTEXT (Agent shared memory) ===
if [[ -f "$BLACKBOARD" ]]; then
  # Check if blackboard has recent messages (last 30 min)
  CUTOFF=$(($(date +%s) - 1800))
  RECENT_MSGS=$(jq -r --arg cutoff "$CUTOFF" '
    .messages |
    map(select(.timestamp > ($cutoff | tonumber))) |
    if length > 0 then
      "### Agent Blackboard (shared memory)\n" +
      (map("- **\(.from)** [\(.type)]: \(.data.key_files | join(", ") | .[0:100])") | join("\n"))
    else
      ""
    end
  ' "$BLACKBOARD" 2>/dev/null || echo "")

  if [[ -n "$RECENT_MSGS" ]]; then
    OUTPUT+="$RECENT_MSGS\n\n"
  fi
fi

# === PERSISTENT LEARNINGS ===
if [[ -f "$LEARNINGS_DB" ]]; then
  PROJECT_PATH=$(pwd)
  LEARNINGS=$(sqlite3 "$LEARNINGS_DB" "
    SELECT '- ' || content
    FROM learnings
    WHERE project_path LIKE '%${PROJECT_PATH##*/}%'
    ORDER BY created_at DESC
    LIMIT 5
  " 2>/dev/null || echo "")

  if [[ -n "$LEARNINGS" ]]; then
    OUTPUT+="### Recalled Learnings\n$LEARNINGS\n\n"
  fi
fi

# === CONTEXT FORWARD (post-/clear continuation) ===
CONTEXT_FWD="$CACHE_DIR/context-forward.md"
if [[ -f "$CONTEXT_FWD" ]]; then
  FWD_CONTENT=$(cat "$CONTEXT_FWD" 2>/dev/null)
  if [[ -n "$FWD_CONTENT" ]]; then
    OUTPUT+="### Forwarded Context (from previous session)\n$FWD_CONTENT\n\n"
  fi
  # Consume the file — one-time use
  rm -f "$CONTEXT_FWD"
fi

# === WORKIN DIRECTORY RESTORE ===
LAST_WORKIN="$HOME/.claude/last-workin"
if [[ -f "$LAST_WORKIN" ]]; then
  RESTORE_DIR=$(cat "$LAST_WORKIN" 2>/dev/null)
  if [[ -d "$RESTORE_DIR" ]]; then
    OUTPUT+="### Working Directory Restore\nAuto-cd to: $RESTORE_DIR\n\n"
  fi
fi

# === SKILL GRAPH DETECTION ===
GRAPH_INDEX="/Users/quartershots/Source/.claude/docs/swift-graph/index.md"
if [[ -f "$GRAPH_INDEX" ]]; then
  # Check if current project is iOS/Swift (has .swift files or .xcodeproj)
  HAS_SWIFT=$(find . -maxdepth 3 -name "*.swift" -o -name "*.xcodeproj" 2>/dev/null | head -1)
  if [[ -n "$HAS_SWIFT" ]]; then
    MOC_COUNT=$(ls "$CLAUDE_DIR/docs/swift-graph/"*.md 2>/dev/null | wc -l | tr -d ' ')
    OUTPUT+="### Swift Skill Graph: $MOC_COUNT MOCs available\n"
    OUTPUT+="Navigate via \`.claude/docs/swift-graph/index.md\` before loading iOS/visionOS docs.\n\n"
  fi
fi

# === TLDR CACHE STATUS ===
CACHE_COUNT=$(find "$CACHE_DIR/tldr" -name "*.tldr" 2>/dev/null | wc -l | tr -d ' ')
if [[ $CACHE_COUNT -gt 0 ]]; then
  OUTPUT+="### TLDR Cache: $CACHE_COUNT files indexed\n\n"
fi

# Output context if we have any
if [[ -n "$OUTPUT" ]]; then
  echo -e "$OUTPUT"
fi

exit 0
