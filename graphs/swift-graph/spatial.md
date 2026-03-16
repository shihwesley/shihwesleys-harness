---
description: "visionOS spatial computing: scene types, RealityKit ECS, ARKit providers, hand tracking, world anchors, spatial audio, ShaderGraph, visionOS 26"
keywords: [visionos, realitykit, arkit, hand-tracking, world-anchors, immersive-space, ecs, shadergraph]
---

# Spatial Computing (visionOS)

Covers the full visionOS stack from window management to immersive experiences. The platform layers: SwiftUI (scenes/UI) → RealityKit (3D content) → ARKit (spatial understanding) → CoreML/Vision (perception).

## Scene Types & Fundamentals

Start here for any visionOS project:

- **Skill: `/visionos-spatial`** → `.claude/commands/visionos-spatial.md`
  Windows, volumes, immersive spaces, RealityView, Model3D, ARKit provider setup, input handling (gesture → entity targeting), ornaments.

- **Doc: `visionos-fundamentals.md`** → `.claude/docs/visionos-development/visionos-fundamentals.md`
  Scene lifecycle, progressive immersion model, coordinate spaces, placement rules.

- **Doc: `overview.md`** → `.claude/docs/visionos-development/overview.md`
  Platform architecture, framework roles, input model. Hub doc — read for orientation.

## RealityKit & 3D Pipeline

For 3D content, ECS patterns, and asset optimization:

- **Skill: `/realitykit-ecs`** → `.claude/commands/realitykit-ecs.md`
  Entities, components, systems, ShaderGraph materials, animations, spatial audio, USDZ workflow, triangle budgets.

- **Doc: `realitykit-3d-pipeline.md`** → `.claude/docs/visionos-development/realitykit-3d-pipeline.md`
  ECS deep dive, asset optimization targets, ShaderGraph node reference, spatial audio setup.

API lookup:
```bash
cd ~/Source/neo-research && .venv/bin/python3 scripts/knowledge-cli.py search "RealityKit Entity" --project spatial-computing --top-k 5
```

## ARKit — Spatial Understanding

Hand tracking, plane detection, world anchors, scene reconstruction:

- **Doc: `arkit-spatial.md`** → `.claude/docs/visionos-development/arkit-spatial.md`
  Provider setup (HandTrackingProvider, PlaneDetectionProvider, WorldTrackingProvider), anchor types, permissions.

- **Doc: `world-anchoring-deep-dive.md`** → `.claude/docs/visionos-development/world-anchoring-deep-dive.md`
  SLAM/VIO internals, anchor persistence, relocalization, coordinate math, drift compensation, failure modes. Read this when debugging spatial tracking issues.

API lookup: `cd ~/Source/neo-research && .venv/bin/python3 scripts/knowledge-cli.py search "HandTrackingProvider" --project spatial-computing --top-k 3`

## ML & Computer Vision on visionOS

Object detection, hand gesture classification, scene understanding:

- **Doc: `coreml-vision-recognition.md`** → `.claude/docs/visionos-development/coreml-vision-recognition.md`
  Camera access tiers (consumer vs enterprise), CoreML pipeline, Vision framework integration.

For broader AI/ML patterns see [[ai-ml.md]].

## visionOS 26 Updates

- **Doc: `visionos-26-whats-new.md`** → `.claude/docs/visionos-development/visionos-26-whats-new.md`
  CoordinateSpace3D, 90Hz hand tracking, stereo camera, SharePlay shared anchors, SurfaceAlignment, bottom/world-aligned volumes.

## Unreal Engine Bridge

For full-immersion rendering when RealityKit isn't enough:

- **Doc: `unreal-visionos-bridge.md`** → `.claude/docs/visionos-development/unreal-visionos-bridge.md`
  UE5 experimental visionOS support, Metal rendering, CompositorServices, decision: RealityKit vs UE.

## Hardware & Platform Internals

- **Doc: `vision-pro-hardware-internals.md`** → `.claude/docs/visionos-development/vision-pro-hardware-internals.md`
  R1+M2 chip roles, sensor array, micro-OLED, foveated rendering, passthrough pipeline. Read when optimizing for hardware constraints.

## Accessibility in Spatial

- **Doc: `spatial-accessibility-hig.md`** → `.claude/docs/visionos-development/spatial-accessibility-hig.md`
  AccessibilityComponent, VoiceOver in 3D, Dwell Control, ergonomic placement distances, HIG spatial design principles.

## Agents

- **Agent: `visionos-specialist`** → `.claude/agents/visionos-specialist.md`
  Autonomous visionOS work. Reads the graph, builds with RealityKit/ARKit/CoreML.

- **Agent: `ios-specialist`** → `.claude/agents/ios-specialist.md`
  For shared iOS/visionOS work (SwiftUI views that run on both platforms).

## Cross-References

- SwiftUI view patterns that work on visionOS → [[swiftui.md]]
- Architecture choices (TCA works on visionOS) → [[architecture.md]]
- Swift concurrency (ARKit providers use async sequences) → [[concurrency.md]]
