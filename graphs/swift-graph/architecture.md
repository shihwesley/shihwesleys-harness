---
description: "Architecture decisions for iOS/visionOS: TCA vs MVVM vs vanilla SwiftUI, reducer composition, dependency injection, navigation patterns"
keywords: [tca, mvvm, observable, composable-architecture, state-management, navigation]
---

# Architecture & State Management

Choosing architecture depends on team size, app complexity, and testing requirements. This MOC connects the decision framework to the implementation skills.

## Platform Overview

- **Doc: `overview.md`** → `.claude/docs/ios-development/overview.md`
  Platform state iOS 17-26, architecture landscape, core tech stack. Read for broad orientation before diving into a specific pattern.

## Decision Framework

Start here when setting up a new project or evaluating architecture for an existing one:

- **Skill: `/ios-architecture-guide`** → `.claude/commands/ios-architecture-guide.md`
  Decision tree: TCA vs MVVM vs vanilla. Covers team size thresholds, complexity indicators, SwiftData integration points.

## The Composable Architecture (TCA)

For apps that need predictable state, deep testing, and complex navigation:

- **Skill: `/composable-architecture`** → `swift-engineering:composable-architecture`
  @Reducer, Store, Effect, TestStore, reducer composition, dependency injection, TCA navigation (tree-based routing).

- **Agent: `tca-architect`** → `swift-engineering:tca-architect`
  Design TCA features — state shape, action taxonomy, dependency boundaries. Use before implementation.

- **Agent: `tca-engineer`** → `swift-engineering:tca-engineer`
  Implement TCA features — reducers, effects, bindings. Use after architecture is designed.

When TCA features need SwiftUI views, see [[swiftui.md]] for view patterns that compose with Store observation.

## MVVM + @Observable

For mid-complexity apps (iOS 17+) where TCA overhead isn't justified:

- **Doc: `app-architecture.md`** → `.claude/docs/ios-development/app-architecture.md`
  MVVM with @Observable, view model patterns, when to graduate to TCA.

- **Skill: `/swiftui-patterns`** → `swift-engineering:swiftui-patterns`
  @Observable/@Bindable, NavigationStack, lazy loading, .task/.refreshable. The view layer for MVVM.

## Vanilla SwiftUI

For simple apps, prototypes, or single-screen features:

- **Doc: `app-architecture.md`** → `.claude/docs/ios-development/app-architecture.md`
  Vanilla SwiftUI section: @State/@Binding, when it's enough, when to add structure.

## Navigation

Navigation patterns cut across all architectures:

- TCA navigation: tree-based routing via `swift-engineering:composable-architecture`
- SwiftUI navigation: NavigationStack/NavigationSplitView via [[swiftui.md]]
- visionOS navigation: scene management, volumes, immersive spaces via [[spatial.md]]

## Testing

Architecture determines your testing approach — TCA uses TestStore, MVVM tests view models with @Test, vanilla tests views directly. See [[testing.md]] for the full testing MOC.
