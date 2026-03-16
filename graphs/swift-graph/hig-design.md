---
description: "Apple Human Interface Guidelines: design guidance (hig-doctor) + implementation (ios-hig). All platforms."
keywords: [hig, accessibility, design, dark-mode, typography, color, touch-targets, dynamic-type, visionos-hig]
---

# Human Interface Guidelines

Two complementary layers: **hig-doctor** (what Apple's HIG says — design decisions, component selection, platform conventions) and **ios-hig** (how to implement it — SwiftUI/UIKit code patterns).

## Design Layer — hig-doctor (apple-hig-skills plugin)

14 skills, 156 reference files. Plugin: `apple-hig-skills`. Triggers automatically on HIG/design questions.

### Foundations

- **Skill: `hig-foundations`** (auto-trigger)
  Color, typography, dark mode, accessibility, SF Symbols, app icons, branding, layout, materials, motion, privacy, RTL, spatial layout, writing style, inclusion, images, immersive experiences. 18 reference files.

### Platforms

- **Skill: `hig-platforms`** (auto-trigger)
  Platform-specific conventions: iOS (touch-first), iPadOS (Split View, Stage Manager), macOS (pointer+keyboard), tvOS (focus-based), visionOS (eye tracking + pinch, spatial), watchOS (glanceable), Games. 7 reference files.

### Components (8 skills)

| Skill | Covers | Refs |
|-------|--------|------|
| `hig-components-controls` | Buttons, toggles, segmented, sliders, pickers, steppers, text fields, combo boxes, gauges | 14 |
| `hig-components-layout` | Sidebars, columns, split views, tab bars, scroll views, windows, panels, lists, ornaments | 12 |
| `hig-components-menus` | Menu bar, context menus, pop-up/pull-down buttons, toolbars, action buttons, dock menus | 11 |
| `hig-components-content` | Charts, collections, image views, color wells, web views, activity views, lockups | 8 |
| `hig-components-system` | Widgets, Live Activities, notifications, complications, quick actions, top shelf, App Clips, App Shortcuts | 9 |
| `hig-components-dialogs` | Alerts, action sheets, popovers, sheets, digit entry | 5 |
| `hig-components-search` | Search fields, page controls, path controls | 3 |
| `hig-components-status` | Progress indicators, status bar, activity rings | 3 |

### Patterns

- **Skill: `hig-patterns`** (auto-trigger)
  Modality, feedback, undo, launching, onboarding, drag-and-drop, notifications, searching, haptics, printing, ratings, settings, workouts, collaboration. 25 reference files.

### Inputs

- **Skill: `hig-inputs`** (auto-trigger)
  Multi-touch, Apple Pencil, keyboard shortcuts, game controllers, pointer/trackpad, Digital Crown, eye tracking, focus system, Siri Remote, sensors. 13 reference files.

### Technologies

- **Skill: `hig-technologies`** (auto-trigger)
  Siri, Apple Pay, HealthKit, HomeKit, ARKit, CoreML, generative AI, Sign in with Apple, iCloud, SharePlay, CarPlay, Game Center, VoiceOver, Wallet, NFC, Maps, always-on display. 28 reference files.

### Project Context

- **Skill: `hig-project-context`** (auto-trigger)
  Meta-skill that creates `.claude/apple-design-context.md` by auto-discovering platform targets, tech stack, and design system from project files. Other HIG skills read this file to skip repetitive questions.

## Implementation Layer — swift-engineering

Code-level HIG implementation. These tell you *how to write the code*:

- **Skill: `/ios-hig`** → `swift-engineering:ios-hig`
  7 reference files: accessibility (VoiceOver code), visual-design (semantic colors API), interaction (44pt targets, NavigationStack), content (Dynamic Type modifiers, empty states), feedback (haptics code, ProgressView), performance-platform (LazyVStack, SF Symbols), privacy-permissions (permission request Swift patterns).

- **Skill: `/haptics`** → `swift-engineering:haptics`
  UIFeedbackGenerator, CHHapticEngine, Causality/Harmony/Utility principles.

- **Plugin: `swiftui-expert`** → `swiftui-expert:swiftui-expert-skill`
  `accessibility-patterns.md` reference covers: @ScaledMetric, accessibilityAddTraits, accessibilityRepresentation, accessibilityLabeledPair.

- **Doc: `accessibility-localization.md`** → `.claude/docs/ios-development/accessibility-localization.md`
  VoiceOver, @AccessibilityFocusState, String Catalogs, RTL, audit checklist.

## When to Use Which

| Question | Use |
|----------|-----|
| "Should I use a sheet or popover here?" | hig-doctor → `hig-components-dialogs` |
| "How do I present a sheet in SwiftUI?" | ios-hig → `interaction.md` |
| "What's the visionOS ergonomic zone?" | hig-doctor → `hig-platforms` / `hig-foundations/spatial-layout.md` |
| "How do I implement Dynamic Type?" | ios-hig → `content.md` + swiftui-expert → `accessibility-patterns.md` |
| "Is my color contrast okay?" | hig-doctor → `hig-foundations/color.md` (ratios) + ios-hig → `visual-design.md` (semantic colors) |
| "What haptic should I use for a purchase?" | hig-doctor → `hig-patterns` + `/haptics` skill (code) |
| "How do I design for CarPlay?" | hig-doctor → `hig-technologies/carplay.md` |
| "How do I request camera permission?" | ios-hig → `privacy-permissions.md` |

## Cross-References

- SwiftUI implementation patterns → [[swiftui.md]]
- visionOS spatial design → [[spatial.md]]
- App Store review (HIG compliance checks) → [[app-store-flow.md]]
- Logging for accessibility debugging → `/swift-logging`
