#!/bin/bash
# Context7 Doc Cacher - Auto-caches library docs after Context7 fetches
# Saves tokens on future reads via TLDR hook
# Location: /Users/quartershots/Source/.claude/hooks/context7-doc-cacher.sh

set -euo pipefail

CLAUDE_DIR="/Users/quartershots/Source/.claude"
DOCS_DIR="$CLAUDE_DIR/docs"

# Read hook input
INPUT=$(cat)

# Only process Context7 tool calls
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')
[[ "$TOOL_NAME" != *"context7"* ]] && [[ "$TOOL_NAME" != *"get_library_docs"* ]] && exit 0

# Extract library name and content from result
LIBRARY=$(echo "$INPUT" | jq -r '.tool_input.libraryName // .tool_input.library // ""' | tr '/' '-')
TOPIC=$(echo "$INPUT" | jq -r '.tool_input.topic // "general"' | tr '/' '-' | tr ' ' '-')
CONTENT=$(echo "$INPUT" | jq -r '.tool_result.content // .tool_result // ""')

# Skip if no library name or content
[[ -z "$LIBRARY" ]] && exit 0
[[ -z "$CONTENT" ]] || [[ "$CONTENT" == "null" ]] && exit 0

# Create docs directory
LIBRARY_DIR="$DOCS_DIR/$LIBRARY"
mkdir -p "$LIBRARY_DIR"

# Save doc with timestamp
DOC_FILE="$LIBRARY_DIR/${TOPIC}.md"
cat > "$DOC_FILE" << EOF
<!-- Cached: $(date -Iseconds) | Source: Context7 -->
# $LIBRARY - $TOPIC

$CONTENT
EOF

echo "Cached: $DOC_FILE" >&2
exit 0
