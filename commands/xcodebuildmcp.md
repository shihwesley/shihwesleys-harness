---
name: xcodebuildmcp
description: "Use when building, testing, debugging, or interacting with iOS/visionOS simulators via MCP tools instead of raw xcodebuild. Preferred over raw CLI for supported operations."
argument-hint: "[action: build, test, debug, run, log, ui, screenshot]"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# XcodeBuildMCP — MCP-Powered Xcode Operations

MCP server wrapping xcodebuild, simctl, and LLDB into structured tools. Returns parsed errors/warnings instead of raw build logs. Preferred over raw xcodebuild for all supported operations.

## When to Use This vs `/xcode-terminal`

| Use XcodeBuildMCP | Use raw xcodebuild |
|---|---|
| Build, test, run on sim | Archive & export IPA |
| LLDB debugging sessions | xctrace profiling |
| Log capture & inspection | Code signing operations |
| UI automation & screenshots | ExportOptions.plist workflows |
| Session defaults management | CI-specific result bundles |

XcodeBuildMCP doesn't cover archiving, profiling, or export. Fall back to `/xcode-terminal` for those.

## Setup Flow

Call these tools in order when starting a session:

1. `discover_projs` — find .xcodeproj/.xcworkspace
2. `list_sims` — get available simulators (look for "Apple Vision Pro")
3. `boot_sim` — start the target simulator
4. `session_set_defaults` — save scheme + simulator name so you don't repeat them

After defaults are set, most tools inherit them automatically.

## Build & Run

| Tool | When |
|------|------|
| `build_sim` | Compile only, no launch. Use for type-checking or CI-style build verification |
| `build_run_sim` | Build + install + launch. The main "run my app" command |
| `clean` | Remove DerivedData when builds are stale |

All return structured output: errors, warnings, and success/failure status. No xcbeautify needed.

## Testing

| Tool | When |
|------|------|
| `test_sim` | Run XCTest/Swift Testing suite on simulator |

Pass `testPlan`, `onlyTesting`, or `skipTesting` to filter tests. Output includes pass/fail counts and failure messages.

## LLDB Debugging

Attach to a running simulator app, set breakpoints, inspect state:

```
debug_attach_sim  → attach by bundleId (app must be running)
debug_breakpoint_add → file:line or symbol name
debug_continue    → resume after breakpoint hit
debug_stack       → current backtrace
debug_variables   → frame-local variables
debug_lldb_command → arbitrary LLDB expression (po, expr, etc.)
debug_detach      → clean disconnect
```

Typical debug flow:
1. `build_run_sim` — launch the app
2. `debug_attach_sim` — attach LLDB
3. `debug_breakpoint_add` — set breakpoint at suspect code
4. Wait for hit, then `debug_stack` + `debug_variables`
5. `debug_continue` or `debug_detach`

## Log Capture

```
start_sim_log_cap → begin streaming console output
stop_sim_log_cap  → stop and return captured logs
```

Logs include os_log, print(), and NSLog output from the app process. Start capture before triggering the behavior you want to inspect.

## UI Inspection & Automation

| Tool | Purpose |
|------|---------|
| `snapshot_ui` | Full view hierarchy with accessibility IDs and coordinates |
| `screenshot` | PNG capture of current simulator state |
| `tap` | Tap by accessibility ID/label (preferred) or XY coordinates |
| `swipe` | Directional swipe between two points |
| `type_text` | Keyboard text entry |
| `gesture` | Preset gestures (pinch, rotate, etc.) |

For visionOS: prefer accessibility ID-based `tap` over coordinates. The simulator maps gaze+pinch to mouse clicks, so coordinate-based tapping is less reliable for spatial UI.

## Simulator Management

| Tool | Purpose |
|------|---------|
| `list_sims` | All available simulators |
| `boot_sim` | Start a simulator |
| `open_sim` | Open Simulator.app window |
| `set_sim_appearance` | Toggle light/dark mode |
| `erase_sims` | Factory reset a simulator |

## visionOS Notes

- Platform value: `visionOS` (session defaults handle the destination string)
- Simulator name: `Apple Vision Pro`
- All simulator tools work with visionOS — same interface as iOS
- Debug visualizations (collision, anchoring, occlusion) are in Simulator.app UI only — not scriptable
- UI automation works but spatial gesture testing is limited — prefer `snapshot_ui` for layout verification

## MagicCarpet-Specific

If working in the MagicCarpet project, session defaults are pre-configured in `.xcodebuildmcp/config.yaml`:
- Scheme: `MagicCarpet`
- Simulator: `Apple Vision Pro`
- Platform: `visionOS`

Run `xcodegen generate` before first build (XcodeGen project). Signing is handled by config — no need for `CODE_SIGNING_ALLOWED=NO` when using XcodeBuildMCP session defaults.
