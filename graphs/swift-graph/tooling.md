---
description: "Build tools: xcodebuild, simctl, xcbeautify, xctrace, ASC CLI, Apple API knowledge store"
keywords: [xcodebuild, simctl, xcbeautify, xctrace, instruments, apple-docs, knowledge-store, profiling]
---

# Tooling & Build

Terminal-first development tools. Build, test, profile, and query docs without leaving the command line.

## Xcode Terminal Operations

- **Skill: `/xcodebuildmcp`** → `.claude/commands/xcodebuildmcp.md`
  MCP server wrapping xcodebuild, simctl, and LLDB. Preferred for build/test/run/debug — returns structured errors instead of raw logs. Covers simulator ops, LLDB debugging, UI automation, log capture. Falls back to raw CLI for archive/export/profiling.

- **Skill: `/xcode-terminal`** → `.claude/commands/xcode-terminal.md`
  Raw xcodebuild (build, test, archive, export), simctl, xctrace (Instruments from CLI), xcbeautify, asc CLI. Use for operations XcodeBuildMCP doesn't cover: archiving, IPA export, xctrace profiling, code signing, CI result bundles.

- **Doc: `xcode-terminal.md`** → `.claude/docs/ios-development/xcode-terminal.md`
  Quick reference for common xcodebuild invocations, simulator management, profiling commands.

## Performance Profiling

- **Doc: `performance-debugging.md`** → `.claude/docs/ios-development/performance-debugging.md`
  Xcode 26 Instruments, SwiftUI Instrument, Power Profiler, build caching, TSan for data race detection.

## Apple API Documentation

Local Apple docs indexed into a searchable knowledge store. No network needed.

**Search (primary):**
```bash
cd ~/Source/neo-research && .venv/bin/python3 scripts/knowledge-cli.py search "<API or concept>" --project <store> --top-k 5
```

**Domain stores** (pick the one matching your task):
| Store | Covers |
|-------|--------|
| `spatial-computing` | RealityKit, ARKit, SceneKit, visionOS frameworks |
| `swiftui` | SwiftUI, Observation, Charts, WidgetKit, AppIntents |
| `ml-ai` | Foundation Models, CoreML, Vision, NaturalLanguage, SoundAnalysis |
| `foundation-core` | Foundation, Swift standard library, Combine |
| `networking` | URLSession, Network.framework, MultipeerConnectivity |
| `security-auth` | CryptoKit, AuthenticationServices, LocalAuthentication |
| `media-audio` | AVFoundation, AVKit, MediaPlayer, AudioToolbox |
| `uikit-appkit` | UIKit, AppKit, TextKit |
| `metal` | Metal, MetalKit, MetalPerformanceShaders |
| `graphics` | Core Graphics, Core Animation, Core Image, SpriteKit |
| `hardware-sensors` | CoreBluetooth, CoreMotion, CoreLocation, NearbyInteraction |
| `health-home-data` | HealthKit, HomeKit, CoreData, SwiftData |
| `location-maps-weather` | MapKit, CoreLocation, WeatherKit |

Returns scored snippets with framework/heading attribution. Supports BM25 keyword matching; hybrid (BM25 + vector) when embedder is available.

**Source files:** `~/Source/DocSetQuery/docs/apple/` — 300+ framework `.md` files, pre-exported from Apple's documentation archive.

**Export a missing framework:**
```bash
cd ~/Source/DocSetQuery
python3 tools/docset_query.py export --root /documentation/<framework> --output docs/apple/<framework>.md --max-depth 3
python3 tools/docset_sanitize.py --input docs/apple/<framework>.md --in-place --toc-depth 2
python3 tools/docindex.py rebuild
```
After export, re-ingest into the appropriate domain store (see table above for which store the framework belongs to).

## Code Style

- **Skill: `/swift-style`** → `swift-engineering:swift-style`
  Naming conventions, formatting, organization, idiomatic patterns.

## Logging & Diagnostics

- **Skill: `/swift-logging`** → `.claude/commands/swift-logging.md`
  os.Logger (Unified Logging), apple/swift-log (cross-platform), OSSignposter (Instruments intervals), OSLogStore (log export). Privacy annotations, level guide, Console.app and `log` CLI debugging workflows.

  Reference files at `.claude/docs/swift-logging/`: `os-logger.md`, `swift-log.md`, `signposts.md`, `log-store.md`, `best-practices.md`.

## Cross-References

- Build commands for CI pipelines → [[distribution.md]]
- Profiling spatial apps (triangle budgets, thermal) → [[spatial.md]]
- Debugging build failures (SPM, "No such module") → [[concurrency.md]] diagnostics section
- visionOS debug loop with XcodeBuildMCP → [[spatial.md]]
- Logging decision framework (os.Logger vs swift-log) → `/swift-logging` skill
