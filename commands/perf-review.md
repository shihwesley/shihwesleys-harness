---
name: perf-review
description: "Use when auditing code performance, optimizing before deployment, or checking for N+1 queries, memory leaks, missing caches, and algorithmic complexity issues."
argument-hint: "[PR number or 'local' for unstaged changes]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# Performance Review

Specialized review of runtime performance, database access patterns, memory efficiency, caching strategy, and algorithmic complexity. Focuses on issues that affect real users at real scale — not theoretical micro-optimizations.

**Target:** "$ARGUMENTS"

## Severity Levels

| Level | Name | Threshold | Action |
|-------|------|-----------|--------|
| P0 | Critical | 90-100 | Must fix. Will cause outage or data loss at current scale. |
| P1 | High | 80-89 | Should fix. Measurable degradation under normal load. |
| P2 | Medium | 70-79 | Fix soon. Works now, breaks at 10x scale. |
| P3 | Low | <70 | Optimization opportunity. Measurable but not urgent. Only report if >=60. |

## Workflow

### Phase 1: Gather Context

Launch a **general-purpose** agent (model: `sonnet`) to:

1. **Determine review target:**
   - PR number → `gh pr diff <number>`
   - `local` or empty → `git diff` + `git diff --cached`
   - Branch name → `git diff main...<branch>`

2. **Classify changed code by performance domain:**
   - **Database layer**: files touching ORM/queries/migrations/models
   - **API layer**: route handlers, controllers, middleware
   - **Compute layer**: business logic, data transformation, algorithms
   - **UI layer**: views, components, rendering code
   - **Infrastructure**: caching config, connection pools, queues

3. **Detect tech stack** from imports and project structure:
   - Database: PostgreSQL, MySQL, SQLite, MongoDB, etc.
   - ORM: ActiveRecord, Prisma, SQLAlchemy, GRDB, CoreData, etc.
   - Cache: Redis, Memcached, in-memory, none
   - Runtime: Node.js, Python, Swift, Go, etc.

4. **Read project CLAUDE.md** for performance-relevant conventions.

5. **Return:** Diff by domain, stack info, project conventions.

### Phase 2: Deep Analysis (Parallel Agents)

Launch **3 parallel general-purpose agents** (model: `sonnet`), each receiving the full diff, domain classification, and stack info.

**IMPORTANT:** Use `subagent_type: "general-purpose"`. Do NOT use `feature-dev:code-reviewer` or any review from `/feature-dev`.

#### Agent #1: Database + I/O Analyst

Read the checklist from `.claude/skills/perf-review/references/performance-checklist.md` sections 1 and 5 (Database Access Patterns + Resource Management).

Focus:
- Trace every database call in the diff. Is it inside a loop? Is there a batch alternative?
- For each query: does the WHERE clause use an indexed column? Check schema if accessible.
- For each write: is it inside a transaction? Should it be?
- For each connection/handle: is it properly closed in all code paths (including error)?
- For each API call to external services: is there a timeout? What happens on failure?

Produce a **query map**: list of all DB operations with their context (loop/single, indexed/unindexed, transactional/not).

#### Agent #2: Memory + Resource Analyst

Read the checklist from `.claude/skills/perf-review/references/performance-checklist.md` sections 2 and 5 (Memory Usage + Resource Management).

Focus:
- Identify every collection that could grow with user data. Is there a size limit?
- Trace object lifetimes: is anything held longer than needed?
- Check for closure captures that retain large objects (especially in Swift/iOS)
- Check for event listener registration without corresponding removal
- Check for large data loaded into memory: files, images, API responses
- Platform-specific: retain cycles (Swift), goroutine leaks (Go), Buffer leaks (Node), etc.

Produce a **memory risk map**: list of allocations with growth classification (bounded/unbounded, short-lived/long-lived).

#### Agent #3: Caching + Complexity Analyst

Read the checklist from `.claude/skills/perf-review/references/performance-checklist.md` sections 3 and 4 (Caching Opportunities + Algorithmic Complexity).

Focus:
- Find repeated identical operations (same query, same computation, same API call) in a single request path. Flag missing memoization/cache.
- Classify algorithmic complexity of loops and data processing. Flag anything O(n^2) or worse on potentially large input.
- Check for main thread blocking: synchronous I/O, heavy computation, large sort/filter on UI thread.
- Check for sequential async calls that could be parallel.
- Check HTTP caching headers on new endpoints.
- Check for existing caches: do they have TTL? Max size? Invalidation?

Produce a **hotspot map**: list of code paths with estimated complexity and scale threshold.

### Phase 3: Scoring + Issue Reporting

After all Phase 2 agents complete:

1. **Deduplicate** findings across agents.

2. **Score each finding** 0-100 for severity, considering scale:
   ```
   0-25:  Theoretical. Would need 100x current scale to matter. Cold path.
   26-50: Minor. Suboptimal but within acceptable latency at current scale.
   51-69: Real but not urgent. Will need fixing before next scale milestone.
   70-79: Noticeable at current scale. Users may experience slowness.
   80-89: Measurable degradation now. P95 latency affected, or resource waste significant.
   90-100: Will cause outage, OOM, or cascading failure at current traffic.
   ```

3. **Filter**: Drop below 60. Map to P0-P3 per severity table above.

4. **Write agent-consumable findings file:**

   Create `.orchestrate/` directory if it doesn't exist. Write findings to `.orchestrate/perf-review.md` following the format in `.claude/skills/review-output-format.md`.

   **Each finding MUST include:**
   - `**ID:**` with severity-numbered tag (P1-1, P2-3, etc.)
   - `**File:**` with exact path and line number(s)
   - `**Source:**` which analysis agent found it
   - `**Current code:**` verbatim from the source file (3-10 lines, fenced code block)
   - `**Problem:**` specific perf scenario (at what scale it breaks, what metric degrades, what the user sees)
   - `**Fix — Option A (recommended):**` exact replacement code in fenced block, with explanation of why it's faster
   - `**Fix — Option B:**` alternative (or "Do nothing" with consequences and scale threshold)
   - `**Verification:**` how to confirm the fix (profiling step, benchmark, or observable behavior)

   The file starts with a summary header. Include the hotspot map inline. Include a deduplication log at the end.

   Optionally include a "Non-Issues" section listing things investigated and cleared (helps avoid re-investigation).

### Phase 4: Output

#### PR mode (post as GitHub comment):

```markdown
### Performance Review

**Reviewed**: X files across Y performance domains
**Assessment**: [CLEAN / MINOR_ISSUES / NEEDS_OPTIMIZATION / CRITICAL]

---

**Hotspot Map**
| Code Path | Complexity | Scale Threshold | Domain |
|-----------|-----------|-----------------|--------|
| getUserPosts() | O(n) queries (N+1) | Breaks at 100 users | Database |
| processBatch() | O(n^2) | Breaks at 1K items | Compute |
| renderFeed() | Unbounded memory | Breaks at 500 items | Memory |
...

**P0 - Critical** (X found)
1. **[Finding title]**
   [Description with file:line]
   [Scale impact: at what point this becomes a problem]
   [Options with effort/risk/impact]
   [Recommendation]

**P1 - High** (X found)
...

**P2 - Medium** (X found)
...

---

**Strengths**
- [What's well optimized — cite specific patterns]

Generated with [Claude Code](https://claude.ai/code) | Perf Review v1.0
```

#### Local mode (terminal output):

Same structured output. The detailed findings file was already written in Phase 3 step 4 to `.orchestrate/perf-review.md`.

Then show:

```markdown
## Next Steps

Found X issues (P0: _, P1: _, P2: _, P3: _).
Findings written to: `.orchestrate/perf-review.md`

**How would you like to proceed?**
1. Deploy fix agent (reads findings file, applies all fixes)
2. Deploy fix agent for P0/P1 only
3. Fix specific items (list IDs, e.g. P1-1, P2-3)
4. No changes — review only
```

**IMPORTANT**: Do NOT implement fixes until user explicitly confirms.
