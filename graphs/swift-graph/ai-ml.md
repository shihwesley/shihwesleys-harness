---
description: "On-device AI/ML: Apple Foundation Models (@Generable, @Guide, tool calling), CoreML pipeline, Vision framework, on-device inference"
keywords: [foundation-models, generable, coreml, vision, on-device-ai, guided-generation]
---

# On-Device AI & ML

Apple's AI stack in iOS 26: Foundation Models (3B parameter LLM on-device), CoreML (custom models), Vision (image analysis). All run locally — no server needed.

## Apple Foundation Models (iOS 26+)

The on-device LLM with structured output:

- **Skill: `/on-device-ai`** → `.claude/commands/on-device-ai.md`
  @Generable for type-safe structured output, @Guide for constrained generation, tool calling, streaming, availability checks (`LanguageModelSession.isAvailable`).

- **Skill: `/foundation-models`** → `swift-engineering:foundation-models`
  Implementation patterns: summarization, extraction, classification features. @Generable schema design, session management.

- **Doc: `foundation-models-ai.md`** → `.claude/docs/ios-development/foundation-models-ai.md`
  Architecture overview: model capabilities, token limits, what it can and can't do. Guardrails and safety.

API lookup:
```bash
cd ~/Source/neo-research && .venv/bin/python3 scripts/knowledge-cli.py search "LanguageModelSession" --project ml-ai --top-k 5
```

## CoreML & Vision (visionOS + iOS)

Custom models and computer vision:

- **Doc: `coreml-vision-recognition.md`** → `.claude/docs/visionos-development/coreml-vision-recognition.md`
  CoreML pipeline (model conversion → optimization → deployment), Vision framework requests, camera access tiers on visionOS.

API lookup: `cd ~/Source/neo-research && .venv/bin/python3 scripts/knowledge-cli.py search "VNRequest" --project ml-ai --top-k 3`

## Cross-References

- visionOS ML features (object detection, hand classification) → [[spatial.md]]
- Concurrency: ML inference uses async/await → [[concurrency.md]]
- Testing ML outputs → [[architecture.md]] testing section
