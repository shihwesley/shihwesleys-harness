---
name: test-review
description: "Use when auditing test suite quality, strengthening tests before release, or checking for coverage gaps, weak assertions, and untested failure modes."
argument-hint: "[PR number or 'local' for unstaged changes]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# Test Review

Specialized review of test quality — not whether tests pass, but whether they're good enough to catch real bugs. Evaluates coverage completeness, assertion precision, edge case thoroughness, and failure mode testing.

**Target:** "$ARGUMENTS"

## Severity Levels

| Level | Name | Threshold | Action |
|-------|------|-----------|--------|
| P0 | Critical | 90-100 | Must fix. Core functionality untested, or tests would pass even with broken code. |
| P1 | High | 80-89 | Should fix. Important failure mode untested, weak assertions on critical path. |
| P2 | Medium | 70-79 | Fix in PR or follow-up. Missing edge case, test isolation issue. |
| P3 | Low | <70 | Optional. Test readability, minor coverage gap on non-critical code. Only report if >=60. |

## Workflow

### Phase 1: Gather Context

Launch a **general-purpose** agent (model: `sonnet`) to:

1. **Determine review target:**
   - PR number → `gh pr diff <number>` to get the full diff
   - `local` or empty → `git diff` for unstaged + `git diff --cached` for staged
   - Branch name → `git diff main...<branch>`

2. **Separate test files from implementation files:**
   - Test files: `*_test.*`, `*.test.*`, `*.spec.*`, `*Tests.*`, files in `tests/`, `__tests__/`, `*Tests/` directories
   - Implementation files: everything else in the diff
   - If NO test files in the diff, that itself is a P0 finding

3. **Gather project test conventions:**
   - Read CLAUDE.md for testing preferences
   - Detect test framework from imports/config (Jest, Vitest, pytest, Swift Testing, XCTest, etc.)
   - Find existing test patterns: `Glob("**/*.test.*")` or `Glob("**/*Tests.swift")` — sample 2-3 existing test files to understand project style

4. **Return:** Implementation diff, test diff, framework detected, project conventions, file counts.

### Phase 2: Deep Analysis (Parallel Agents)

Launch **3 parallel general-purpose agents** (model: `sonnet`), each receiving the full diff, test diff, and project conventions.

**IMPORTANT:** Use `subagent_type: "general-purpose"`. Do NOT use `feature-dev:code-reviewer` or any review from `/feature-dev`.

#### Agent #1: Coverage + Gap Analyst

Read the checklist from `.claude/skills/test-review/references/test-quality-checklist.md` sections 1 and 3 (Coverage Gaps + Edge Case Coverage).

For each function/method/endpoint in the implementation diff:
- Is there a corresponding test?
- Does the test exercise the happy path AND at least one error path?
- Are input boundaries tested?
- For state mutations: is before-and-after verified?

For each conditional branch in the implementation:
- Is there a test that takes the true path?
- Is there a test that takes the false path?
- For switch/match: is there a test for each case + default?

Produce a **coverage map**: list of functions/endpoints with test status (tested, partially tested, untested).

#### Agent #2: Assertion Strength + Isolation Analyst

Read the checklist from `.claude/skills/test-review/references/test-quality-checklist.md` sections 2 and 5 (Assertion Strength + Test Quality Signals).

For each test in the diff:
- What is actually asserted? Is it precise enough?
- Would the test still pass if the feature was subtly broken?
- Is the test over-mocked (testing the mock instead of the code)?
- Does the test depend on other tests running first?
- Are side effects verified (DB writes, events emitted, logs produced)?

Rate each test assertion 1-5 for precision (1 = `toBeTruthy()`, 5 = exact value + side effect verification).

#### Agent #3: Failure Mode + Error Path Analyst

Read the checklist from `.claude/skills/test-review/references/test-quality-checklist.md` section 4 (Untested Failure Modes).

For each error handling path in the implementation diff:
- Is there a test that triggers this error?
- Does the test verify the error message/type, not just "an error was thrown"?
- For try/catch blocks: is the catch behavior tested?
- For network calls: are timeout, connection failure, and unexpected response tested?
- For database calls: are constraint violations, connection failures, and deadlocks tested?
- For partial failures: what happens when 3 of 5 items succeed?

Produce an **error path map**: list of error handlers with test status.

### Phase 3: Scoring + Issue Reporting

After all Phase 2 agents complete:

1. **Deduplicate** findings across agents (same file:line or same gap).

2. **Score each finding** 0-100 for severity:
   ```
   0-25:  Pedantic. Pre-existing gap, or code path is trivial/unreachable.
   26-50: Minor gap on non-critical code. Won't cause real bugs.
   51-69: Valid gap. Missing test for a realistic scenario.
   70-79: Real risk. Feature could break without anyone noticing.
   80-89: Important. Critical path undertested, or assertions too weak to catch regressions.
   90-100: Dangerous. Core functionality untested, or test would pass with broken code.
   ```

3. **Filter**: Drop below 60. Map to P0-P3 per severity table above.

4. **Write agent-consumable findings file:**

   Create `.orchestrate/` directory if it doesn't exist. Write findings to `.orchestrate/test-review.md` following the format in `.claude/skills/review-output-format.md`.

   **Each finding MUST include:**
   - `**ID:**` with severity-numbered tag (P1-1, P2-3, etc.)
   - `**File:**` source file that's missing test coverage (not the test file)
   - `**Source:**` which analysis agent found it
   - `**Current code:**` the untested function/method verbatim (3-10 lines)
   - `**Problem:**` what failure scenario is uncovered, what could break undetected
   - `**Fix — Option A (recommended):**` test file to create/modify, test function signatures, what to assert, prerequisite protocols/test doubles needed, and example test code (skeleton with assertions, not just function names)
   - `**Fix — Option B:**` alternative approach (e.g., integration test vs unit test)
   - `**Fix — Option C: Do nothing** with consequences
   - `**Verification:**` how to confirm the test catches the gap (e.g., "mutate line X, test should fail")

   For test coverage findings specifically, the fix code should include:
   - The test file path
   - Any protocol/mock types that need to be created first
   - Complete test function with `@Test` attribute and `#expect` assertions
   - Dependency injection setup if needed

   The file starts with a summary header. Include the coverage map inline. Include a deduplication log at the end.

### Phase 4: Output

#### PR mode (post as GitHub comment):

```markdown
### Test Review

**Reviewed**: X test files, Y implementation files
**Assessment**: [PASS / NEEDS_WORK / CRITICAL_GAPS]

---

**Coverage Map**
| Function/Endpoint | Tests | Coverage | Gaps |
|-------------------|-------|----------|------|
| createUser() | 3 | High | Missing: duplicate email |
| deleteUser() | 0 | None | P0: No tests at all |
...

**P0 - Critical** (X found)
1. **[Finding title]**
   [Description with file:line]
   [Options with effort/risk/impact]
   [Recommendation]

**P1 - High** (X found)
...

**P2 - Medium** (X found)
...

---

**Strengths**
- [What's well tested — cite specific tests]

Generated with [Claude Code](https://claude.ai/code) | Test Review v1.0
```

#### Local mode (terminal output):

Same structured output. The detailed findings file was already written in Phase 3 step 4 to `.orchestrate/test-review.md`.

Then show:

```markdown
## Next Steps

Found X gaps (P0: _, P1: _, P2: _, P3: _).
Findings written to: `.orchestrate/test-review.md`

**How would you like to proceed?**
1. Deploy test-writing agent (reads findings file, creates all tests)
2. Deploy agent for P0/P1 tests only
3. Generate specific tests (list IDs, e.g. P1-1, P1-3)
4. No changes — review only
```

**IMPORTANT**: Do NOT generate tests until user explicitly confirms.
