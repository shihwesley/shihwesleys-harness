---
name: commit-split
description: Use when finishing a feature with many uncommitted changes that need splitting into logical, reviewable commits. Triggered by "/commit-split" or when atomic commits rule applies at finish time.
user-invocable: true
allowed-tools: ["Bash", "Read", "Glob", "Grep", "AskUserQuestion"]
---

# Commit Split

Break uncommitted or staged changes into a series of logical, reviewable commits.

## When to Use

- Large diff with multiple concerns (models + routes + tests + config)
- Before merge/PR when work was done without incremental commits
- User says "split commits", "break into commits", or `/commit-split`

## Process

### 1. Survey Changes

```bash
git status
git diff --stat          # unstaged
git diff --cached --stat # staged
```

### 2. Categorize by Concern

Group changed files into logical units. Common groupings:

| Commit order | Category | Example files |
|-------------|----------|---------------|
| 1 | Schema/models | migrations, models, types |
| 2 | Core logic | services, helpers, utils |
| 3 | API/routes | controllers, routes, handlers |
| 4 | UI | components, views, styles |
| 5 | Tests | test files matching above |
| 6 | Config/docs | package.json, README, config |

**Ordering principle:** Dependencies first. Models before services before routes before tests.

### 3. Present Plan

Show user the proposed commit groups:

```
Proposed commits (N total):

1. "Add user model and migration" → 3 files
2. "Implement auth service" → 2 files
3. "Add login/register routes" → 2 files
4. "Add auth tests" → 3 files

Proceed?
```

**Wait for approval.** User may want to regroup.

### 4. Execute Commits

For each group:

```bash
# Reset staging area
git reset HEAD

# Stage only this group's files
git add <file1> <file2> ...

# Commit with descriptive message
git commit -m "<message>"
```

**Commit message style:** Match the repo's existing style (`git log --oneline -5`).

### 5. Verify

```bash
git log --oneline -<N>  # Show the N new commits
```

## Rules

- **NEVER use `git add -A` or `git add .`** — always stage specific files
- **NEVER amend previous commits** unless user explicitly asks
- **NEVER rebase/squash** — this skill creates commits, not reorganizes them
- If a file has changes spanning multiple concerns, ask user how to handle it (split with `git add -p` or assign to one commit)
- Always present the plan before executing any commits

## Partial File Splitting

When a single file has changes for multiple commits:

```bash
git add -p <file>  # Interactive hunk staging
```

Warn user: "File X has mixed changes — I'll use patch mode to split hunks. This works best when changes are in separate functions/sections."

## Integration

- **During development:** Follow the atomic commits CLAUDE.md rule — commit at natural boundaries
- **At finish time:** Use this skill to split accumulated changes before merge/PR
- **With finishing-a-development-branch:** Run `/commit-split` before that skill's Step 1
