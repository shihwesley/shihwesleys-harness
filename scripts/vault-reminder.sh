#!/usr/bin/env bash
# Session-start reminder: reads pending tasks from Obsidian vault
# Works with Obsidian Tasks plugin syntax (due dates, priorities, etc.)

set -euo pipefail

VAULT="$HOME/claude/Second Brain"
ACTION_ITEMS="$VAULT/Polaris/Action Items.md"
TODAY=$(date +%Y-%m-%d)
DAILY_NOTE="$VAULT/Daily/$TODAY.md"

echo "### Vault Reminders"
echo ""

# Pending action items (exclude completed [x] and code blocks)
if [ -f "$ACTION_ITEMS" ]; then
  PENDING=$(grep -c '^- \[ \]' "$ACTION_ITEMS" 2>/dev/null || echo "0")
  if [ "$PENDING" -gt 0 ]; then
    echo "**Action Items:** $PENDING pending"
    grep '^- \[ \]' "$ACTION_ITEMS" | head -5
    if [ "$PENDING" -gt 5 ]; then
      echo "  ...and $((PENDING - 5)) more"
    fi
    echo ""
  fi
fi

# Overdue tasks (vault-wide, tasks with past due dates)
OVERDUE=$(grep -r "^- \[ \].*📅 " "$VAULT" --include="*.md" 2>/dev/null | grep -v Templates | while IFS= read -r line; do
  due=$(echo "$line" | grep -o '📅 [0-9-]*' | cut -d' ' -f2)
  [ -n "$due" ] && [ "$due" \< "$TODAY" ] && echo "$line"
done || true)
if [ -n "$OVERDUE" ]; then
  echo "**Overdue:**"
  echo "$OVERDUE" | head -5 | sed 's/^.*\.md[:-]/  /'
  echo ""
fi

# Due today (vault-wide)
DUE_TODAY=$(grep -r "^- \[ \].*📅 $TODAY" "$VAULT" --include="*.md" 2>/dev/null | grep -v Templates/ || true)
if [ -n "$DUE_TODAY" ]; then
  echo "**Due today:**"
  echo "$DUE_TODAY" | head -5 | sed 's/^.*\.md[:-]/  /'
  echo ""
fi

# Today's daily note incomplete tasks
if [ -f "$DAILY_NOTE" ]; then
  DAILY_TASKS=$(grep -c '^- \[ \]' "$DAILY_NOTE" 2>/dev/null || echo "0")
  if [ "$DAILY_TASKS" -gt 0 ]; then
    echo "**Today's tasks:**"
    grep '^- \[ \]' "$DAILY_NOTE"
    echo ""
  fi
fi

# Yesterday's carryover
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d 'yesterday' +%Y-%m-%d 2>/dev/null || echo "")
if [ -n "$YESTERDAY" ] && [ -f "$VAULT/Daily/$YESTERDAY.md" ]; then
  YESTERDAY_TASKS=$(grep -c '^- \[ \]' "$VAULT/Daily/$YESTERDAY.md" 2>/dev/null || echo "0")
  if [ "$YESTERDAY_TASKS" -gt 0 ]; then
    echo "**Carried over from yesterday ($YESTERDAY):**"
    grep '^- \[ \]' "$VAULT/Daily/$YESTERDAY.md"
    echo ""
  fi
fi

# Top of Mind
TOP_OF_MIND="$VAULT/Polaris/Top of Mind.md"
if [ -f "$TOP_OF_MIND" ]; then
  echo "**Top of Mind:** $(grep '^- ' "$TOP_OF_MIND" | head -3 | sed 's/^- //' | tr '\n' ' | ')"
  echo ""
fi
