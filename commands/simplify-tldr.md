---
name: simplify-tldr
description: "TLDR-aware code simplifier that uses AST summaries for context and reads only target files in full. Use when user says /simplify, wants to reduce code complexity, remove dead code, or simplify over-engineered patterns. Saves 80%+ tokens via merkle-integrated O(1) cache lookups."
argument-hint: "[file or pattern]"
---

# TLDR-Aware Code Simplifier

Launch the TLDR-optimized code simplifier agent to refine recently modified code.

## How It Works

This simplifier is **TLDR-aware**:
1. Uses AST summaries to survey the codebase (saves ~95% tokens)
2. Requests specific line ranges only for code it will modify
3. Preserves full context while minimizing token consumption
4. **Auto-logs** all changes to `SIMPLIFICATION_LOG.md` in project root

## Usage

```bash
# Simplify recently modified files
/simplify-tldr

# Simplify specific file
/simplify-tldr src/api/auth.ts

# Simplify pattern
/simplify-tldr src/components/*.tsx
```

## Agent Instructions

You are now operating as the **TLDR-aware code simplifier**. Follow the protocol defined in `.claude/agents/code-simplifier-tldr.md`:

1. **Discovery**: Use TLDR summaries to understand file structures
2. **Target**: Request line ranges for sections you'll modify
3. **Simplify**: Apply project standards and clarity improvements
4. **Verify**: Confirm changes with targeted reads
5. **Log**: Write/append session summary to `SIMPLIFICATION_LOG.md`

$ARGUMENTS

Begin by checking what files were recently modified with `git diff --name-only HEAD~3`, then survey them using TLDR summaries before diving into specific sections.
