#!/usr/bin/env bash
# shihwesleys-harness installer
# Creates symlinks from ~/.claude/ directories to this repo
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SOURCE_CLAUDE="$HOME/Source/.claude"

echo "Installing shihwesleys-harness from: $HARNESS_DIR"
echo "Target: $CLAUDE_DIR"
echo ""

backup_and_link() {
  local src="$1"
  local dest="$2"
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    echo "  Backing up: $dest → ${dest}.bak"
    mv "$dest" "${dest}.bak"
  elif [ -L "$dest" ]; then
    rm "$dest"
  fi
  ln -s "$src" "$dest"
  echo "  Linked: $(basename "$dest")"
}

# --- Commands (skills) ---
echo "=== Skills ==="
for f in "$HARNESS_DIR"/commands/*.md; do
  [ -f "$f" ] || continue
  backup_and_link "$f" "$CLAUDE_DIR/commands/$(basename "$f")"
done
for d in "$HARNESS_DIR"/commands/*/; do
  [ -d "$d" ] || continue
  name=$(basename "$d")
  backup_and_link "$d" "$CLAUDE_DIR/commands/$name"
done

# --- Agents ---
echo "=== Agents ==="
mkdir -p "$CLAUDE_DIR/agents"
for f in "$HARNESS_DIR"/agents/*.md; do
  [ -f "$f" ] || continue
  backup_and_link "$f" "$CLAUDE_DIR/agents/$(basename "$f")"
done

# --- Scripts ---
echo "=== Scripts ==="
mkdir -p "$CLAUDE_DIR/scripts"
for f in "$HARNESS_DIR"/scripts/*; do
  [ -f "$f" ] || continue
  backup_and_link "$f" "$CLAUDE_DIR/scripts/$(basename "$f")"
done

# --- Hooks ---
echo "=== Hooks ==="
mkdir -p "$CLAUDE_DIR/hooks" "$CLAUDE_DIR/hooks/chronicler"
for f in "$HARNESS_DIR"/hooks/*; do
  [ -f "$f" ] || continue
  backup_and_link "$f" "$CLAUDE_DIR/hooks/$(basename "$f")"
done
for f in "$HARNESS_DIR"/hooks/chronicler/*; do
  [ -f "$f" ] || continue
  backup_and_link "$f" "$CLAUDE_DIR/hooks/chronicler/$(basename "$f")"
done

# --- Graphs ---
# These go into the Source project's .claude/docs/, not ~/.claude/
echo "=== Skill Graphs ==="
mkdir -p "$SOURCE_CLAUDE/docs/swift-graph" "$SOURCE_CLAUDE/docs/agent-infra-graph"
for f in "$HARNESS_DIR"/graphs/swift-graph/*; do
  [ -f "$f" ] || continue
  backup_and_link "$f" "$SOURCE_CLAUDE/docs/swift-graph/$(basename "$f")"
done
for f in "$HARNESS_DIR"/graphs/agent-infra-graph/*; do
  [ -f "$f" ] || continue
  backup_and_link "$f" "$SOURCE_CLAUDE/docs/agent-infra-graph/$(basename "$f")"
done

echo ""
echo "Done. $(find "$HARNESS_DIR" -type f | wc -l | tr -d ' ') files linked."
echo "Note: release.md is managed by shihwesley-plugins (not included here)."
