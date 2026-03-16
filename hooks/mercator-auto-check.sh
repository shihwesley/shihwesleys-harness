#!/bin/bash
# mercator-auto-check.sh
# PostToolUse hook (Bash matcher) — after git commits, auto-refreshes the
# merkle manifest and invalidates TLDR cache for changed files.
#
# This is the KEY to preventing staleness without burning LLM tokens:
# - Manifest refresh = pure Python (hashing), ~2s, zero tokens
# - TLDR cache invalidation = delete stale cache files, zero tokens
# - Architecture prose in CODEBASE_MAP.md is NOT updated here (that needs LLM)
#   Only structure changes (new/removed modules) flag a manual /mercator-ai run
#
# Cost: ~2 seconds of Python execution. No API calls. No tokens.

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Only trigger on git commit (not other git operations)
echo "$COMMAND" | grep -qE 'git\s+commit\s' || exit 0

# Skip .claude/ meta-commits
echo "$COMMAND" | grep -qE '\.claude/' && exit 0

# Find project root
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
MANIFEST="$PROJECT_ROOT/docs/.mercator.json"

# No manifest = never mapped, skip
[ -f "$MANIFEST" ] || exit 0

# Find scanner script
SCANNER=""
for path in \
  "/Users/quartershots/Source/.claude/plugins/cache/mercator-ai/mercator-ai/"*/skills/mercator-ai/scripts/scan-codebase.py; do
  [ -f "$path" ] && SCANNER="$path" && break
done
[ -z "$SCANNER" ] && exit 0

# --- Step 1: Get diff BEFORE refreshing manifest ---
PYTHON=$(/usr/bin/which python3 2>/dev/null || echo "/opt/homebrew/bin/python3")
DIFF_OUTPUT=$(cd "$PROJECT_ROOT" && "$PYTHON" "$SCANNER" . --diff "$MANIFEST" 2>/dev/null) || exit 0
HAS_CHANGES=$(echo "$DIFF_OUTPUT" | jq -r '.has_changes // false' 2>/dev/null)

[ "$HAS_CHANGES" = "true" ] || exit 0

# --- Step 2: Refresh the manifest (pure Python, no LLM) ---
cd "$PROJECT_ROOT" && "$PYTHON" "$SCANNER" . --format json > "$MANIFEST.tmp" 2>/dev/null && \
  mv "$MANIFEST.tmp" "$MANIFEST"

# --- Step 3: Invalidate TLDR cache for changed/added files ---
TLDR_CACHE="/Users/quartershots/Source/.claude/cache/tldr"
if [ -d "$TLDR_CACHE" ]; then
  # Get list of changed + added files
  CHANGED_FILES=$(echo "$DIFF_OUTPUT" | jq -r '(.changed // []) + (.added // []) | .[]' 2>/dev/null)
  for file in $CHANGED_FILES; do
    # TLDR cache keys are based on file path — remove matching entries
    CACHE_KEY=$(echo -n "$PROJECT_ROOT/$file" | md5 2>/dev/null || echo -n "$PROJECT_ROOT/$file" | md5sum 2>/dev/null | cut -d' ' -f1)
    rm -f "$TLDR_CACHE/$CACHE_KEY"* 2>/dev/null
  done
fi

# --- Step 4: Report what happened ---
CHANGED=$(echo "$DIFF_OUTPUT" | jq -r '.changed | length // 0' 2>/dev/null)
ADDED=$(echo "$DIFF_OUTPUT" | jq -r '.added | length // 0' 2>/dev/null)
REMOVED=$(echo "$DIFF_OUTPUT" | jq -r '.removed | length // 0' 2>/dev/null)

echo "Merkle manifest refreshed (changed: $CHANGED, added: $ADDED, removed: $REMOVED)."

# Flag if structural changes need a full /mercator-ai run
if [ "$ADDED" -gt 0 ] || [ "$REMOVED" -gt 0 ]; then
  echo "New/removed files detected — run /mercator-ai to update architecture diagrams."

  # Auto-sync CLAUDE.md stats if the project has the sync script
  SYNC_SCRIPT="$PROJECT_ROOT/scripts/sync-claude-md-stats.sh"
  if [ -x "$SYNC_SCRIPT" ]; then
    /bin/zsh "$SYNC_SCRIPT" 2>/dev/null && echo "CLAUDE.md stats auto-synced." || true
  fi
fi
