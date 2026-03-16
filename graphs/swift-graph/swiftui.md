---
description: "SwiftUI patterns for iOS 17-26: @Observable, Liquid Glass, NavigationStack, ViewThatFits, gesture composition, UIKit interop"
keywords: [swiftui, observable, liquid-glass, navigation, gestures, ios26, viewthatfits]
---

# SwiftUI

Covers view layer patterns from iOS 17 through iOS 26. Split between foundational patterns (any iOS version) and iOS 26 specifics (Liquid Glass, native WebView).

## iOS 26 — New APIs

Use when building for iOS 26 or adopting Liquid Glass:

- **Skill: `/ios26-swiftui`** → `.claude/commands/ios26-swiftui.md`
  Liquid Glass materials, GlassEffectContainer, native WebView, rich TextEditor, toolbar changes, @Observable migration from ObservableObject.

- **Doc: `swiftui-modern.md`** → `.claude/docs/ios-development/swiftui-modern.md`
  Broader iOS 17-26 SwiftUI patterns including @Observable, NavigationStack, ViewThatFits.

For exact API signatures:
```bash
cd ~/Source/neo-research && .venv/bin/python3 scripts/knowledge-cli.py search "GlassEffectContainer" --project swiftui --top-k 5
```

## Core Patterns (iOS 17+)

- **Skill: `/swiftui-patterns`** → `swift-engineering:swiftui-patterns`
  @Observable/@Bindable, MVVM architecture, NavigationStack, lazy loading, UIKit interop, accessibility (VoiceOver/Dynamic Type), async operations (.task/.refreshable).

- **Skill: `/swiftui-advanced`** → `swift-engineering:swiftui-advanced`
  Gesture composition (simultaneous, sequenced, exclusive), adaptive layouts (ViewThatFits, AnyLayout, size classes), State-as-Bridge pattern.

- **Plugin: `swiftui-expert`** → `swiftui-expert:swiftui-expert-skill` (AvdLee, v2.0.1)
  Agent-only. Auto-triggers on SwiftUI code review/writing tasks. 14 reference files covering state management, view structure, performance, list patterns, layout, accessibility, animations (basic/transitions/keyframe), sheet/navigation, scroll patterns, image optimization, and Liquid Glass. Has a deprecated→modern API transition guide covering iOS 15 through 26. Complements the above skills with deeper reference material and a behavioral ruleset (no architecture mandates from the view layer).

- **Agent: `swiftui-specialist`** → `swift-engineering:swiftui-specialist`
  Implement SwiftUI views following Apple HIG. Use after core logic is done.

## Architecture Integration

SwiftUI views need a state management layer. Choose based on complexity:

- Simple: @State/@Binding → vanilla SwiftUI (see [[architecture.md]])
- Medium: @Observable view models → MVVM (see [[architecture.md]])
- Complex: Store observation → TCA (see [[architecture.md]])

## Accessibility & HIG

For the full HIG design layer (all platforms, components, patterns, technologies), see [[hig-design.md]]. Below are the implementation-level skills:

- **Skill: `/ios-hig`** → `swift-engineering:ios-hig`
  VoiceOver, Dynamic Type, dark mode, touch targets, animation/haptic feedback, permission requests.

- **Skill: `/haptics`** → `swift-engineering:haptics`
  UIFeedbackGenerator, CHHapticEngine patterns for confirmations, errors, custom patterns.

- **Doc: `accessibility-localization.md`** → `.claude/docs/ios-development/accessibility-localization.md`
  VoiceOver implementation, Dynamic Type, String Catalogs, RTL layout.

## Haptic Feedback

- **Skill: `/haptics`** → `swift-engineering:haptics`
  UIFeedbackGenerator for quick confirmations/errors, CHHapticEngine for custom tactile patterns. Use for button presses, toggles, purchase confirmations, error notifications.

## Localization

- **Skill: `/localization`** → `swift-engineering:localization`
  String Catalogs, pluralization, LocalizedStringKey, RTL support.

## visionOS SwiftUI

SwiftUI on visionOS has spatial extensions (RealityView, Model3D, ornaments). See [[spatial.md]] for the full spatial computing MOC.
