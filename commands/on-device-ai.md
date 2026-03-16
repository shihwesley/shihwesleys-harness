---
name: on-device-ai
description: "Use when implementing on-device AI with Apple's Foundation Models framework (iOS 26+). Covers @Generable, @Guide, tool calling, streaming, and availability checks."
argument-hint: "[AI feature to implement]"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
---

# On-Device AI with Foundation Models

Implement Apple's Foundation Models framework for on-device AI inference.

## When to Use
- Adding AI-powered features (summarization, extraction, classification)
- Building structured output with @Generable
- Integrating tool calling for dynamic data
- Streaming AI responses in SwiftUI

## Requirements Check

Before implementing:
- [ ] iOS 26+ deployment target
- [ ] Physical device for testing (no simulator)
- [ ] Apple Intelligence enabled on device
- [ ] iPhone 15 Pro+ or Apple Silicon Mac/iPad

## Implementation Workflow

### 1. Availability Gate

```swift
switch SystemLanguageModel().availability {
case .available: showAIFeatures()
case .unavailable(.appleIntelligenceNotEnabled): promptSettings()
case .unavailable(.deviceNotEligible): showFallback()
}
```

### 2. Define @Generable Schema

Properties generated top-to-bottom. Put dependent fields last.

```swift
@Generable struct Analysis {
    @Guide(description: "Main findings") let findings: [String]
    @Guide(.range(1...10)) let confidence: Int
    @Guide(description: "Summary based on findings") let summary: String  // last
}
```

**Constraints**: `.range()`, `.count()`, `.minimumCount()`, `.maximumCount()`, `.anyOf()`, `.pattern()`

### 3. Generate Response

```swift
let session = LanguageModelSession { "You are a helpful assistant." }
let result = try await session.respond(to: prompt, generating: Analysis.self)
// result.content is type Analysis
```

### 4. Streaming (for UI)

```swift
for try await partial in session.streamResponse(to: prompt, generating: Analysis.self) {
    self.current = partial  // PartiallyGenerated<Analysis>, all optional
}
```

### 5. Tool Calling (for external data)

```swift
struct WeatherTool: Tool {
    @Generable struct Arguments { let location: String }
    nonisolated func call(arguments: Arguments) async throws -> ToolOutput { ... }
}
let session = LanguageModelSession(tools: [WeatherTool()])
```

## Performance Tips

- `session.prewarm()` on view appear
- Minimize @Generable properties (all generated regardless of use)
- 4096 token limit (input + output combined)
- Use enums for classification: `@Generable enum Sentiment { case positive, negative, neutral }`

## SwiftData Persistence

Map @Generable structs → @Model classes:
```swift
@Model class AnalysisModel {
    init(from analysis: Analysis) { ... }
}
```

## Common Patterns

- **Summarization**: @Generable with mainPoints array + keyTakeaway
- **Entity extraction**: Struct with people/organizations/locations arrays
- **Classification**: @Generable enum with case per category
- **Quiz generation**: Struct with question, choices (.count(4)), correctAnswer, explanation

## Knowledge Docs
Reference: `.claude/docs/ios-development/foundation-models-ai.md`
