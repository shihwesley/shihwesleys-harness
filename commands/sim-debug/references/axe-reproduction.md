# AXe Reproduction Scripts

Write repeatable bug reproduction scripts using `axe batch`. This makes every test cycle identical — no variance from manual interaction.

## Why This Matters

Without a reproduction script, each debug cycle involves different timing, different tap locations, different sequence. A bug that appears "sometimes" might be a reproduction problem, not a real intermittent. Scripted reproduction eliminates that variable.

## Writing a Reproduction Script

### Step 1: Discover the UI

```bash
axe describe-ui --udid <UDID>
```

This prints the full accessibility tree. Look for `AXUniqueId` and `AXLabel` values you can use as tap targets.

### Step 2: Write the Batch

```bash
axe batch --udid <UDID> \
  --step "tap --id 'MenuButton'" \
  --step "sleep 0.5" \
  --step "tap --label 'Settings'" \
  --step "sleep 0.3" \
  --step "gesture scroll-down" \
  --step "sleep 0.2" \
  --step "tap --id 'ProblematicToggle'"
```

**Prefer `--id` over `--label` over coordinates.** IDs are stable across runs.

### Step 3: Save as Shell Script

Save to `.claude/cache/debug-repro.sh` so it persists across sessions:

```bash
#!/bin/bash
# Reproduction script for: [bug description]
# Created: [date]
UDID="${1:?Usage: debug-repro.sh <UDID>}"

axe batch --udid "$UDID" \
  --step "tap --id 'MenuButton'" \
  --step "sleep 0.5" \
  --step "tap --label 'Settings'" \
  --step "sleep 0.3" \
  --step "gesture scroll-down"
```

Make executable: `chmod +x .claude/cache/debug-repro.sh`

### Step 4: Use in Every Test Cycle

After each code change → build → run → execute repro script → capture evidence.

## Timing

- Use `sleep` steps between actions that trigger animations or navigation
- Use `--wait-timeout` on selector taps to wait for elements to appear (better than sleep)
- Use `--pre-delay` / `--post-delay` on individual taps for fine timing
- Start with generous sleeps (0.5s), tighten later if needed

## Batch Flags

| Flag | Purpose |
|------|---------|
| `--continue-on-error` | Don't stop on first failure (useful for exploratory runs) |
| `--wait-timeout <sec>` | Wait for element to appear before tapping (selector taps only) |
| `--poll-interval <sec>` | How often to check for element during wait (default 0.25s) |
| `--ax-cache perStep` | Refresh accessibility tree per step (slower but handles changing UI) |
| `--verbose` | Print step details (debugging the reproduction script itself) |

## Recording the Bug

Capture video of the reproduction for the user to review:

```bash
# Start recording in background
axe record-video --udid <UDID> --fps 15 --output .claude/cache/bug-recording.mp4 &
RECORD_PID=$!

# Run reproduction
bash .claude/cache/debug-repro.sh <UDID>

# Wait a moment for the bug to manifest, then stop
sleep 2
kill $RECORD_PID
```

The MP4 file can be shared with the user for visual confirmation.

## Point Inspection

If `describe-ui` shows the element exists but tapping it doesn't work, inspect a specific point:

```bash
axe describe-ui --point 200,400 --udid <UDID>
```

This shows exactly what's at those coordinates — useful for debugging tap targets that don't respond.
