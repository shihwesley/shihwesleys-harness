#!/bin/bash
# Orchestrator Status Hook
# Runs on SubagentStop — tracks agent completion during /orchestrate runs
# Updates progress file if orchestration is active

set -e

# Check if orchestration is active (state file exists)
STATE_DIR="/tmp/claude-orchestrate"
STATE_FILE=$(ls -t "$STATE_DIR"/*/state.json 2>/dev/null | head -1)

[[ -z "$STATE_FILE" ]] && exit 0

# Read orchestration state
SESSION_DIR=$(dirname "$STATE_FILE")
PROGRESS_FILE=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('progressFile', ''))" 2>/dev/null)

[[ -z "$PROGRESS_FILE" ]] && exit 0
[[ ! -f "$PROGRESS_FILE" ]] && exit 0

# Get current phase info
CURRENT_PHASE=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('currentPhase', 'unknown'))" 2>/dev/null)
TOTAL_AGENTS=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('totalAgents', 0))" 2>/dev/null)
COMPLETED_AGENTS=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d.get('completedAgents', 0))" 2>/dev/null)

# Increment completed count
NEW_COUNT=$((COMPLETED_AGENTS + 1))
python3 -c "
import json
with open('$STATE_FILE', 'r') as f:
    state = json.load(f)
state['completedAgents'] = $NEW_COUNT
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
" 2>/dev/null

# Report progress
echo "Orchestrator: Phase $CURRENT_PHASE — Agent $NEW_COUNT/$TOTAL_AGENTS completed"

exit 0
