---
description: "Navigation protocol for the Swift skill graph. Teaches agents how to traverse MOCs efficiently using TLDR-integrated progressive disclosure."
agent-only: true
---

# Swift Skill Graph — Traversal Protocol

You are navigating a skill graph for iOS/visionOS/Swift development. The graph is at `.claude/docs/swift-graph/`.

## How to Navigate

**Step 1 — Read the index.** Read `swift-graph/index.md`. The TLDR hook serves a summary with all domain MOCs and their descriptions. Pick 1-2 MOCs relevant to your current task.

**Step 2 — Read the relevant MOC(s).** Each MOC lists skills, docs, and agents with file paths and one-line descriptions. Pick the 2-3 items you actually need.

**Step 3 — Read the target files.** Now read the specific skill or doc files the MOC pointed you to. These have the operational knowledge.

**Step 4 — API details (if needed).** For exact API signatures, parameters, or platform availability, search the domain knowledge store:
```bash
cd ~/Source/neo-research && .venv/bin/python3 scripts/knowledge-cli.py search "<API or concept>" --project <store> --top-k 5
```
Pick `<store>` by domain: `spatial-computing` (RealityKit, ARKit, SceneKit), `swiftui`, `ml-ai` (Foundation Models, CoreML, Vision), `foundation-core`, `networking`, `security-auth`, `media-audio`, `uikit-appkit`, `metal`, `graphics`, `hardware-sensors`, `health-home-data`, `location-maps-weather`. Use `--top-k 3` for focused lookups.

## Rules

- **Never load all MOCs.** Pick only what matches the task.
- **Never read files the MOC didn't point you to.** The graph already filtered for you.
- **Don't re-read files you just wrote or edited.** You know the contents.
- **Follow `[[cross-references]]` only when they're relevant.** MOCs link to other MOCs — follow those links only if your task spans domains (e.g., a visionOS feature that needs TCA architecture).
- **TLDR summaries are your first pass.** If the hook serves a summary, scan it before requesting full content. Most navigation decisions happen at the summary level.

## Cost Budget

A well-navigated traversal costs ~3-4k tokens:
- Index summary: ~400 tokens
- 1-2 MOC summaries: ~600-1200 tokens
- 2-3 target file reads: ~1500-2500 tokens

Compare to loading all docs linearly: ~25k+ tokens. The graph pays for itself on the first task.

## When to Skip the Graph

- If you already know the exact file path → read it directly
- If the task is "fix line 42 of ContentView.swift" → no navigation needed
- If the user tells you which skill to load → load it, don't traverse

The graph is for discovery, not ceremony.
