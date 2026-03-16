#!/bin/bash
# Session start check for worktree usage
# Warns if on main/master with uncommitted changes or active work

# Skip non-git directories
git rev-parse --git-dir &>/dev/null || exit 0

BRANCH=$(git branch --show-current 2>/dev/null || echo "")

# Only warn on main/master
[[ "$BRANCH" != "main" && "$BRANCH" != "master" ]] && exit 0

# Check for uncommitted changes
CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')

# Check for worktrees
WORKTREE_COUNT=$(git worktree list 2>/dev/null | wc -l | tr -d ' ')

# Build warning message
MSG=""

if [[ $CHANGES -gt 0 ]]; then
    MSG="⚠️  On '$BRANCH' with $CHANGES uncommitted changes."
fi

if [[ $WORKTREE_COUNT -gt 1 ]]; then
    WORKTREES=$(git worktree list 2>/dev/null | tail -n +2 | awk '{print "  - " $1 " (" $3 ")"}')
    MSG="$MSG\n📂 Active worktrees:\n$WORKTREES"
fi

if [[ -n "$MSG" ]]; then
    echo -e "$MSG"
    echo ""
    echo "For multi-file work, use: git worktree add ../<name> -b feature/<name>"
fi

exit 0
