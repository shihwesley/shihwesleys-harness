---
name: mind-backup
description: "Backup and restore claude-brain .mv2 memory files to gist, local archive, or repo. Use when user says /mind-backup, wants to save their memory state, restore from a backup, or migrate memory to a new machine."
user-invocable: true
allowed-tools: ["Bash"]
---

# Mind Backup

Backup and restore your claude-brain memory files.

## Commands

### `/mind-backup` or `/mind-backup local`
Create timestamped local backup:

```bash
MIND_FILE="${HOME}/.claude/mind.mv2"
BACKUP_DIR="${HOME}/.claude/backups/mind"
mkdir -p "$BACKUP_DIR"

if [ -f "$MIND_FILE" ]; then
  TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
  SIZE=$(du -h "$MIND_FILE" | cut -f1)
  cp "$MIND_FILE" "$BACKUP_DIR/mind-${TIMESTAMP}.mv2"
  echo "✓ Backed up mind.mv2 ($SIZE) to $BACKUP_DIR/mind-${TIMESTAMP}.mv2"

  # Keep only last 10 backups
  ls -t "$BACKUP_DIR"/mind-*.mv2 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
  echo "  (keeping last 10 backups)"
else
  echo "No mind.mv2 found at $MIND_FILE"
fi
```

### `/mind-backup gist`
Upload to private GitHub gist:

```bash
MIND_FILE="${HOME}/.claude/mind.mv2"

if [ ! -f "$MIND_FILE" ]; then
  echo "No mind.mv2 found"
  exit 1
fi

# Base64 encode the binary file
ENCODED=$(base64 < "$MIND_FILE")
TIMESTAMP=$(date +%Y-%m-%d)

# Create gist via gh CLI
gh gist create --private \
  -d "Claude Brain Backup - $TIMESTAMP" \
  <(echo "$ENCODED") \
  --filename "mind-${TIMESTAMP}.mv2.b64"
```

### `/mind-backup restore <path-or-gist-url>`
Restore from backup:

```bash
SOURCE="$ARGUMENTS"
MIND_FILE="${HOME}/.claude/mind.mv2"

if [[ "$SOURCE" == https://gist.github.com/* ]]; then
  # Restore from gist
  GIST_ID=$(echo "$SOURCE" | grep -oE '[a-f0-9]{32}')
  CONTENT=$(gh gist view "$GIST_ID" --raw)
  echo "$CONTENT" | base64 -d > "$MIND_FILE"
  echo "✓ Restored from gist"
elif [ -f "$SOURCE" ]; then
  # Restore from local file
  cp "$SOURCE" "$MIND_FILE"
  echo "✓ Restored from $SOURCE"
else
  echo "Source not found: $SOURCE"
  exit 1
fi
```

### `/mind-backup list`
List available backups:

```bash
BACKUP_DIR="${HOME}/.claude/backups/mind"

echo "Local backups:"
ls -lh "$BACKUP_DIR"/mind-*.mv2 2>/dev/null | awk '{print "  " $NF " (" $5 ")"}'

echo ""
echo "Gist backups:"
gh gist list --limit 10 | grep "Claude Brain Backup" || echo "  (none found)"
```

## Auto-Backup Hook

Add to settings.json hooks for automatic backup on session end:

```json
{
  "SessionEnd": [{
    "hooks": [{
      "type": "command",
      "command": "mkdir -p ~/.claude/backups/mind && cp ~/.claude/mind.mv2 ~/.claude/backups/mind/mind-$(date +%Y-%m-%d).mv2 2>/dev/null || true",
      "timeout": 5
    }]
  }]
}
```
