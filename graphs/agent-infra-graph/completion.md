---
description: "Finishing work: phase-finisher (test→review→commit→merge), worktree-manager (git isolation), commit-split (atomic commits)"
keywords: [phase-finisher, worktree-manager, commit-split, merge, worktree, git-isolation]
---

# Completion & Isolation

Three files handle the "last mile": finishing agent work, managing git worktrees, and splitting commits.

## Phase Finisher

- **Skill: `phase-finisher`** → `.claude/skills/orchestrator/phase-finisher.md`
  Runs after all agents in a phase complete. Chains four steps:

  1. **Orbit test** — runs project test suite in the worktree
  2. **Code review** — `code-review-pro` on the working changes (see [[review.md]])
  3. **Commit** — `commit-split` breaks changes into atomic commits
  4. **Merge** — merges phase branch to main, cleans up worktree

  Mode-agnostic: works identically whether agents ran in team or classic mode. Receives aggregated results from either.

## Git Worktree Isolation

- **Skill: `worktree-manager`** → `.claude/skills/orchestrator/worktree-manager.md`
  Full lifecycle management (create → use → clean up) of git worktrees:

  - **Create**: `git worktree add ../{project}-phase-N orchestrate/phase-N-slug`
  - **Use**: agents work in the worktree directory, isolated from main
  - **Clean up**: after merge, removes worktree and branch

  Naming: worktree at `../{project}-phase-N`, branch `orchestrate/phase-N-slug`.
  Requires git 2.15+.

  Each phase gets its own worktree so phases can run in parallel without stepping on each other's files.

## Atomic Commits

- **Skill: `/commit-split`** → `.claude/commands/commit-split.md`
  Breaks a batch of uncommitted changes into logical, reviewable commits:

  - Groups by concern: models, routes, tests, config, etc.
  - Each commit is independently buildable
  - Useful both in the pipeline (called by `phase-finisher`) and standalone (`/commit-split` for retrospective splitting)

## The Completion Chain

```
agents complete
       ↓
phase-finisher
  ├── orbit test (fail → fix loop)
  ├── code-review-pro (P0 → fix loop)
  ├── commit-split (atomic commits)
  └── merge to main + worktree cleanup
```

## Cross-References

- Phase finisher receives results from dispatch → [[dispatch.md]]
- Code review step details → [[review.md]]
- Worktree creation happens during orchestration Stage 5 → [[orchestration.md]]
- Plans that produce the phases → [[planning.md]]
