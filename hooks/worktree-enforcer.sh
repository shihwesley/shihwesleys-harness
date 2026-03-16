#!/bin/bash
# Worktree Enforcer Hook
# Blocks multi-file edits on main/master branch
# Tracks files via state file, blocks at 3+ files

set -e

# Get file being edited from Claude's tool input
FILE_PATH="${CLAUDE_FILE_PATH:-}"
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"

# Skip if no file path (shouldn't happen for Edit/Write)
[[ -z "$FILE_PATH" ]] && exit 0

# Skip non-git directories
git rev-parse --git-dir &>/dev/null || exit 0

# Get current branch
BRANCH=$(git branch --show-current 2>/dev/null || echo "")

# Skip if not on main/master
[[ "$BRANCH" != "main" && "$BRANCH" != "master" ]] && exit 0

# Allowed file patterns (exceptions)
ALLOWED_PATTERNS=(
    "CLAUDE.md"
    "README.md"
    ".claude/*"
    "*.json"  # Config files
    "*.yaml"
    "*.yml"
    "*.toml"
    ".gitignore"
    ".env*"
)

# Check if file matches allowed patterns
for pattern in "${ALLOWED_PATTERNS[@]}"; do
    if [[ "$FILE_PATH" == *$pattern ]]; then
        exit 0  # Allowed, don't track or block
    fi
done

# State file to track edited files this session
STATE_DIR="/tmp/claude-worktree-state"
mkdir -p "$STATE_DIR"

# Use git root as unique identifier
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null | md5 | cut -c1-8)
STATE_FILE="$STATE_DIR/$GIT_ROOT-files.txt"

# Clean state if older than 2 hours (new session)
if [[ -f "$STATE_FILE" ]]; then
    FILE_AGE=$(( $(date +%s) - $(stat -f %m "$STATE_FILE" 2>/dev/null || echo 0) ))
    if [[ $FILE_AGE -gt 7200 ]]; then
        rm -f "$STATE_FILE"
    fi
fi

# Add current file to tracked list (unique)
touch "$STATE_FILE"
if ! grep -qxF "$FILE_PATH" "$STATE_FILE" 2>/dev/null; then
    echo "$FILE_PATH" >> "$STATE_FILE"
fi

# Count unique files edited
FILE_COUNT=$(wc -l < "$STATE_FILE" | tr -d ' ')

# Block at 3+ files
if [[ $FILE_COUNT -ge 3 ]]; then
    FILES_LIST=$(cat "$STATE_FILE" | head -5)

    cat <<EOF
BLOCKED: Multi-file edit on $BRANCH branch detected.

You've edited $FILE_COUNT files on '$BRANCH':
$FILES_LIST

REQUIRED ACTION:
1. Create a worktree for this work:
   git worktree add ../<project>-<feature> -b feature/<name>

2. Move to that worktree and continue there

3. To reset this check (after creating worktree):
   rm $STATE_FILE

See CLAUDE.md "Worktree Enforcement" section.
EOF
    exit 1
fi

# Warn at 2 files
if [[ $FILE_COUNT -eq 2 ]]; then
    echo "WARNING: 2 files edited on '$BRANCH'. Next edit will be blocked. Consider creating a worktree."
fi

exit 0
