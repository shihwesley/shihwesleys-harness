---
description: "Swift 6 strict concurrency: actors, async/await, Sendable, TaskGroup, structured concurrency, migration from completion handlers"
keywords: [swift6, concurrency, actors, async-await, sendable, taskgroup, structured-concurrency]
---

# Swift Language & Concurrency

Swift 6 strict concurrency is the biggest language change since Swift 3. Most build errors in modern Swift projects trace back to Sendable conformance or actor isolation.

## Strict Concurrency & async/await

- **Skill: `/modern-swift`** → `swift-engineering:modern-swift`
  async/await patterns, strict concurrency enablement, fixing Sendable errors, migrating from completion handlers, actor isolation, Task/TaskGroup for structured concurrency.

- **Plugin: `swift-concurrency`** → `swift-concurrency:swift-concurrency` (AvdLee, v1.1.0)
  Agent-only. Auto-triggers on async/await, actor isolation, Sendable errors, Swift 6 migration, data race debugging, and concurrency lint warnings. 15 reference files: async/await basics, tasks, threading, actors, Sendable, AsyncSequence, async algorithms, memory management, performance, Core Data concurrency, migration from callbacks, testing async code, linting rules, glossary. Includes a Quick Fix Playbook mapping compiler diagnostics to minimal fixes and a validation loop (build → fix → rebuild → test). Checks Swift language mode from Package.swift/.pbxproj before advising. Complements `/modern-swift` with deeper reference material and structured triage.

- **Doc: `swift6-concurrency.md`** → `.claude/docs/ios-development/swift6-concurrency.md`
  Comprehensive reference: actors, global actors (@MainActor), Sendable protocol, data race safety, structured vs unstructured concurrency, AsyncSequence.

## Diagnostics

When concurrency issues cause crashes or build failures:

- **Skill: `/swift-diagnostics`** → `swift-engineering:swift-diagnostics`
  Systematic debugging for build failures (Sendable errors, "expression not Sendable"), runtime crashes (actor re-entrancy), NavigationStack issues, memory problems.

## Networking (uses async/await)

Network code is where concurrency patterns matter most:

- **Skill: `/swift-networking`** → `swift-engineering:swift-networking`
  Network.framework (NWConnection, NetworkConnection), URLSession async/await, connection failure debugging, network transitions. iOS 26 structured concurrency networking patterns.

- **Doc: `networking-apis.md`** → `.claude/docs/ios-development/networking-apis.md`
  URLSession async patterns, App Intents, background tasks.

## Cross-References

- ARKit providers use AsyncSequence → see [[spatial.md]] for ARKit patterns
- TCA effects are async → see [[architecture.md]] for Effect patterns
- Testing async code with Swift Testing → see [[architecture.md]] testing section
