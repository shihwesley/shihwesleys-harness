#!/bin/bash
# Swift Skill Graph Validator
# Checks link validity, coverage, and staleness
# Run: bash .claude/scripts/swift-graph-validate.sh
# Exit codes: 0 = healthy, 1 = issues found

set -euo pipefail

GRAPH_DIR="/Users/quartershots/Source/.claude/docs/swift-graph"
COMMANDS_DIR="/Users/quartershots/Source/.claude/commands"
IOS_DOCS_DIR="/Users/quartershots/Source/.claude/docs/ios-development"
VISIONOS_DOCS_DIR="/Users/quartershots/Source/.claude/docs/visionos-development"
AGENTS_DIR="/Users/quartershots/Source/.claude/agents"

ISSUES=0
WARNINGS=0

echo "=== Swift Skill Graph Validation ==="
echo ""

# Helper: extract `.claude/...` file paths from → references in a file
extract_refs() {
  # Pattern: → `.claude/path/to/file.md`
  grep -o '→ `\.claude/[^`]*`' "$1" 2>/dev/null | sed 's/→ `//;s/`//' || true
}

# Helper: extract [[cross-refs]] from a file
extract_xrefs() {
  grep -o '\[\[[a-z0-9-]*\.md\]\]' "$1" 2>/dev/null | sed 's/\[\[//;s/\]\]//' || true
}

# --- 1. Check all file references in MOCs resolve to real files ---
echo "## Link Validity"

for moc in "$GRAPH_DIR"/*.md; do
  moc_name=$(basename "$moc")
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    full_path="/Users/quartershots/Source/$path"
    if [[ ! -f "$full_path" ]]; then
      echo "  BROKEN: $moc_name → $path (file not found)"
      ISSUES=$((ISSUES + 1))
    fi
  done <<< "$(extract_refs "$moc")"
done

if [[ $ISSUES -eq 0 ]]; then
  echo "  All file references valid."
fi
echo ""

# --- 2. Check coverage — are all iOS/visionOS skill/doc files in the graph? ---
echo "## Coverage"

# Build set of all file paths referenced in the graph
ALL_REFS=""
for moc in "$GRAPH_DIR"/*.md; do
  ALL_REFS+="$(extract_refs "$moc")"$'\n'
done
ALL_REFS=$(echo "$ALL_REFS" | sort -u)

# Check command skills (iOS/visionOS related)
for cmd in ios-architecture-guide ios26-swiftui on-device-ai app-store-submit asc-automation realitykit-ecs visionos-spatial xcode-terminal; do
  ref=".claude/commands/$cmd.md"
  if ! echo "$ALL_REFS" | grep -qF "$ref"; then
    echo "  MISSING: $ref not referenced in any MOC"
    WARNINGS=$((WARNINGS + 1))
  fi
done

# Check iOS docs
if [[ -d "$IOS_DOCS_DIR" ]]; then
  for doc in "$IOS_DOCS_DIR"/*.md; do
    doc_name=$(basename "$doc")
    [[ "$doc_name" == "sources.md" ]] && continue
    ref=".claude/docs/ios-development/$doc_name"
    if ! echo "$ALL_REFS" | grep -qF "$ref"; then
      echo "  MISSING: $ref not referenced in any MOC"
      WARNINGS=$((WARNINGS + 1))
    fi
  done
fi

# Check visionOS docs
if [[ -d "$VISIONOS_DOCS_DIR" ]]; then
  for doc in "$VISIONOS_DOCS_DIR"/*.md; do
    doc_name=$(basename "$doc")
    [[ "$doc_name" == "sources.md" ]] && continue
    ref=".claude/docs/visionos-development/$doc_name"
    if ! echo "$ALL_REFS" | grep -qF "$ref"; then
      echo "  MISSING: $ref not referenced in any MOC"
      WARNINGS=$((WARNINGS + 1))
    fi
  done
fi

# Check agents
for agent in ios-specialist visionos-specialist; do
  ref=".claude/agents/$agent.md"
  if ! echo "$ALL_REFS" | grep -qF "$ref"; then
    echo "  MISSING: $ref not referenced in any MOC"
    WARNINGS=$((WARNINGS + 1))
  fi
done

if [[ $WARNINGS -eq 0 ]]; then
  echo "  All iOS/visionOS files covered."
fi
echo ""

# --- 3. Staleness — are linked files newer than their MOC? ---
echo "## Staleness"

STALE=0
for moc in "$GRAPH_DIR"/*.md; do
  moc_name=$(basename "$moc")
  [[ "$moc_name" == "traverse.md" ]] && continue
  [[ "$moc_name" == "index.md" ]] && continue

  moc_mtime=$(stat -f %m "$moc" 2>/dev/null || stat -c %Y "$moc" 2>/dev/null)

  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    full_path="/Users/quartershots/Source/$path"
    if [[ -f "$full_path" ]]; then
      file_mtime=$(stat -f %m "$full_path" 2>/dev/null || stat -c %Y "$full_path" 2>/dev/null)
      if [[ "$file_mtime" -gt "$moc_mtime" ]]; then
        echo "  STALE: $moc_name — linked file $path is newer"
        STALE=$((STALE + 1))
      fi
    fi
  done <<< "$(extract_refs "$moc")"
done

if [[ $STALE -eq 0 ]]; then
  echo "  All MOCs up to date."
fi
echo ""

# --- 4. Cross-reference validation — do [[links]] point to real MOCs? ---
echo "## Cross-References"

XREF_ISSUES=0
for moc in "$GRAPH_DIR"/*.md; do
  moc_name=$(basename "$moc")
  while IFS= read -r xref; do
    [[ -z "$xref" ]] && continue
    if [[ ! -f "$GRAPH_DIR/$xref" ]]; then
      echo "  BROKEN: $moc_name links to [[$xref]] but file doesn't exist"
      XREF_ISSUES=$((XREF_ISSUES + 1))
    fi
  done <<< "$(extract_xrefs "$moc")"
done

if [[ $XREF_ISSUES -eq 0 ]]; then
  echo "  All cross-references valid."
fi
echo ""

# --- Summary ---
TOTAL=$((ISSUES + WARNINGS + STALE + XREF_ISSUES))
echo "=== Summary ==="
echo "  Broken links:     $ISSUES"
echo "  Missing coverage: $WARNINGS"
echo "  Stale MOCs:       $STALE"
echo "  Broken xrefs:     $XREF_ISSUES"

if [[ $TOTAL -eq 0 ]]; then
  echo "  Status: HEALTHY"
  exit 0
else
  echo "  Status: $TOTAL issue(s) found"
  exit 1
fi
