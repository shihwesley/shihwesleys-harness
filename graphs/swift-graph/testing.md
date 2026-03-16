---
description: "Testing strategy and frameworks: Swift Testing, TCA TestStore, UI testing, snapshot testing, performance testing, coverage, test organization"
keywords: [testing, swift-testing, teststore, xcuitest, snapshot, coverage, tdd]
---

# Testing

Covers the full testing stack from unit tests to UI tests to performance validation. Split by framework and purpose — pick what matches your testing need.

## Swift Testing Framework (iOS 17+)

The modern replacement for XCTest. Use by default for all new tests:

- **Skill: `/swift-testing`** → `swift-engineering:swift-testing`
  @Test macro, #expect assertions, parameterized tests, traits, test suites. Migration path from XCTest.

- **Plugin: `swift-testing-expert`** → `swift-testing-expert:swift-testing-expert` (AvdLee, v1.0.0)
  Agent-only. Auto-triggers when writing new tests, modernizing XCTest suites, debugging flaky tests, or improving test quality. 10 reference files: fundamentals (@Test, suites, naming), expectations (#expect, #require, throw validation), traits/tags (bug linking, test-plan filtering), parameterized testing (single/multi-argument), parallelization (.serialized), performance/best practices (flaky test prevention), async testing (callback bridging, event-stream verification), XCTest migration workflow, Xcode navigator/report diagnostics. Behavioral rule: only import `Testing` in test targets, never in app/library targets. Complements `/swift-testing` with deeper reference material and a structured triage template.

- **Doc: `swift-testing.md`** → `.claude/docs/ios-development/swift-testing.md`
  Patterns, what to test vs what the type system guarantees, behavior-driven testing.

## TCA Testing

TCA has its own testing story through TestStore:

- **Skill: `/composable-architecture`** → `swift-engineering:composable-architecture`
  TestStore for reducer testing, exhaustive assertion checking, dependency overrides, non-exhaustive testing for integration tests.

Test a TCA feature by sending actions and asserting state mutations. TestStore fails if any unexpected state change goes unasserted — this is the strictest testing model in iOS.

## UI Testing (XCUITest)

For end-to-end flows that need to verify the actual UI:

- Xcode's XCUITest framework — launch app, tap elements, assert labels
- Accessibility identifiers are your test hooks (set `.accessibilityIdentifier` on views)
- Slow and flaky compared to unit tests — use sparingly for critical user flows (onboarding, purchase, auth)

Run from terminal: `xcodebuild test -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 16'` (see [[tooling.md]])

## Snapshot Testing

Visual regression testing — capture view screenshots, compare against baselines:

- Point-Free's `swift-snapshot-testing` library
- Works with SwiftUI views via `assertSnapshot(of: MyView(), as: .image)`
- Good for: design system components, layout validation across device sizes
- Bad for: views with dynamic content, animations, dark/light mode (generates too many baselines)

## Performance Testing

- **Doc: `performance-debugging.md`** → `.claude/docs/ios-development/performance-debugging.md`
  Xcode Instruments, SwiftUI Instrument, Power Profiler, TSan for data race detection.

- XCTest `measure {}` blocks for micro-benchmarks
- Instruments traces for macro performance (app launch, scroll hitches, memory)
- visionOS: triangle budget validation, thermal throttling tests (see [[spatial.md]])

## Test Organization

Rules that keep a test suite useful:

- **Test behavior, not implementation.** Only call public API from tests. Don't test private methods.
- **Don't test what the type system guarantees.** If a property is non-optional, don't test that it's not nil.
- **One assertion concept per test.** Multiple `#expect` calls are fine if they verify the same behavior.
- **Name tests as sentences:** `@Test("User can complete purchase with valid card")`
- **Factories over fixtures.** Build test data inline or with factory functions, not shared fixtures that create hidden coupling.

## Agents

- **Agent: `swift-test-creator`** → `swift-engineering:swift-test-creator`
  Writes unit and integration tests using Swift Testing. Spawn after implementation is complete.

- **Agent: `swift-code-reviewer`** → `swift-engineering:swift-code-reviewer`
  Reviews code for quality, security, performance, and HIG compliance — includes test coverage gaps in review output.

## Cross-References

- Architecture determines testing approach → [[architecture.md]] (TCA = TestStore, MVVM = @Test on view models, vanilla = @Test on views)
- Concurrency testing (actors, async) → [[concurrency.md]]
- Build and run tests from terminal → [[tooling.md]]
