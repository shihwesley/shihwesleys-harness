# Observation Tool Token Costs

Reference for choosing the right observation method during debugging.

## Cost Table

### XcodeBuildMCP Tools

| Tool | Typical tokens | When to use | Returns |
|------|---------------|-------------|---------|
| `snapshot_ui` | 200–400 | Layout, hierarchy, missing elements | Structured text: view tree with types, frames |
| `stop_sim_log_cap` | 100–2,000 | Runtime behavior, crashes, state changes | Console text: os_log, print(), NSLog |
| LLDB `debug_variables` | 100–300 | Specific variable values at breakpoint | Frame-local variable names and values |
| LLDB `debug_stack` | 100–200 | Call stack at breakpoint | Backtrace with file:line references |
| `screenshot` | ~1,500 | Visual-only bugs: color, rendering, animation | Base64-encoded PNG image |

### AXe CLI Tools

| Tool | Typical tokens | When to use | Returns |
|------|---------------|-------------|---------|
| `axe describe-ui` | 200–600 | Full accessibility tree, element discovery | Text: accessibility IDs, labels, frames, traits |
| `axe describe-ui --point` | 50–150 | What's at specific coordinates | Text: element at that point |
| `axe batch` (execution) | ~50 | Scripted reproduction of bug | Success/failure per step |
| `axe screenshot` | ~1,500 | Visual capture (same cost as MCP) | PNG file on disk (not inline) |
| `axe record-video` | ~50 | Record bug behavior for user review | MP4 file on disk |

### When to Use Which

| Need | Best tool | Why |
|------|-----------|-----|
| View hierarchy structure | `snapshot_ui` | Gives SwiftUI view types and frames |
| Accessibility IDs for tapping | `axe describe-ui` | Shows IDs you can pass to `axe tap --id` |
| Both at once | Run both — they complement | ~400-1000 tokens total, full picture |
| Interact with the UI | `axe tap`/`axe batch` | Only AXe can tap, swipe, type |
| Repeatable reproduction | `axe batch` script | Scripted, deterministic, reusable |

## Why This Matters

Over 10 debug cycles:

| Strategy | Observation cost | Reasoning overhead | Total |
|----------|-----------------|-------------------|-------|
| Screenshot-driven | ~15,000 tokens | High (visual pattern matching) | ~25k+ |
| Text-first (logs + UI snapshot) | ~3,000 tokens | Low (structured data) | ~8k |

Text-first observation gives ~3x more debug cycles before context pressure.

## Decision Flow

```
Is the bug about how something LOOKS (color, animation, rendering)?
  → YES: screenshot (but max 2 per cycle)
  → NO: Is it about LAYOUT or HIERARCHY (position, size, missing views)?
    → YES: snapshot_ui
    → NO: Is it about BEHAVIOR or STATE (wrong data, crash, logic error)?
      → YES: start_sim_log_cap → trigger → stop_sim_log_cap
      → NO: Is it about a SPECIFIC VALUE at a specific moment?
        → YES: LLDB (attach → breakpoint → debug_variables)
        → NO: Start with logs, narrow from there
```

## Screenshot Budget

Max 2 screenshots per debug cycle. If you need more visual information, describe what you're looking for and use `snapshot_ui` to check hierarchy first.
