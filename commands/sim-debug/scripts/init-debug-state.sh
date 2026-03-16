#!/bin/bash
# Initialize a debug state file for a new debugging session.
# Usage: init-debug-state.sh "bug title" "project name" "scheme" "simulator"

set -euo pipefail

CACHE_DIR=".claude/cache"
STATE_FILE="$CACHE_DIR/debug-state.md"

# Args with defaults
TITLE="${1:-Untitled Bug}"
PROJECT="${2:-Unknown}"
SCHEME="${3:-Unknown}"
SIMULATOR="${4:-Apple Vision Pro}"
DATE=$(date +%Y-%m-%d)

mkdir -p "$CACHE_DIR"

# Don't overwrite existing state
if [ -f "$STATE_FILE" ]; then
  echo "State file already exists at $STATE_FILE"
  echo "To start fresh, delete it first: rm $STATE_FILE"
  exit 1
fi

cat > "$STATE_FILE" << EOF
# Debug: $TITLE
Started: $DATE
Status: active

## Symptoms
<!-- Fill in after Phase 1 observation. Exact error messages, log lines, UI state. -->

## Environment
- Project: $PROJECT
- Scheme: $SCHEME
- Simulator: $SIMULATOR
- OS:
- Key files:

## Hypotheses

## Changes Made

## Dead Ends — DO NOT RETRY

## Current State

## Next Steps
1. Run Phase 1 observation: build, capture logs, capture UI state
EOF

echo "Created $STATE_FILE"
