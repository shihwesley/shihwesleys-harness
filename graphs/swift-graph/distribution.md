---
description: "App Store submission, privacy manifests, TestFlight, signing, CI/CD pipelines, Xcode Cloud, GitHub Actions"
keywords: [app-store, testflight, privacy-manifest, signing, cicd, xcode-cloud, fastlane]
---

# Distribution & CI/CD

From local build to App Store. Covers submission requirements, privacy compliance, automated pipelines, and TestFlight management.

## App Store Submission

For the full submission process (required assets, paperwork, review flow), see [[app-store-flow.md]].

- **Skill: `/app-store-submit`** → `.claude/commands/app-store-submit.md`
  Privacy manifests (PrivacyInfo.xcprivacy), compliance requirements, TestFlight setup, rejection prevention checklist. iOS 26 SDK deadline: Apr 28, 2026.

## App Store Connect Automation

- **Skill: `/asc-automation`** → `.claude/commands/asc-automation.md`
  `asc` CLI for build uploads, TestFlight group management, metadata sync, signing asset management, submission health checks.

## In-App Purchases & StoreKit

- **Skill: `/storekit`** → `swift-engineering:storekit`
  StoreKit 2 subscriptions, consumables, non-consumables, transaction handling. Testing-first workflow with `.storekit` configuration files, StoreManager architecture, transaction verification.

## CI/CD & Build Tooling

- **Doc: `cicd-build-tooling.md`** → `.claude/docs/ios-development/cicd-build-tooling.md`
  Xcode Cloud configuration, GitHub Actions for iOS, fastlane integration, SPM dependency management, code signing for CI.

Terminal build commands connect to [[tooling.md]] for xcodebuild specifics.

## Cross-References

- Privacy manifests affect what APIs you can use → check specific framework docs in [[swiftui.md]] or [[spatial.md]]
- Signing and entitlements for visionOS apps → [[spatial.md]] (visionOS has additional entitlements for ARKit features)
