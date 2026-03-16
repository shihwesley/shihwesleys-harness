---
description: "Data persistence: SwiftData, Core Data, GRDB raw SQL, SQLiteData macros, CloudKit sync, schema migrations"
keywords: [swiftdata, coredata, grdb, sqlitedata, cloudkit, sqlite, migrations]
---

# Data & Persistence

Choose based on complexity: SwiftData for simple models, GRDB for complex queries, SQLiteData for macro-based convenience, Core Data for legacy projects needing CloudKit.

## SwiftData

Built into iOS 17+. Best for apps with straightforward model graphs:

- **Doc: `data-persistence.md`** → `.claude/docs/ios-development/data-persistence.md`
  SwiftData vs Core Data vs GRDB comparison, SwiftData usage patterns, migration strategies.

## GRDB — Raw SQL with Type Safety

For complex joins, window functions, and reactive queries:

- **Skill: `/grdb`** → `swift-engineering:grdb`
  Raw SQL with GRDB, complex joins across 4+ tables, window functions, ValueObservation for reactive queries. Direct SQLite access with type-safe query builders.

## SQLiteData — Macro-Based Persistence

For projects using the SQLiteData library:

- **Skill: `/sqlite-data`** → `swift-engineering:sqlite-data`
  @Table, @FetchAll, @FetchOne macros. SQLite persistence, queries, writes, migrations, CloudKit private database sync.

## Core Data

For legacy or CloudKit-synced projects still on Core Data:

- **Plugin: `core-data-expert`** → `core-data-expert:core-data-expert` (AvdLee, v1.0.0)
  Agent-only. Auto-triggers on Core Data stack setup, fetch requests, NSFetchedResultsController, save/merge conflicts, threading, batch operations, persistent history tracking, model configuration, migrations (lightweight, staged iOS 17+, deferred), NSPersistentCloudKitContainer/CloudKit sync, performance tuning, and testing with in-memory stores. 15 reference files. Behavioral rule: never pass NSManagedObject instances across contexts. Includes a project audit checklist for discovering an existing project's Core Data setup, and a common-errors→fix mapping. Good complement to the swift-concurrency plugin's Core Data concurrency reference.

## Cross-References

- Architecture choices affect persistence layer → [[architecture.md]] (TCA uses dependencies for DB access; MVVM uses view model injection)
- Concurrency with database access → [[concurrency.md]] (actor isolation for write queues)
- Core Data + Swift Concurrency → `swift-concurrency` plugin has a dedicated `core-data.md` reference
