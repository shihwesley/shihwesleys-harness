---
description: "Hub MOC for iOS/visionOS/Swift development. Entry point for all skill graph navigation."
updated: 2026-03-03
domains: [ios, visionos, swift, swiftui, tca, realitykit, arkit, hig]
---

# Swift Skill Graph

Navigate by reading this index, then following the MOC that matches your task. Each MOC links to specific skills, docs, and API references. Read MOCs for orientation; read linked files only when you need to act.

## Architecture & State Management

- [[architecture.md]] — TCA vs MVVM vs vanilla SwiftUI. Decision framework for project setup, reducer composition, @Observable patterns, state management trade-offs.

## SwiftUI

- [[swiftui.md]] — iOS 17-26 SwiftUI patterns. @Observable, Liquid Glass, NavigationStack, ViewThatFits, gesture composition, UIKit interop, adaptive layouts.

## Spatial Computing (visionOS)

- [[spatial.md]] — visionOS scene types, RealityKit ECS, ARKit providers, hand tracking, world anchors, spatial audio, ShaderGraph, visionOS 26 updates, Unreal Engine bridge.

## Swift Language & Concurrency

- [[concurrency.md]] — Swift 6 strict concurrency, actors, async/await, Sendable, TaskGroup, structured concurrency, migration from completion handlers.

## Data & Persistence

- [[persistence.md]] — SwiftData, Core Data, GRDB, SQLiteData, CloudKit sync. Schema design, migrations, reactive queries.

## On-Device AI & ML

- [[ai-ml.md]] — Apple Foundation Models (@Generable, @Guide, tool calling), CoreML pipeline, Vision framework, on-device inference patterns.

## Testing

- [[testing.md]] — Swift Testing framework, TCA TestStore, UI testing, snapshot testing, performance testing, test organization patterns, coverage.

## Human Interface Guidelines (Design Layer)

- [[hig-design.md]] — Apple HIG across all platforms. Two layers: **design guidance** (hig-doctor plugin — 14 skills, 156 reference files covering foundations, platforms, components, patterns, inputs, technologies) and **implementation** (swift-engineering:ios-hig — SwiftUI/UIKit code patterns). Use hig-doctor for "what should I do?" and ios-hig for "how do I code it?"

## App Store Submission Flow

- [[app-store-flow.md]] — The full path from "code is done" to "app is live." Required assets, privacy compliance, review guidelines, metadata, screenshots, signing, TestFlight, release management.

## Distribution & CI/CD

- [[distribution.md]] — StoreKit, CI/CD pipelines, Xcode Cloud, GitHub Actions, ASC CLI automation.

## Logging & Diagnostics

- [[logging.md]] — Unified Logging (os.Logger), swift-log, OSSignposter, OSLogStore, privacy annotations, Console.app debugging.

## Tooling & Build

- [[tooling.md]] — xcodebuild, simctl, xcbeautify, xctrace, ASC CLI, Apple API knowledge store. Terminal-first development workflows.

---

## Navigation Protocol

- [[traverse.md]] — Full traversal protocol for agents. How to navigate MOCs with TLDR-integrated progressive disclosure, cost budgets, and rules.

1. Read this index (you're here) — pick the MOC(s) matching your task
2. Read the MOC — pick the specific skills/docs you need
3. Read those files — now you have the knowledge to act
4. For API signatures: `cd ~/Source/neo-research && .venv/bin/python3 scripts/knowledge-cli.py search "<term>" --project <store>` (stores: `spatial-computing`, `swiftui`, `ml-ai`, `foundation-core`, `networking`, `security-auth`, `media-audio`, `uikit-appkit`, `metal`, `graphics`, `hardware-sensors`, `health-home-data`, `location-maps-weather`)
5. For agent selection and dispatch routing: see `.claude/skills/orchestrator/skill-registry.json`
6. For the full orchestration pipeline: see `.claude/docs/agent-infra-graph/orchestration.md`

Do not load all MOCs. Do not read files you won't use. The graph saves tokens by being selective.
