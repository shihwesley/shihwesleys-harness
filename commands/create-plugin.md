---
name: create-plugin
description: Create or audit Claude Code plugins. Use --audit to analyze an existing plugin against quality standards.
argument-hint: [description] or --audit [path]
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "TodoWrite", "AskUserQuestion", "Skill", "Task"]
---

# Plugin Creation & Audit

**Initial request:** $ARGUMENTS

## Argument Routing

Parse `$ARGUMENTS` to determine the workflow mode:

- If arguments contain `--audit` → jump to **Audit Mode** below. The path after `--audit` is the plugin directory (default: current directory).
- Otherwise → Read the full creation workflow from the plugin-dev marketplace source and follow it:
  Read file: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/commands/create-plugin.md`
  Follow its Phase 1-8 workflow exactly, passing `$ARGUMENTS` as the initial request.

---

## Audit Mode

**Triggered by:** `/create-plugin --audit [path]` or `/create-plugin --audit`

Analyzes an existing plugin against the full quality bar — technical structure, content quality, distribution readiness, and official directory submission criteria. Produces a scored report with actionable fixes.

### Audit Step 1: Locate and Scan

1. Resolve plugin path (from argument, or current directory if omitted)
2. Verify it's a plugin by checking for any of:
   - `.claude-plugin/plugin.json`
   - `commands/` or `skills/` or `agents/` directory
   - `hooks/hooks.json`
   - `.mcp.json` or `.lsp.json`
3. If no plugin markers found, ask user: "No plugin detected at [path]. Point me to the right directory?"
4. Read `plugin.json` manifest (if present) to understand declared metadata
5. Scan directory structure — catalog every component found:
   - Skills (skills/*/SKILL.md)
   - Commands (commands/*.md)
   - Agents (agents/*.md)
   - Hooks (hooks/hooks.json or inline in plugin.json)
   - MCP servers (.mcp.json or inline)
   - LSP servers (.lsp.json or inline)
6. Create a todo list to track audit progress

**Output**: Component inventory table

### Audit Step 2: Technical Quality Check

Run every check from the technical quality bar:

| Check | How to verify |
|---|---|
| Validation | Run `claude plugin validate .` in plugin directory |
| Manifest completeness | Read plugin.json, flag missing fields: `name`, `version`, `description`, `author` (name+email), `homepage`, `repository`, `license`, `keywords` |
| Directory structure | Components at root, only plugin.json inside `.claude-plugin/` |
| Path safety | Grep for absolute paths and `../` traversals across all JSON/MD files |
| `${CLAUDE_PLUGIN_ROOT}` usage | Check every hook command and MCP server config uses it |
| Script permissions | For each .sh/.py/.js in scripts/, check executable bit with `ls -la` |
| Secrets scan | Grep for patterns: API keys, tokens, passwords, hardcoded URLs with credentials |
| LICENSE file | Check plugin root for LICENSE or LICENSE.md |
| CHANGELOG | Check plugin root for CHANGELOG.md |
| Versioning | Verify version in plugin.json follows semver; flag 0.x.x as pre-release |

Score: X/10 passed

**Output**: Technical findings table with pass/fail/warning per check

### Audit Step 3: Content Quality Check

For each component found in Step 1:

**Skills:**
- Read each SKILL.md frontmatter — does `description` use third-person with specific trigger phrases?
- Is the body in imperative form?
- Are there reference files or examples alongside SKILL.md?
- Word count check: is the body 1,500-2,000 words (progressive disclosure)?

**Commands:**
- Read each command .md frontmatter — does it have `description` and `argument-hint`?
- Are `allowed-tools` minimal and appropriate?
- Are instructions written FOR Claude (not TO the user)?

**Agents:**
- Read each agent .md — does it have `<example>` blocks?
- Are trigger conditions specific (not vague)?
- Does `whenToUse` have concrete scenarios?

**Hooks:**
- Are event names exact and case-sensitive? (`PostToolUse` not `postToolUse`)
- Do hook commands use `${CLAUDE_PLUGIN_ROOT}`?
- Are hook types valid? (`command`, `prompt`, or `agent`)

**MCP servers:**
- Do configs use `${CLAUDE_PLUGIN_ROOT}` for paths?
- Are env vars documented in README?

Score: X/N components passed (report per component)

**Output**: Per-component findings with specific line references

### Audit Step 4: README Assessment

1. Check if README.md exists
2. If it does, evaluate against cognitive funnel:
   - [ ] Has a one-liner (what + why)
   - [ ] Has visual proof (screenshot, GIF, Mermaid diagram, or code output)
   - [ ] Has install instructions (copy-paste ready)
   - [ ] Has quick start / usage example with expected output
   - [ ] Has TOC if >100 lines
   - [ ] No section exceeds 80 lines
   - [ ] No placeholder or empty sections
3. If README is missing or below standard, offer to generate one using `/writing-readmes`

Score: X/7 passed

**Output**: README gap analysis

### Audit Step 5: Official Directory Submission Readiness

Run the submission form checklist (form: https://docs.google.com/forms/d/e/1FAIpQLSc31jdYDs_1z649BmFfX85mSSdyTXi0GOLsHD7tWKj0F_k9Dg/viewform):

- [ ] Plugin name: kebab-case, descriptive, stable
- [ ] In-app description: 50-100 words (check current description length)
- [ ] GitHub repo: plugin at top-level (check if current path is a git repo root)
- [ ] At least 3 use cases: scan README for use case / example sections
- [ ] Company/Org URL: check plugin.json `author.url` or `homepage`
- [ ] Contact email: check plugin.json `author.email`
- [ ] Stable version: 1.x.x+ (not 0.x.x)
- [ ] Platform target: determined from component types

Score: X/8 passed

**Output**: Submission readiness assessment

### Audit Step 6: Report & Fix

Present the full report:

```
Plugin Audit: [plugin-name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Components: X skills, Y commands, Z agents, W hooks, V MCP servers

Technical Quality:    X/10  [■■■■■■■□□□]
Content Quality:      X/N   [■■■■■□□□□□]
README:               X/7   [■■■■□□□□□□]
Submission Ready:     X/8   [■■■■■■□□□□]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall:              XX/YY

Critical (must fix):
  1. [issue]
  2. [issue]

Warnings (should fix):
  1. [issue]

Suggestions (nice to have):
  1. [issue]
```

**Ask user** with AskUserQuestion:
- "Fix all critical issues now" — auto-fix what can be fixed (missing fields, permissions, structure)
- "Fix critical + warnings" — more thorough pass
- "Generate fix plan only" — list changes without applying them
- "I'll fix manually" — just take the report

For any fixes applied, show a before/after diff summary.

**End of Audit Mode.**
