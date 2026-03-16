#!/bin/bash
# Bridge: extract-learnings SQLite → claude-brain .mv2
# Runs after extract-learnings.py to sync learnings into memvid
# Location: /Users/quartershots/Source/.claude/hooks/learnings-to-mind.sh
#
# Note: mind.mv2 is per-project at .claude/mind.mv2 (not global ~/.claude/mind.mv2)
# This hook syncs learnings from SQLite into the project's memvid memory

set -euo pipefail

# Use nvm's node
export PATH="${HOME}/.nvm/versions/node/v22.12.0/bin:$PATH"

LEARNINGS_DB="${HOME}/Source/.claude/cache/learnings.db"
SYNC_STATE="${HOME}/Source/.claude/cache/learnings-sync-state"
# Project-local mind.mv2 (per claude-brain plugin convention)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
MIND_FILE="${PROJECT_DIR}/.claude/mind.mv2"

# Exit if no learnings DB
[ ! -f "$LEARNINGS_DB" ] && exit 0

# Get last sync timestamp (Unix epoch)
LAST_SYNC=0
[ -f "$SYNC_STATE" ] && LAST_SYNC=$(cat "$SYNC_STATE")

# Query new learnings - format for memvid ingestion
NEW_LEARNINGS=$(sqlite3 "$LEARNINGS_DB" "
  SELECT '[' || upper(category) || '] ' || content
  FROM learnings
  WHERE strftime('%s', created_at) > '$LAST_SYNC'
  ORDER BY created_at ASC
  LIMIT 50
" 2>/dev/null || echo "")

# Exit if nothing new
[ -z "$NEW_LEARNINGS" ] && exit 0

# Find claude-brain plugin
PLUGIN_ROOT=""
for dir in "${HOME}/.claude/plugins/cache/memvid-marketplace/claude-brain" \
           "${HOME}/.claude/plugins/cache/claude-brain"*; do
  [ -d "$dir/node_modules/@memvid/sdk" ] && PLUGIN_ROOT="$dir" && break
done

# If plugin found and SDK available, sync learnings
if [ -n "$PLUGIN_ROOT" ]; then
  COUNT=0

  # Write learnings to temp file as JSON for reliable passing to Node
  TEMP_FILE=$(mktemp)
  echo "$NEW_LEARNINGS" | python3 -c "
import sys, json
learnings = [line.strip() for line in sys.stdin if line.strip()]
print(json.dumps(learnings))
" > "$TEMP_FILE" 2>/dev/null

  # Add all learnings in one Node.js invocation
  cd "$PLUGIN_ROOT" && node << NODESCRIPT
const { use, create } = require('@memvid/sdk');
const { existsSync, readFileSync } = require('fs');
const path = '${MIND_FILE}';
const learnings = JSON.parse(readFileSync('${TEMP_FILE}', 'utf8'));

(async () => {
  if (!learnings.length) process.exit(0);

  try {
    let mv;
    if (existsSync(path)) {
      // use() requires tier as first arg
      mv = await use('basic', path);
    } else {
      mv = await create(path, 'basic');
    }

    let added = 0;
    for (const text of learnings) {
      try {
        // Put with title for better display in mind search
        await mv.put({
          title: '[LEARNING] ' + text.substring(0, 60),
          text: text,
          tags: ['learning', 'self-improvement']
        });
        added++;
      } catch (e) {
        // Skip individual failures
      }
    }

    console.error('Added ' + added + ' learnings to mind.mv2');
    process.exit(0);
  } catch (e) {
    console.error('Error:', e.message);
    process.exit(1);
  }
})();
NODESCRIPT
  COUNT=$?
  rm -f "$TEMP_FILE"

  [ $COUNT -gt 0 ] && echo "Synced $COUNT learnings to mind.mv2" >&2
fi

# Update sync timestamp
date +%s > "$SYNC_STATE"
