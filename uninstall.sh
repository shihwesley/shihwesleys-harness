#!/usr/bin/env bash
# shihwesleys-harness uninstaller
# Removes symlinks and restores .bak files if they exist
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SOURCE_CLAUDE="$HOME/Source/.claude"

remove_link() {
  local dest="$1"
  if [ -L "$dest" ]; then
    rm "$dest"
    if [ -e "${dest}.bak" ]; then
      mv "${dest}.bak" "$dest"
      echo "  Restored: $(basename "$dest")"
    else
      echo "  Removed: $(basename "$dest")"
    fi
  fi
}

echo "Uninstalling shihwesleys-harness symlinks..."

for f in "$HARNESS_DIR"/commands/*.md; do
  [ -f "$f" ] || continue
  remove_link "$CLAUDE_DIR/commands/$(basename "$f")"
done
for d in "$HARNESS_DIR"/commands/*/; do
  [ -d "$d" ] || continue
  remove_link "$CLAUDE_DIR/commands/$(basename "$d")"
done
for f in "$HARNESS_DIR"/agents/*.md; do
  [ -f "$f" ] || continue
  remove_link "$CLAUDE_DIR/agents/$(basename "$f")"
done
for f in "$HARNESS_DIR"/scripts/*; do
  [ -f "$f" ] || continue
  remove_link "$CLAUDE_DIR/scripts/$(basename "$f")"
done
for f in "$HARNESS_DIR"/hooks/*; do
  [ -f "$f" ] || continue
  remove_link "$CLAUDE_DIR/hooks/$(basename "$f")"
done
for f in "$HARNESS_DIR"/hooks/chronicler/*; do
  [ -f "$f" ] || continue
  remove_link "$CLAUDE_DIR/hooks/chronicler/$(basename "$f")"
done
for f in "$HARNESS_DIR"/graphs/swift-graph/*; do
  [ -f "$f" ] || continue
  remove_link "$SOURCE_CLAUDE/docs/swift-graph/$(basename "$f")"
done
for f in "$HARNESS_DIR"/graphs/agent-infra-graph/*; do
  [ -f "$f" ] || continue
  remove_link "$SOURCE_CLAUDE/docs/agent-infra-graph/$(basename "$f")"
done

echo "Done. Symlinks removed."
