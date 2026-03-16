---
name: code-review-pro
description: "Use when reviewing code before merge, after completing a feature, or when user says /code-review-pro. Covers SOLID, security, quality, and boundary conditions."
argument-hint: "[PR number or 'local' for unstaged changes]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# Code Review Pro

Deep, multi-agent code review combining parallel specialist analysis, structured checklists, confidence-based scoring, and P0-P3 severity classification.

**Target:** "$ARGUMENTS"

## Severity Levels

| Level | Name     | Threshold | Action                                    |
|-------|----------|-----------|-------------------------------------------|
| P0    | Critical | 90-100    | Must block merge. Security, data loss, correctness bug. |
| P1    | High     | 80-89     | Should fix before merge. Logic error, SOLID violation, perf regression. |
| P2    | Medium   | 70-79     | Fix in PR or follow-up. Code smell, maintainability. |
| P3    | Low      | <70       | Optional. Style, naming, minor suggestion. Only report if >=60. |

## Workflow

Execute these phases in order. Create a todo list to track progress.

---

### Phase 1: Preflight

Launch a **general-purpose** agent (model: `sonnet`) to gather context. It must:

1. **Determine review target:**
   - If argument is a PR number: `gh pr view <number>` to get details
   - If argument is `local` or empty: review unstaged changes via `git diff`
   - If argument is a branch name: `git diff main...<branch>`

2. **Check eligibility** (PR mode only):
   - Skip if closed, draft, or already reviewed by this tool
   - Skip if automated/trivial PR (eg. dependency bumps with no logic changes)

3. **Gather context:**
   - List all changed files with `git diff --stat`
   - Collect full diff content
   - Find all relevant CLAUDE.md files (root + directories of changed files)
   - Detect file types/languages to determine which agents apply

4. **Summarize:** Return a brief summary of what changed, file count, line count, and languages detected.

5. **Edge cases:**
   - **No changes**: Inform user. Ask if they want staged changes or a specific commit range.
   - **Large diff (>500 lines)**: Note this. Agents will batch by module/feature area.
   - **Mixed concerns**: Group findings by logical feature, not file order.

---

### Phase 2: Parallel Deep Review (Sonnet 4.6 agents)

Launch **up to 7 parallel general-purpose agents** (model: `sonnet`), each with a specialist focus. Each agent receives the diff, CLAUDE.md content, and its specific checklist.

**IMPORTANT:** Use `subagent_type: "general-purpose"` and `model: "sonnet"` for all Phase 2 agents. Do NOT use `feature-dev:code-reviewer` — these agents must follow the checklists below, not a pre-built review methodology.

**Always launch these 4 core agents:**

#### Agent #1: SOLID + Architecture Analyst

Read the SOLID checklist from `.claude/skills/code-review-pro/references/solid-checklist.md` and provide it to the agent.

Review the changes for:
- **SRP**: Modules with unrelated concerns, god objects, low cohesion
- **OCP**: New behavior requiring edits to switch/if blocks, missing extension points
- **LSP**: Type checks in overrides, precondition changes
- **ISP**: Broad interfaces with unused methods, stub implementations
- **DIP**: High-level logic coupled to concrete IO/storage types
- **Code organization & module structure**: Evaluate cohesion within modules, logical grouping of related code, separation of concerns across files/directories, and whether the structure makes navigation intuitive
- **Import & module patterns**: Circular dependencies, barrel re-export bloat, cross-layer imports, import style violations
- **Architecture smells**: Long methods (>30 lines), feature envy, data clumps, primitive obsession, shotgun surgery, divergent change, speculative generality, magic numbers

For each finding, provide ALL of:
- file:line reference
- Current code verbatim (3-10 lines, enough context to locate the edit)
- What principle is violated and what breaks
- Exact replacement code (ready to paste, not "change X to Y")
- Second option if applicable
Do NOT suggest large rewrites.

#### Agent #2: Security + Race Condition Hunter

Read the security checklist from `.claude/skills/code-review-pro/references/security-checklist.md` and provide it to the agent.

Scan for:
- **Input safety**: XSS, injection (SQL/NoSQL/command/GraphQL), SSRF, path traversal, prototype pollution
- **Auth/Authz**: Missing tenant/ownership checks, endpoints without guards, IDOR, client-trusted roles
- **JWT/Tokens**: Algorithm confusion, weak secrets, missing exp/iss/aud validation
- **Secrets/PII**: Credentials in code/config/logs, excessive PII logging
- **Supply chain**: Unpinned deps, dependency confusion, untrusted imports
- **CORS/Headers**: Overly permissive CORS, missing security headers
- **Race conditions**: Shared state without sync, TOCTOU, check-then-act, missing DB locking, read-modify-write without atomics
- **Crypto**: Weak algorithms (MD5/SHA1), hardcoded IVs, ECB mode, insufficient key length
- **Data integrity**: Missing transactions, partial writes, weak validation, missing idempotency

For each finding, provide ALL of:
- file:line reference
- Current code verbatim (3-10 lines)
- Severity (P0-P3) with exploit scenario
- Exact replacement code that fixes the vulnerability
- Verification step (how to confirm the fix)

#### Agent #3: Code Quality + Boundary Conditions

Read the quality checklist from `.claude/skills/code-review-pro/references/quality-checklist.md` and provide it to the agent.

Analyze for:
- **Error handling (call out explicitly)**: Swallowed exceptions, overly broad catches, error info leakage, missing async error handling, missing error boundaries. Every error handling gap must be called out with the specific scenario that would trigger it — no vague "might fail" warnings
- **Performance**: Expensive ops in hot paths, N+1 queries, missing indexes, over-fetching, missing pagination, unbounded collections, cache without TTL/invalidation
- **Boundary conditions**:
  - Null/undefined: missing checks, truthy/falsy confusion, optional chaining hiding issues
  - Empty collections: unhandled empty arrays/objects, unchecked first/last access
  - Numeric: division by zero, overflow, float comparison with ===, negative values, off-by-one
  - String: empty/whitespace-only, very long strings, unicode edge cases (emoji, RTL, combining chars)
- **DRY violations (be aggressive)**: Copy-pasted blocks, near-identical functions, same business rule in multiple places, parallel conditional chains. Flag any duplication that could be extracted — even 3-line repeats or similar-shaped logic with minor variations. Err on the side of flagging; let the author decide what's intentional
- **Naming conventions**: Names inconsistent with project CLAUDE.md style, misleading names, generic names that hide intent
- **Code complexity**: Deeply nested logic, complex conditionals, missing early returns
- **Technical debt hotspots**: Code that works now but will cause pain later — hardcoded values that should be config, tight coupling that blocks testability, workarounds with TODO/HACK/FIXME comments, patterns that diverge from the rest of the codebase, and any area where small changes require disproportionate effort

For each finding, provide ALL of:
- file:line reference
- Current code verbatim (3-10 lines)
- What breaks and when (specific scenario, not vague)
- Exact replacement code
- If the fix touches multiple files, list all files that need changing

#### Agent #4: Git History + Context Analyzer

This agent does NOT use a checklist file. Instead it:
- Reads `git blame` of modified files to understand history
- Reads `git log` of modified files for recent changes
- Checks previous PRs that touched these files via `gh pr list --search`
- Reads comments on recent related PRs
- Cross-references to find: patterns being violated, regressions, repeated issues, context the author may have missed

For each finding, provide ALL of:
- file:line reference
- Current code verbatim
- Historical context (what commit/PR introduced this, what pattern it violates)
- Whether it's a regression or pre-existing

**Conditionally launch these specialist agents:**

#### Agent #5: Silent Failure Hunter (if error handling code changed)

Systematically locate all try-catch blocks, error callbacks, conditional error branches, fallback logic, optional chaining that might hide errors. For each:
- Is the error logged with appropriate severity and context?
- Does the user receive clear, actionable feedback?
- Is the catch block specific enough?
- Does fallback behavior mask the real problem?
- Should this error propagate instead of being caught?

Flag: empty catch blocks, catch-and-continue, returning defaults on error without logging, retry logic without user notification.

#### Agent #6: Test Coverage Analyst (if test files changed or new functionality added)

Focus on behavioral coverage, not line coverage:
- Critical code paths with no tests
- Missing edge case coverage for boundary conditions
- Untested error handling paths
- Missing negative test cases
- Tests coupled to implementation details rather than behavior
- Rate each gap 1-10 criticality

#### Agent #7: Type Design Analyzer (if new types/interfaces/structs added)

Analyze new types for:
- Invariant identification and enforcement
- Encapsulation quality (rate 1-10)
- Invariant expression clarity (rate 1-10)
- Whether illegal states are representable
- Missing constructor validation
- Mutable internals exposure

---

### Phase 3: Confidence Scoring + Deduplication (Sonnet 4.6 agents)

After all Phase 2 agents complete:

1. **Deduplicate**: Merge findings that reference the same file:line or describe the same issue from different agents. Keep the most detailed version.

2. **Score each unique finding** with a parallel **general-purpose** agent (model: `sonnet`) that receives:
   - The finding description
   - The relevant diff context
   - The CLAUDE.md files
   - This scoring rubric (provide verbatim):

   ```
   Score 0-100 confidence that this is a real, actionable issue:

   0-25: False positive. Pre-existing issue, or doesn't stand up to scrutiny.
         Stylistic issue not in CLAUDE.md. Linter/compiler would catch it.
   26-50: Might be real but likely a nitpick. Not explicitly in CLAUDE.md.
          General quality concern without specific impact.
   51-69: Valid but low-impact. Minor improvement opportunity.
   70-79: Real issue, moderate impact. Should be addressed.
   80-89: Verified important issue. Will affect functionality or violates
          explicit CLAUDE.md rule. Should fix before merge.
   90-100: Confirmed critical issue. Security vulnerability, data loss risk,
           or correctness bug that will happen in practice.
   ```

3. **Filter**: Drop findings scoring below 60. Map scores to severity:
   - 90-100 -> P0 Critical
   - 80-89 -> P1 High
   - 70-79 -> P2 Medium
   - 60-69 -> P3 Low

4. **False positive checklist** - additionally filter out:
   - Pre-existing issues (not introduced by this diff)
   - Issues a linter/typechecker/compiler would catch
   - Pedantic nitpicks a senior engineer wouldn't flag
   - General quality concerns not in CLAUDE.md (unless P0/P1 severity)
   - Issues on lines not modified in this PR
   - Intentional functionality changes related to the PR's purpose
   - Issues silenced by lint-ignore comments

5. **Write agent-consumable findings file:**

   Create `.orchestrate/` directory if it doesn't exist. Write findings to `.orchestrate/code-review.md` following the format in `.claude/skills/review-output-format.md`.

   **Each finding MUST include:**
   - `**ID:**` with severity-numbered tag (P1-1, P2-3, etc.)
   - `**File:**` with exact path and line number(s)
   - `**Source:**` which analysis agent found it
   - `**Current code:**` verbatim from the source file (3-10 lines, fenced code block)
   - `**Problem:**` specific failure scenario, not vague
   - `**Fix — Option A (recommended):**` exact replacement code in fenced block
   - `**Fix — Option B:**` alternative (or "Do nothing" with consequences)
   - `**Verification:**` how to confirm the fix

   The file starts with a summary header (review type, date, severity counts, verdict). This header is what the phase-runner coordinator reads. Everything below is for the fix agent.

   Include a deduplication log at the end showing which findings were merged and from which agents.

   Optionally include a "Non-Issues" section listing things investigated and cleared.

---

### Phase 4: Output

#### If reviewing a PR (post as GitHub comment):

Use `gh pr comment <number>` with this format:

```markdown
### Code Review Pro

**Reviewed**: X files, Y lines changed
**Assessment**: [APPROVE / REQUEST_CHANGES / COMMENT]

---

**P0 - Critical** (X found)

1. **[Brief title]** — [Agent that found it]
   [Description of issue and why it matters]
   [Link to file:line with full SHA, eg https://github.com/owner/repo/blob/<full-sha>/path/file.ext#L10-L15]

**P1 - High** (X found)
...

**P2 - Medium** (X found)
...

**P3 - Low** (X found)
...

---

**Removal Candidates** (if any dead code found)
- [file:line] — [what and why it's safe to remove]

**Strengths**
- [What's well done — be specific with file:line references]

Generated with [Claude Code](https://claude.ai/code) | Review Pro v1.0

<sub>If this review was useful, react with a thumbs up. Otherwise, react with a thumbs down.</sub>
```

**Linking rules:**
- Full git SHA required (not abbreviated)
- Format: `https://github.com/owner/repo/blob/<sha>/path#L<start>-L<end>`
- Include 1 line of context before and after
- Repo name must match the actual repo

#### If reviewing local changes (display in terminal):

Display the same structured output. The detailed findings file was already written in Phase 3 step 5 to `.orchestrate/code-review.md`.

Then show:

```markdown
## Next Steps

Found X issues (P0: _, P1: _, P2: _, P3: _).
Findings written to: `.orchestrate/code-review.md`

**How would you like to proceed?**
1. Deploy fix agent (reads findings file, applies all fixes)
2. Deploy fix agent for P0/P1 only
3. Fix specific items (list IDs, e.g. P1-1, P2-3)
4. No changes — review only
```

**IMPORTANT**: Do NOT implement any fixes until user explicitly confirms. This is a review-first workflow.

---

## Notes

- Do not attempt to build, lint, or typecheck — assume CI handles that
- Use `gh` for all GitHub interaction
- When linking code in PR comments, use full SHA (not `$(git rev-parse HEAD)`)
- Each agent should return findings with: description, file:line, severity estimate, confidence estimate, suggested fix
- Agents operate autonomously — give each one the full diff and relevant CLAUDE.md content
- For diffs >500 lines, agents should batch by module/feature area
- If no issues meet the threshold, post/display a clean review confirmation
