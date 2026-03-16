---
name: hig-audit
description: "Use when checking Apple HIG compliance before App Store submission, during code review, or when SwiftUI code needs accessibility, color, typography, or layout audit."
argument-hint: "[project-path or empty for current directory]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# HIG Audit

Runs hig-doctor against a project's Swift/SwiftUI code, then post-processes results into a deduplicated, scored findings file that a fix agent can consume.

**Target:** "$ARGUMENTS"

## Severity Levels

| Level | Name | Threshold | Action |
|-------|------|-----------|--------|
| P0 | Critical | 90-100 | Must fix. Accessibility blocker, App Store rejection risk. |
| P1 | High | 80-89 | Should fix. Missing Dynamic Type, hardcoded colors without dark mode. |
| P2 | Medium | 70-79 | Fix soon. Minor accessibility gaps, non-standard controls. |
| P3 | Low | <70 | Optional. Style consistency, minor HIG suggestions. Only report if >=60. |

## Workflow

### Phase 1: Run hig-doctor

1. Determine project path (use argument if provided, otherwise current working directory).

2. Run the audit tool with `--json` for structured results:
   ```bash
   bun /Users/quartershots/.claude/plugins/marketplaces/apple-hig-skills/packages/hig-doctor/src-termcast/src/cli.ts <project-path> --json
   ```

3. Parse the JSON output. Extract all findings with their file paths, line numbers, categories, and severity indicators.

4. If the overall score is < 70, also run with `--stdout` to get the full markdown report for additional context:
   ```bash
   bun /Users/quartershots/.claude/plugins/marketplaces/apple-hig-skills/packages/hig-doctor/src-termcast/src/cli.ts <project-path> --stdout
   ```

### Phase 2: Analysis + Context

Launch a **general-purpose** agent (model: `sonnet`) to enrich the raw hig-doctor findings:

1. **Read CLAUDE.md** for project-specific HIG conventions or exceptions.

2. **For each finding from hig-doctor:**
   - Read the referenced source file at the flagged line
   - Verify the finding is accurate (not a false positive from pattern matching)
   - Determine if the code has context that makes it acceptable (e.g., intentional use of hardcoded color for brand)
   - Reference the matching HIG skill for guidance (e.g., hardcoded colors → `hig-foundations`, missing labels → `hig-inputs`)

3. **For each verified finding, produce:**
   - file:line reference
   - Current code verbatim (3-10 lines)
   - Which HIG principle is violated
   - Exact replacement code that fixes it
   - Whether the fix requires other file changes (e.g., adding a Color to asset catalog)

### Phase 3: Scoring + Deduplication

1. **Deduplicate**: hig-doctor may flag the same pattern multiple times across related lines (e.g., 5 hardcoded `Color.red` in the same file). Merge findings that share the same file + same violation type. Keep the most representative instance and note count.

2. **Score each finding** 0-100 for real-world impact:
   ```
   0-25:  Pedantic. Pattern match on code that's actually correct.
   26-50: Minor style issue. Won't affect users or App Store review.
   51-69: Valid HIG gap. Users or reviewers may notice.
   70-79: Real compliance issue. Affects accessibility or appearance.
   80-89: Will affect real users. Missing Dynamic Type, broken dark mode.
   90-100: App Store rejection risk or accessibility barrier.
   ```

3. **Filter**: Drop below 60. Map to P0-P3 per severity table above.

4. **False positive checklist** — filter out:
   - Intentional brand colors documented in CLAUDE.md or asset catalog
   - Custom controls with proper accessibility traits already set
   - Platform-specific code paths (e.g., watchOS code in an iOS audit)
   - Test/preview code that doesn't ship

5. **Write findings file:**

   Create `.orchestrate/` directory if it doesn't exist. Write findings to `.orchestrate/hig-audit.md` following the format in `.claude/skills/review-output-format.md`.

   **Each finding MUST include:**
   - `**ID:**` with severity-numbered tag (P1-1, P2-3, etc.)
   - `**File:**` with exact path and line number(s)
   - `**Source:**` hig-doctor category (Accessibility, Color, Typography, etc.)
   - `**Current code:**` verbatim from the source file (3-10 lines, fenced code block)
   - `**Problem:**` which HIG principle is violated and what the user impact is
   - `**Fix — Option A (recommended):**` exact replacement code in fenced block
   - `**Fix — Option B:**` alternative (or "Do nothing" with consequences)
   - `**Verification:**` how to confirm (visual check, VoiceOver test, dark mode toggle, etc.)

   The file starts with a summary header (review type, date, hig-doctor score, severity counts, verdict). Include a deduplication log at the end showing which findings were merged.

### Phase 4: Output

Display in terminal:

```markdown
### HIG Audit

**Score**: XX/100
**Reviewed**: X Swift files
**Assessment**: [EXCELLENT / GOOD / NEEDS_WORK / POOR]

---

**P0 - Critical** (X found)
1. **[Brief title]** — [Category]
   [Description with file:line]
   [HIG principle violated]

**P1 - High** (X found)
...

**P2 - Medium** (X found)
...

---

**Strengths**
- [What's well done — cite specific patterns]

Generated with [Claude Code](https://claude.ai/code) | HIG Audit v1.1
```

Then show:

```markdown
## Next Steps

Found X issues (P0: _, P1: _, P2: _, P3: _).
Findings written to: `.orchestrate/hig-audit.md`

**How would you like to proceed?**
1. Deploy fix agent (reads findings file, applies all fixes)
2. Deploy fix agent for P0/P1 only
3. Fix specific items (list IDs, e.g. P1-1, P2-3)
4. No changes — audit only
```

**IMPORTANT**: Do NOT implement fixes until user explicitly confirms.

## Score Interpretation

| Score | Meaning |
|-------|---------|
| 90-100 | Excellent — strong HIG compliance |
| 70-89 | Good — solid foundation, room for improvement |
| 50-69 | Needs work — several HIG areas need attention |
| 0-49 | Poor — significant HIG violations |

## What hig-doctor Checks

- **Accessibility:** Missing labels, VoiceOver hints, accessibility traits, Reduce Motion
- **Color:** Hardcoded colors vs semantic, dark mode support
- **Typography:** Fixed font sizes vs Dynamic Type
- **Controls:** Standard vs custom, proper button styles
- **Layout:** Safe areas, navigation patterns
- **Haptics/Audio:** Feedback patterns
- **Technologies:** WidgetKit, HealthKit, ARKit, Apple Pay, Sign in with Apple patterns
