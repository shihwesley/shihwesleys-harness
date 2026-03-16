# LLDB Debugging via XcodeBuildMCP

Use LLDB when logs alone can't answer the question — typically when you need to inspect specific variable values at a specific execution point.

## When to Use

- Bug involves incorrect state that isn't logged
- Need to inspect RealityKit entity transforms, components, or hierarchy
- Need to check values at a specific point in an async flow
- Logs show the symptom but not the cause

## Flow

```
1. build_run_sim          → launch the app
2. debug_attach_sim       → attach to running process (needs bundleId)
3. debug_breakpoint_add   → set breakpoint at suspect line (file:line or symbol)
4. [trigger the bug in the app]
5. debug_stack            → see where you are (backtrace)
6. debug_variables        → inspect frame-local variables
7. debug_lldb_command     → arbitrary expressions (po, expr, etc.)
8. debug_continue         → resume execution
9. debug_detach           → clean disconnect when done
```

## Common Expressions

```
# Print an object
po myVariable

# Evaluate an expression
expr myEntity.position

# Check a boolean condition
expr (bool)(myValue > threshold)

# Print view hierarchy (UIKit)
expr -l objc -- (void)[CATransaction flush]
po [UIWindow.keyWindow recursiveDescription]

# Check RealityKit entity
po entity.components
po entity.transform.matrix
```

## Tips

- Set breakpoints BEFORE triggering the bug, not after
- `debug_variables` shows only the current frame — use `debug_stack` first to confirm you're in the right frame
- For async code, breakpoints in continuations may not hit where expected — set them in the synchronous entry point and step through
- Detach cleanly (`debug_detach`) when done — leaving LLDB attached can cause hangs on next build

## Token Cost

LLDB inspection is cheap (100–300 tokens per call). Prefer multiple targeted `debug_variables` calls over a single `screenshot` when investigating state.
