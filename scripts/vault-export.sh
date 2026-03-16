#!/usr/bin/env bash
# Export Claude auto-memory insights to Obsidian vault as individual notes
# Usage: bash vault-export.sh [--dry-run]
#
# Reads from Claude's auto-memory and mind search results,
# creates properly tagged Obsidian notes in the vault.

set -euo pipefail

VAULT="$HOME/claude/Second Brain"
MEMORY_DIR="$HOME/Source/.claude/projects/-Users-quartershots-Source/memory"
EXPORT_DIR="$VAULT/References/Claude Learnings"
DRY_RUN="${1:-}"
TODAY=$(date +%Y-%m-%d)

mkdir -p "$EXPORT_DIR"

# Track what we've already exported
EXPORTED_LOG="$EXPORT_DIR/.exported"
touch "$EXPORTED_LOG"

export_learning() {
  local title="$1"
  local content="$2"
  local tags="$3"
  local filename="$EXPORT_DIR/$title.md"

  # Skip if already exported
  if grep -qF "$title" "$EXPORTED_LOG" 2>/dev/null; then
    echo "  skip: $title (already exported)"
    return
  fi

  if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "  would create: $filename"
    return
  fi

  cat > "$filename" << EOF
---
date: "$TODAY"
tags:
  - learnings/claude
  - $tags
source: "claude-code-export"
---

# $title

$content
EOF

  echo "$title" >> "$EXPORTED_LOG"
  echo "  created: $filename"
}

echo "Scanning auto-memory files..."

# Export from any .md files in memory dir (except MEMORY.md header)
for f in "$MEMORY_DIR"/*.md; do
  [ -f "$f" ] || continue
  basename_f=$(basename "$f")
  echo "Processing: $basename_f"

  # Extract learned entries (lines starting with > **Learned:**)
  while IFS= read -r line; do
    # Strip the > **Learned:** prefix
    learning=$(echo "$line" | sed 's/^> \*\*Learned:\*\* //')
    # Create a title from first 50 chars
    title=$(echo "$learning" | cut -c1-50 | tr '/' '-' | tr ':' '-' | sed 's/[[:space:]]*$//')
    export_learning "$title" "$learning" "learnings/auto-memory"
  done < <(grep '^> \*\*Learned:\*\*' "$f" 2>/dev/null || true)
done

echo ""
echo "Export complete. Notes in: $EXPORT_DIR"
echo "Exported log: $EXPORTED_LOG"
