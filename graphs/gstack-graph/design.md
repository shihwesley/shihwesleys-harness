---
description: "gstack design system skills — consultation, audit, and design QA."
updated: 2026-03-16
parent: "[[index.md]]"
---

# Design Systems

Two complementary design skills: one creates your design system from scratch, the other audits an existing site against it.

## Skills

| Skill | Path | Purpose |
|-------|------|---------|
| `/design-consultation` | `gstack/design-consultation/SKILL.md` | Build a complete design system → DESIGN.md |
| `/plan-design-review` | `gstack/plan-design-review/SKILL.md` | Audit a live site → prioritized report with grades |
| `/qa-design-review` | `gstack/qa-design-review/SKILL.md` | Audit + fix loop (modifies code) |

## Design Consultation Phases

1. **Pre-checks** — Look for existing DESIGN.md, gather codebase context
2. **Product Context** — What does the product do? Who's the user? What's the vibe?
3. **Research** — Competitor analysis (optional)
4. **Complete Proposal** — Aesthetic, typography, color, spacing, layout, motion
5. **Drill-downs** — User-requested adjustments
6. **Font & Color Preview** — Generated HTML preview page
7. **Write DESIGN.md** — Source of truth for the project's design system

Posture: design consultant, not form wizard. Proposes a coherent system and invites conversation.

## Design Audit Checklist (10 categories, ~80 items)

Used by both `/plan-design-review` and `/qa-design-review`:
- Typography (hierarchy, contrast, line length, orphans)
- Color (palette coherence, contrast ratios, dark mode)
- Spacing (consistency, rhythm, breathing room)
- Layout (alignment grid, responsive behavior, content density)
- Visual hierarchy (focal points, information architecture)
- Interaction (hover states, transitions, feedback)
- Accessibility (focus indicators, ARIA, touch targets)
- Performance (LCP, CLS, FID)
- Content (copy quality, placeholders, error messages)
- Polish (favicon, loading states, empty states)

## Related

- [[browser.md]] — Browse engine powers design screenshots and element inspection
- [[qa-testing.md]] — `/qa-design-review` is the fix-loop version
