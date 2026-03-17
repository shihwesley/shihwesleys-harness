---
description: "Anthropic Skill Guide audit of all 14 gstack skills + root SKILL.md"
updated: 2026-03-16
source: "https://github.com/garrytan/gstack"
guide: "shihwesleys-harness/references/anthropic-skill-guide.md"
---

# gstack Skill Audit

Audited against `anthropic-skill-guide.md` (Chapters 1-5). Core ideas preserved — only formatting and structural issues flagged.

## Overall Assessment

**Quality: HIGH** — gstack is a well-built skill pack. The frontmatter is clean, descriptions include trigger phrases, folder naming follows kebab-case, and workflows are specific and actionable. The main structural issue is the template-based boilerplate that inflates every skill by ~80 lines.

## Per-Skill Audit

### Pass (no issues)

| Skill | Lines | Notes |
|-------|-------|-------|
| `browse` | 443 | Root skill, comprehensive command reference |
| `qa` | 618 | Strong trigger phrases, clear tiers |
| `qa-only` | 453 | Good differentiation from `/qa` |
| `review` | 268 | Clean, focused |
| `setup-browser-cookies` | 155 | Right-sized |
| `gstack-upgrade` | 201 | Clean utility skill |

### Pass with notes

| Skill | Lines | Issue | Severity |
|-------|-------|-------|----------|
| `design-consultation` | 382 | Description could add trigger phrases ("design my app", "create design system") | LOW |
| `document-release` | 437 | Description missing trigger phrases ("update docs after shipping") | LOW |
| `plan-ceo-review` | 572 | Over 150-line recommendation; ~80 lines is shared boilerplate | LOW |
| `plan-design-review` | 558 | Same boilerplate issue | LOW |
| `plan-eng-review` | 263 | Description could mention "review my plan" as trigger | LOW |
| `qa-design-review` | 645 | Longest skill — 80 lines boilerplate + 80-item checklist inline | MEDIUM |
| `retro` | 550 | Over 150-line recommendation; metric computation is detailed but necessary | LOW |
| `ship` | 504 | Description is terse compared to others — could add "merge and deploy", "create PR" triggers | LOW |

### Root `SKILL.md` (gstack)

The root SKILL.md duplicates the `browse` skill content verbatim. This is intentional — it's the default entry point when gstack is installed as a single skill. No issue per the Anthropic guide, but worth noting it exists.

---

## Structural Audit (Anthropic Guide Checklist)

### 1. File naming ✅
All `SKILL.md` files are exact case. All folders are kebab-case.

### 2. Frontmatter ✅
All skills have `---` delimiters, `name` in kebab-case, `description` with WHAT + WHEN.

**Minor finding:** No skills use XML angle brackets in frontmatter (good). All descriptions are under 1024 chars (good). The `allowed-tools` field is a gstack-specific addition — not in the Anthropic spec but not prohibited.

### 3. Progressive disclosure ⚠️ PARTIAL
- **Level 1 (frontmatter):** All skills have good frontmatter. ✅
- **Level 2 (SKILL.md body):** Skills are self-contained. ✅
- **Level 3 (references/):** NOT USED. Several skills (plan-ceo-review, qa-design-review, retro) exceed the 150-line recommendation significantly. The shared boilerplate (preamble, AskUserQuestion format, contributor mode) could live in a shared `references/` file.

**Recommendation (not applied — core to gstack's template system):** Extract the ~80-line shared preamble/AskUserQuestion/Contributor Mode sections into `references/shared-sections.md` and reference it from each SKILL.md. This would bring most skills under 200 lines.

### 4. SKILL.md size ⚠️
- 6 skills under 300 lines ✅
- 5 skills 300-500 lines ⚠️
- 3 skills over 500 lines ⚠️ (plan-ceo-review: 572, plan-design-review: 558, qa-design-review: 645)

The Anthropic guide recommends under 150 lines (~5000 words). gstack skills are larger because of the template boilerplate and because they encode complete multi-phase workflows. This is a trade-off the author made deliberately — each skill is fully self-contained and doesn't require reading external files.

### 5. Instructions ✅
All skills are specific and actionable. Error handling is present (browse binary not found, merge conflicts, test failures). Bash code examples are concrete with expected outputs.

### 6. No README.md ✅
No README.md files inside skill folders.

### 7. Description trigger phrases ✅ FIXED
Trigger phrases added to 5 skills that were missing them:
- `design-consultation` — "design my app", "create a design system", "pick fonts and colors"
- `document-release` — "update docs", "sync documentation", "document what shipped"
- `plan-eng-review` — "review my plan", "eng review", "check my architecture"
- `ship` — "ship it", "ship this branch", "merge and deploy", "create a PR"
- `review` — "review my code", "review this PR", "check before merge"

---

## Formatting Improvements Applied

Trigger phrases added to 5 skill descriptions (design-consultation, document-release, plan-eng-review, ship, review). No other changes — core ideas preserved.

## Summary

| Check | Status |
|-------|--------|
| File naming | ✅ Pass |
| Folder naming | ✅ Pass |
| Frontmatter format | ✅ Pass |
| Description quality | ✅ Pass (5 fixed) |
| Progressive disclosure | ⚠️ No references/ used |
| Size guideline | ⚠️ 8/14 over 300 lines |
| Instructions quality | ✅ Pass |
| No README.md | ✅ Pass |
| Error handling | ✅ Pass |
| Security (no XML in frontmatter) | ✅ Pass |
