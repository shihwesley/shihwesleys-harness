# Debug State File Format

Location: `.claude/cache/debug-state.md`

This file persists across context resets. It is the single source of truth for debugging progress. A fresh session reading this file should be able to continue without re-observing (unless code changed).

## Template

```markdown
# Debug: [short bug title]
Started: [YYYY-MM-DD]
Status: active | resolved | blocked | escalated

## Symptoms
<!-- Observable behavior only. No guesses. Exact error messages, log lines, UI state. -->

## Environment
- Project: [name]
- Scheme: [scheme]
- Simulator: [device name]
- OS: [simulator OS version]
- Key files: [list of files relevant to this bug]

## Hypotheses

### H1: [description]
- **Status:** testing | confirmed | eliminated | inconclusive
- **Test:** [exact steps taken to test — what log was added, what breakpoint, what change]
- **Evidence:** [exact output — log line, variable value, UI state]
- **Conclusion:** [what this proves or disproves]

### H2: [description]
- **Status:** ...
- **Test:** ...
- **Evidence:** ...
- **Conclusion:** ...

## Changes Made
<!-- Only changes that are part of the fix, not debug logging -->
- [file:line] — [what changed and why]

## Dead Ends — DO NOT RETRY
<!-- Approaches that were tested and definitively failed -->
- [approach] — [why it failed] — [evidence]

## Current State
<!-- What is true RIGHT NOW — last known good behavior, current broken behavior -->

## Next Steps
<!-- Ordered. What to try next, with specific actions. -->
1. ...
2. ...
```

## Rules

1. **Write symptoms before hypotheses.** Observation precedes theory.
2. **Write hypotheses before changes.** Theory precedes action.
3. **Record evidence verbatim.** Copy log lines and values, don't paraphrase.
4. **Dead Ends are sacred.** Never retry something listed there without new evidence that changes the premise.
5. **Update after every cycle.** If you tested something, record it immediately.
6. **Keep "Current State" current.** A resuming session reads this first.
