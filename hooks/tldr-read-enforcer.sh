#!/bin/bash
# TLDR Read Enforcer (Merkle-Enhanced)
# Returns AST summaries instead of full files
# Achieves ~95% token savings on repeated file reads
# Integrates with Mercator's merkle manifest for O(1) cache lookups
# Location: /Users/quartershots/Source/.claude/hooks/tldr-read-enforcer.sh

set -euo pipefail

CLAUDE_DIR="/Users/quartershots/Source/.claude"
CACHE_DIR="$CLAUDE_DIR/cache/tldr"
mkdir -p "$CACHE_DIR"

# Read hook input
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Exit early if no file path
[[ -z "$FILE_PATH" ]] && exit 0

# Skip if file doesn't exist
[[ ! -f "$FILE_PATH" ]] && exit 0

# Get file info
FILE_SIZE=$(stat -f%z "$FILE_PATH" 2>/dev/null || stat -c%s "$FILE_PATH" 2>/dev/null || echo 0)
FILE_EXT="${FILE_PATH##*.}"
FILE_NAME=$(basename "$FILE_PATH")

# Determine project root (look for .git, package.json, CLAUDE.md)
find_project_root() {
  local dir="$1"
  while [[ "$dir" != "/" ]]; do
    if [[ -d "$dir/.git" ]] || [[ -f "$dir/package.json" ]] || [[ -f "$dir/CLAUDE.md" ]]; then
      echo "$dir"
      return
    fi
    dir=$(dirname "$dir")
  done
  echo ""
}

PROJECT_ROOT=$(find_project_root "$(dirname "$FILE_PATH")")
MANIFEST_PATH="${PROJECT_ROOT:+$PROJECT_ROOT/docs/.mercator.json}"

# === BYPASS RULES ===

# EXCEPTION: Always TLDR .claude/docs/ files (cached library docs)
IS_CACHED_DOC=false
[[ "$FILE_PATH" == */.claude/docs/* ]] && IS_CACHED_DOC=true

# Small files (< 3KB / ~100 lines) - just read them (unless cached doc)
[[ $FILE_SIZE -lt 3000 ]] && [[ "$IS_CACHED_DOC" == false ]] && exit 0

# Config/data files - need full content (unless cached doc)
if [[ "$IS_CACHED_DOC" == false ]]; then
  case "$FILE_EXT" in
    json|yaml|yml|toml|ini|env|lock|txt|csv) exit 0 ;;
  esac
fi

# Image files - Claude reads these visually, TLDR can't summarize binary content
case "$FILE_EXT" in
  png|jpg|jpeg|gif|bmp|tiff|tif|webp|heic|heif|svg|ico|pdf) exit 0 ;;
esac

# Test files - need implementation details
[[ "$FILE_PATH" == *test* ]] && exit 0
[[ "$FILE_PATH" == *spec* ]] && exit 0
[[ "$FILE_PATH" == *__tests__* ]] && exit 0

# Hook files themselves (but not docs)
[[ "$FILE_PATH" == *.claude/* ]] && [[ "$IS_CACHED_DOC" == false ]] && exit 0

# Line range requests - user knows what they want
OFFSET=$(echo "$INPUT" | jq -r '.tool_input.offset // empty')
[[ -n "$OFFSET" ]] && exit 0

# === MERKLE-ENHANCED CACHE LOOKUP ===
# Try to get hash from mercator manifest first (O(1) lookup vs O(n) file read)

MERKLE_HASH=""
MERKLE_PURPOSE=""
FILE_REL_PATH=""

if [[ -n "$PROJECT_ROOT" ]] && [[ -f "$MANIFEST_PATH" ]]; then
  FILE_REL_PATH="${FILE_PATH#$PROJECT_ROOT/}"

  # Extract hash and any stored purpose from manifest
  MERKLE_INFO=$(jq -r --arg path "$FILE_REL_PATH" '
    .merkle.tree[$path] // empty |
    if . then "\(.hash)|\(.purpose // "")" else "" end
  ' "$MANIFEST_PATH" 2>/dev/null || echo "")

  if [[ -n "$MERKLE_INFO" ]]; then
    MERKLE_HASH="${MERKLE_INFO%%|*}"
    MERKLE_PURPOSE="${MERKLE_INFO#*|}"
  fi
fi

# Use merkle hash if available, otherwise compute MD5
if [[ -n "$MERKLE_HASH" ]]; then
  HASH="$MERKLE_HASH"
  CACHE_SOURCE="merkle"
else
  HASH=$(md5 -q "$FILE_PATH" 2>/dev/null || md5sum "$FILE_PATH" | cut -d' ' -f1)
  HASH="${HASH:0:12}"  # Truncate to match merkle format
  CACHE_SOURCE="md5"
fi

CACHE_FILE="$CACHE_DIR/${HASH}.tldr"

# === CHECK CACHE ===
if [[ -f "$CACHE_FILE" ]]; then
  TLDR_CONTENT=$(cat "$CACHE_FILE")

  # Prepend purpose from mercator if available
  if [[ -n "$MERKLE_PURPOSE" ]]; then
    TLDR_CONTENT="# Purpose: $MERKLE_PURPOSE
$TLDR_CONTENT"
  fi
else
  # === GENERATE TLDR ===
  case "$FILE_EXT" in
    py)
      TLDR_CONTENT=$(python3 << 'PYEOF'
import ast
import sys

file_path = sys.argv[1] if len(sys.argv) > 1 else None
if not file_path:
    sys.exit(1)

try:
    with open(file_path) as f:
        source = f.read()
    tree = ast.parse(source)
except Exception as e:
    print(f"Parse error: {e}")
    sys.exit(1)

def get_annotation(node):
    """Extract type annotation as string"""
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Subscript):
        return ast.unparse(node) if hasattr(ast, 'unparse') else "..."
    if hasattr(ast, 'unparse'):
        return ast.unparse(node)
    return "..."

def format_arg(arg):
    """Format argument with type annotation"""
    if arg.annotation:
        return f"{arg.arg}: {get_annotation(arg.annotation)}"
    return arg.arg

output = []
output.append("# TLDR: AST Summary (L1-L3)")
output.append(f"# File: {file_path}")
output.append(f"# Lines: {len(source.splitlines())}")
output.append("")

# Imports (compressed)
imports = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.extend(a.name for a in node.names)
    elif isinstance(node, ast.ImportFrom):
        imports.append(f"{node.module}.*")
if imports:
    output.append(f"Imports: {', '.join(imports[:10])}")
    output.append("")

# L3: Constants at module level
constants = []
for node in ast.iter_child_nodes(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                val = ast.unparse(node.value) if hasattr(ast, 'unparse') else "..."
                constants.append(f"{target.id} = {val[:50]}")
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.target.id.isupper():
            val = ast.unparse(node.value) if node.value and hasattr(ast, 'unparse') else "..."
            constants.append(f"{node.target.id}: {get_annotation(node.annotation)} = {val[:50]}")
if constants:
    output.append("## Constants")
    for c in constants[:10]:
        output.append(f"  {c}")
    output.append("")

# Classes and functions with L3 detail
for node in ast.iter_child_nodes(tree):
    if isinstance(node, ast.ClassDef):
        bases = [b.id if isinstance(b, ast.Name) else "..." for b in node.bases]
        base_str = f"({', '.join(bases)})" if bases else ""
        doc = ast.get_docstring(node)
        output.append(f"class {node.name}{base_str}:  # line {node.lineno}")
        if doc:
            output.append(f'    """{doc[:80]}{"..." if len(doc) > 80 else ""}"""')

        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                args = [format_arg(a) for a in item.args.args]
                ret = f" -> {get_annotation(item.returns)}" if item.returns else ""
                prefix = "async " if isinstance(item, ast.AsyncFunctionDef) else ""
                output.append(f"    {prefix}def {item.name}({', '.join(args)}){ret}:  # L{item.lineno}")
                # L3: method docstring
                mdoc = ast.get_docstring(item)
                if mdoc:
                    output.append(f'        """{mdoc[:60]}{"..." if len(mdoc) > 60 else ""}"""')
        output.append("")

    elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        args = [format_arg(a) for a in node.args.args]
        ret = f" -> {get_annotation(node.returns)}" if node.returns else ""
        prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        doc = ast.get_docstring(node)
        output.append(f"{prefix}def {node.name}({', '.join(args)}){ret}:  # L{node.lineno}")
        if doc:
            output.append(f'    """{doc[:80]}{"..." if len(doc) > 80 else ""}"""')

print("\n".join(output))
PYEOF
"$FILE_PATH" 2>/dev/null) || TLDR_CONTENT=""
      ;;

    ts|tsx|js|jsx)
      # TypeScript/JavaScript - L3 with full signatures and JSDoc
      TLDR_CONTENT=$(cat << EOF
# TLDR: Structure Summary (L1-L3)
# File: $FILE_PATH
# Lines: $(wc -l < "$FILE_PATH")

## Exports
$(grep -n "^export" "$FILE_PATH" 2>/dev/null | head -20 || echo "None found")

## Classes (with methods)
$(grep -n "^class \|^export class \|^abstract class " "$FILE_PATH" 2>/dev/null | head -10 || echo "None found")
$(grep -n "^  \(public\|private\|protected\|async\|static\)\? *\w\+(" "$FILE_PATH" 2>/dev/null | head -15 || true)

## Functions (full signatures)
$(grep -n "^function \|^export function \|^async function \|^export async function " "$FILE_PATH" 2>/dev/null | head -20 || echo "None found")
$(grep -n "^const \w\+ = \(async \)\?(" "$FILE_PATH" 2>/dev/null | head -15 || true)
$(grep -n "^export const \w\+ = \(async \)\?(" "$FILE_PATH" 2>/dev/null | head -15 || true)

## Types/Interfaces (with fields)
$(grep -n "^type \|^interface \|^export type \|^export interface " "$FILE_PATH" 2>/dev/null | head -15 || echo "None found")
$(grep -n "^  \w\+[?]\?: " "$FILE_PATH" 2>/dev/null | head -20 || true)

## Enums & Constants
$(grep -n "^enum \|^export enum \|^const enum " "$FILE_PATH" 2>/dev/null | head -10 || true)
$(grep -n "^const [A-Z_]\+ = \|^export const [A-Z_]\+ = " "$FILE_PATH" 2>/dev/null | head -10 || true)

## JSDoc hints
$(grep -n "^\s*\* @" "$FILE_PATH" 2>/dev/null | head -10 || true)
EOF
)
      ;;

    swift)
      # Swift - L3 with full signatures, properties, and enum cases
      TLDR_CONTENT=$(cat << EOF
# TLDR: Structure Summary (L1-L3)
# File: $FILE_PATH
# Lines: $(wc -l < "$FILE_PATH")

## Imports
$(grep -n "^import " "$FILE_PATH" 2>/dev/null | head -10 || echo "None")

## Structs/Classes/Enums/Protocols
$(grep -n "^struct \|^class \|^enum \|^protocol \|^extension \|^actor " "$FILE_PATH" 2>/dev/null | head -15 || echo "None found")

## Properties (with types)
$(grep -n "^\s*\(let\|var\|@\w\+\s\+var\|@\w\+\s\+let\) \w\+:" "$FILE_PATH" 2>/dev/null | head -20 || true)

## Functions (full signatures)
$(grep -n "^\s*\(func\|private func\|public func\|static func\|mutating func\|async func\|@\w\+ func\)" "$FILE_PATH" 2>/dev/null | head -25 || echo "None found")

## Enum cases
$(grep -n "^\s*case \w\+" "$FILE_PATH" 2>/dev/null | head -15 || true)

## Typealiases & Associated Types
$(grep -n "^\s*typealias \|^\s*associatedtype " "$FILE_PATH" 2>/dev/null | head -10 || true)

## Initializers
$(grep -n "^\s*init(" "$FILE_PATH" 2>/dev/null | head -5 || true)
EOF
)
      ;;

    md)
      # Markdown docs - extract TOC, headings, code block hints
      TLDR_CONTENT=$(cat << EOF
# TLDR: Doc Summary (L1-L3)
# File: $FILE_PATH
# Lines: $(wc -l < "$FILE_PATH")

## Table of Contents
$(grep -n "^#" "$FILE_PATH" 2>/dev/null | head -30 || echo "No headings")

## Code Examples (languages)
$(grep -n '```' "$FILE_PATH" 2>/dev/null | head -20 || echo "No code blocks")

## Key Terms
$(grep -n "^\*\*[^*]\+\*\*\|^- \*\*" "$FILE_PATH" 2>/dev/null | head -15 || true)

## Links/References
$(grep -n "\[.*\](http" "$FILE_PATH" 2>/dev/null | head -10 || true)
EOF
)
      ;;

    *)
      # Generic - just show structure
      TLDR_CONTENT=$(cat << EOF
# TLDR: Basic Summary
# File: $FILE_PATH
# Size: $FILE_SIZE bytes
# Lines: $(wc -l < "$FILE_PATH")

## First 5 lines:
$(head -5 "$FILE_PATH")

## Structure hints:
$(grep -n "^class \|^def \|^function \|^export \|^import \|^struct " "$FILE_PATH" 2>/dev/null | head -20 || echo "No structure detected")
EOF
)
      ;;
  esac

  # Cache the result
  if [[ -n "$TLDR_CONTENT" ]]; then
    mkdir -p "$CACHE_DIR"
    echo "$TLDR_CONTENT" > "$CACHE_FILE"
  fi

  # Prepend purpose if available
  if [[ -n "$MERKLE_PURPOSE" ]]; then
    TLDR_CONTENT="# Purpose: $MERKLE_PURPOSE
$TLDR_CONTENT"
  fi
fi

# If TLDR generation failed, allow normal read
[[ -z "$TLDR_CONTENT" ]] && exit 0

# Count tokens saved (rough estimate: 4 chars = 1 token)
ORIG_TOKENS=$((FILE_SIZE / 4))
TLDR_TOKENS=$((${#TLDR_CONTENT} / 4))
if [[ $ORIG_TOKENS -gt 0 ]]; then
  SAVINGS=$(( (ORIG_TOKENS - TLDR_TOKENS) * 100 / ORIG_TOKENS ))
else
  SAVINGS=0
fi

# Build cache info string
CACHE_INFO="cache:$CACHE_SOURCE"
[[ -n "$MERKLE_HASH" ]] && CACHE_INFO="$CACHE_INFO hash:$MERKLE_HASH"

# Return TLDR instead of full file
jq -n \
  --arg content "$TLDR_CONTENT" \
  --arg path "$FILE_PATH" \
  --arg savings "$SAVINGS" \
  --arg orig "$ORIG_TOKENS" \
  --arg tldr "$TLDR_TOKENS" \
  --arg cache "$CACHE_INFO" \
  '{
    "decision": "block",
    "reason": "\($content)\n\n[TLDR: \($savings)% saved (\($tldr)/\($orig) tokens) | \($cache) | Use offset/limit for full content]"
  }'
