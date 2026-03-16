#!/bin/bash
# Install conventional commits hook in the current repo (or all repos under Source/)
#
# Usage:
#   install-commit-hook.sh              # install in current repo
#   install-commit-hook.sh --all        # install in all repos under ~/Source/
#   install-commit-hook.sh /path/to/repo  # install in specific repo

set -euo pipefail

HOOK_SOURCE="/Users/quartershots/Source/.claude/hooks/commit-msg-lint.sh"
INSTALLED=0
SKIPPED=0

install_in_repo() {
    local repo="$1"
    local hooks_dir="$repo/.git/hooks"

    if [ ! -d "$repo/.git" ]; then
        return
    fi

    mkdir -p "$hooks_dir"

    if [ -L "$hooks_dir/commit-msg" ] && [ "$(readlink "$hooks_dir/commit-msg")" = "$HOOK_SOURCE" ]; then
        echo "  skip: $(basename "$repo") (already installed)"
        SKIPPED=$((SKIPPED + 1))
        return
    fi

    if [ -f "$hooks_dir/commit-msg" ]; then
        echo "  warn: $(basename "$repo") has existing commit-msg hook, backing up"
        mv "$hooks_dir/commit-msg" "$hooks_dir/commit-msg.bak"
    fi

    ln -sf "$HOOK_SOURCE" "$hooks_dir/commit-msg"
    echo "  done: $(basename "$repo")"
    INSTALLED=$((INSTALLED + 1))
}

if [ "${1:-}" = "--all" ]; then
    echo "Installing conventional commits hook in all Source/ repos..."
    echo ""
    for dir in /Users/quartershots/Source/*/; do
        install_in_repo "$dir"
    done
    echo ""
    echo "Installed: $INSTALLED  Skipped: $SKIPPED"
elif [ -n "${1:-}" ] && [ -d "$1" ]; then
    install_in_repo "$1"
else
    # Current directory
    if [ -d ".git" ]; then
        install_in_repo "$(pwd)"
    else
        echo "Not a git repository. Run from a repo root or pass a path."
        exit 1
    fi
fi
