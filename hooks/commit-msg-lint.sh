#!/bin/bash
# Conventional Commits validation — works as both:
#   1. Git commit-msg hook (receives temp file path as $1)
#   2. Standalone validator (pipe message via stdin or pass as $1 string)
#
# Install in any repo: /install-commit-hook (see below)
# Or manually: ln -sf ~/.claude/hooks/commit-msg-lint.sh .git/hooks/commit-msg

set -euo pipefail

# Get the commit message
if [ -f "${1:-}" ]; then
    # Git hook mode: $1 is a file path
    FIRST_LINE=$(head -1 "$1")
else
    # Direct mode: $1 is the message string
    FIRST_LINE=$(echo "${1:-}" | head -1)
fi

# Skip empty
[ -z "$FIRST_LINE" ] && exit 0

# Skip merge commits
echo "$FIRST_LINE" | /usr/bin/grep -qE '^Merge ' && exit 0

# Skip revert commits
echo "$FIRST_LINE" | /usr/bin/grep -qE '^Revert ' && exit 0

# Validate: <type>[optional scope][!]: <description>
# Use /usr/bin/grep to avoid rg alias which doesn't support -E
TYPES="feat|fix|refactor|perf|test|docs|chore|ci|style|build|revert"
PATTERN="^($TYPES)(\([a-zA-Z0-9_. -]+\))?!?: .+"

if ! echo "$FIRST_LINE" | /usr/bin/grep -qE "$PATTERN"; then
    echo ""
    echo "  Commit message rejected — not Conventional Commits format."
    echo ""
    echo "  Expected: <type>[scope]: <description>"
    echo ""
    echo "  Types: feat fix refactor perf test docs chore ci style build"
    echo ""
    echo "  Got: $FIRST_LINE"
    echo ""
    echo "  Examples:"
    echo "    feat: add Phase 0 knowledge store search"
    echo "    fix(search): handle empty BM25 query"
    echo "    feat!: rewrite search API"
    echo "    chore(deps): bump memvid-sdk to 2.1.0"
    echo ""
    exit 1
fi

# Validate description length (≤72 chars for first line, git convention)
DESC_LEN=${#FIRST_LINE}
if [ "$DESC_LEN" -gt 72 ]; then
    echo ""
    echo "  Commit subject too long ($DESC_LEN chars). Keep under 72."
    echo "  Use the commit body for details."
    echo ""
    echo "  Got: $FIRST_LINE"
    echo ""
    exit 1
fi

exit 0
