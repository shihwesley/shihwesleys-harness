---
name: ios-architecture-guide
description: "Use when starting a new iOS project or choosing architecture (TCA vs MVVM vs vanilla). Guides architecture decisions based on team size, complexity, and requirements."
argument-hint: "[project description or requirements]"
allowed-tools: ["Read", "Glob", "Grep", "WebSearch", "AskUserQuestion"]
---

# iOS Architecture Guide

Help the user choose and set up the right architecture for their iOS project.

## When to Use
- Starting a new iOS project
- Evaluating TCA vs MVVM vs vanilla SwiftUI
- Refactoring existing architecture
- Adding state management to a growing app

## Quick Decision Tree

Ask these questions (or infer from context):

1. **Team size?** Solo → vanilla or MVVM. 2-3 → MVVM. 4+ → TCA.
2. **State complexity?** Simple data display → vanilla. Forms/CRUD → MVVM. Cross-feature sync → TCA.
3. **Testing requirements?** Nice-to-have → MVVM. Mandatory → TCA.
4. **iCloud sync needed?** Yes → SwiftData (MVVM integrates cleanest). No → any.
5. **iOS minimum target?** iOS 17+ required for @Observable.

## Architecture Patterns

### TCA
- @Reducer macro, Store, Effect
- State/Action/Dependency triad
- TestStore for exhaustive testing
- Tree-based or stack-based navigation
- Use when: large teams, complex state, testability is critical

### MVVM + @Observable (iOS 17+)
- @Observable class as ViewModel
- @State (not @StateObject) in views
- @Bindable for two-way bindings
- @Environment for dependency injection
- Use when: balanced needs, SwiftData integration

### Vanilla SwiftUI
- @State as implicit ViewModel
- Direct model access
- No formal architecture
- Use when: prototypes, simple apps, learning

## Setup Checklist

For the chosen architecture:

### TCA Setup
1. Add `swift-composable-architecture` via SPM
2. Create feature folder: State + Action + Reducer
3. Set up dependency container
4. Wire Store to SwiftUI views
5. Write first TestStore test

### MVVM Setup
1. Create @Observable ViewModel per screen
2. Define Repository/Service layer
3. Use @Environment for DI
4. Wire with @State in parent view
5. Write unit tests for ViewModel

### Vanilla Setup
1. Define model types
2. Use @State in views
3. Pass data via @Binding
4. Use @Environment for shared state

## Knowledge Docs
Reference: `.claude/docs/ios-development/app-architecture.md`
