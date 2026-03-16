#!/usr/bin/env bash
# plan-mode-redirect.sh
# Blocks EnterPlanMode and redirects the agent to use /interactive-planning instead.
# Exit code 2 = block the tool call and send stdout as feedback to the agent.

cat <<'MSG'
BLOCKED: Do not use EnterPlanMode. Use the /interactive-planning skill instead.

Invoke it with: Skill(skill="interactive-planning")

This gives you interactive gates (AskUserQuestion), TaskCreate-based tracking,
findings.md/progress.md persistence, and optional worktree orchestration —
all of which the built-in plan mode lacks.
MSG

exit 2
