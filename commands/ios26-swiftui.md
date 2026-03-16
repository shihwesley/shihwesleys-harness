---
name: ios26-swiftui
description: "Use when implementing iOS 26 SwiftUI features: Liquid Glass, native WebView, rich TextEditor, toolbar/search changes, or migrating to @Observable."
argument-hint: "[feature or component to implement]"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebSearch"]
---

# iOS 26 SwiftUI Patterns

Implement modern SwiftUI features from iOS 17 through iOS 26.

## When to Use
- Adding Liquid Glass materials to views
- Embedding web content with native WebView
- Building rich text editing with AttributedString
- Migrating from ObservableObject to @Observable
- Implementing NavigationStack with state restoration
- Using ViewThatFits for adaptive layouts

## Liquid Glass

Three material variants: `.regular`, `.clear`, `.identity`.

```swift
// Basic
.glassEffect(.regular.tint(.blue).interactive())

// Morphing: same container + glassEffectID + shared namespace
GlassEffectContainer(spacing: 20) {
    ForEach(items) { item in
        view.glassEffect(.regular)
            .glassEffectID(item.id, in: namespace)
    }
}
```

Auto-adapts for Reduced Transparency, Increased Contrast.

## WebView (iOS 26)

```swift
WebView(url: URL(string: "https://example.com"))

// Advanced: WebPage for JS execution, progress, title
@State private var page = WebPage()
WebView(page)
    .onAppear { page.load(URLRequest(url: url)) }
```

## @Observable Migration

| Before | After |
|--------|-------|
| ObservableObject | @Observable |
| @Published var x | var x |
| @StateObject | @State |
| @ObservedObject | @Bindable (or plain let) |
| @EnvironmentObject | @Environment |

## NavigationStack + State Restoration

Use NavigationPath + SceneStorage for persistence. CodableRepresentation for serialization.

## Implementation Workflow

1. Check minimum deployment target (iOS 17 for @Observable, iOS 26 for Liquid Glass/WebView)
2. Read existing code for current patterns
3. Apply the appropriate pattern from above
4. Test with VoiceOver and Dynamic Type
5. Verify Liquid Glass accessibility adaptations if used

## Knowledge Docs
Reference: `.claude/docs/ios-development/swiftui-modern.md`
