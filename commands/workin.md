---
name: workin
description: "Use when user wants to switch working directory to a project. Triggered by \"/workin <project>\". Does cd only — no exploration, no analysis, no file reading."
user-invocable: true
allowed-tools: ["Bash"]
---

# Work In Project

Switch working directory to a project under `/Users/quartershots/Source/`.

## Usage

```
/workin <project-name>
```

## Process

1. **Fuzzy match** the argument against directories in `/Users/quartershots/Source/`
   - Case-insensitive match
   - If exact match exists, use it
   - If no exact match, find closest substring match
   - If ambiguous (multiple matches), ask user to pick
2. **`cd` into the matched directory** using Bash
3. **Persist the path** by running: `echo "/Users/quartershots/Source/<project>" > ~/.claude/last-workin`
4. **Confirm** with one line: `Now working in /Users/quartershots/Source/<project>`
5. **STOP. Do nothing else.**

## Rules

- **DO NOT** read any files
- **DO NOT** explore the directory
- **DO NOT** run `ls`, `git status`, or any discovery commands
- **DO NOT** analyze the project structure
- **DO NOT** read CLAUDE.md or any project docs
- Wait for the user's next instruction
