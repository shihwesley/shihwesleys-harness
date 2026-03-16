---
description: "App Store submission process: required assets, privacy compliance, review guidelines, TestFlight, signing, metadata, and rejection prevention"
keywords: [app-store, submission, privacy-manifest, review-guidelines, testflight, signing, screenshots, metadata]
---

# App Store Submission Flow

The full path from "code is done" to "app is live." This is a process guide — follow it top to bottom when preparing a release.

## Phase 1 — Pre-Submission Checklist

Before you touch App Store Connect:

### Required Files in Your Xcode Project

- **PrivacyInfo.xcprivacy** — privacy manifest declaring all API usage reasons. Required since iOS 17, strictly enforced from iOS 26 SDK (deadline: Apr 28, 2026). Covers: file timestamp APIs, user defaults, disk space, active keyboards, system boot time.
- **Info.plist keys** — usage descriptions for every permission your app requests (camera, location, microphone, photos, health, contacts, etc.). Missing these = automatic rejection.
- **App icons** — 1024x1024 single icon (Xcode 15+ auto-generates all sizes). No alpha channel, no transparency.
- **Launch screen** — storyboard or SwiftUI launch screen. Static only — no code execution.

### Compliance & Legal

- **Export compliance** — if your app uses encryption (HTTPS counts), you need an export compliance declaration. Most apps select "Yes, uses exempt encryption" (standard HTTPS/TLS).
- **Age rating** — self-rated questionnaire in App Store Connect. Covers violence, profanity, gambling, medical content.
- **EULA** — default Apple EULA covers most apps. Custom EULA needed if you have subscriptions with special terms.
- **Privacy policy URL** — mandatory for all apps. Must be a publicly accessible URL, not a PDF or in-app page.
- **Terms of service URL** — required if you have subscriptions or accounts.

### Code-Level Requirements

- **Minimum deployment target** — Apple requires recent SDK. As of 2026, apps must be built with Xcode 16+ / iOS 17 SDK minimum for new submissions.
- **No private API usage** — Apple's static analyzer catches most violations. Common traps: UIKit internal selectors, undocumented entitlements.
- **No hardcoded test credentials** — review team will find them.
- **Crash-free on launch** — Apple tests cold launch on minimum supported device. If it crashes, automatic rejection.

**Skill: `/app-store-submit`** → `.claude/commands/app-store-submit.md`
Full details on privacy manifests, compliance, rejection prevention.

**Doc: `app-store-distribution.md`** → `.claude/docs/ios-development/app-store-distribution.md`
Distribution requirements, iOS 26 SDK deadline (Apr 28, 2026), build tooling mandates.

## Phase 2 — App Store Connect Setup

### Metadata (per localization)

- **App name** (30 chars) — must be unique on the App Store
- **Subtitle** (30 chars) — brief description shown under the name
- **Description** (4000 chars) — what the app does. First 3 lines visible without "more"
- **Keywords** (100 chars, comma-separated) — for App Store search
- **What's New** (4000 chars) — release notes for this version
- **Support URL** — required
- **Marketing URL** — optional

### Screenshots (required)

Minimum sets needed:
- **6.9" iPhone** (iPhone 16 Pro Max) — required, other sizes auto-scaled
- **6.7" iPhone** (iPhone 15 Plus/Pro Max) — required if you support older sizes
- **13" iPad Pro** — required if your app runs on iPad
- **Apple Vision Pro** — required if you distribute on visionOS

Up to 10 screenshots per device size per localization. First 3 are most important (visible in search results).

### App Review Information

- **Demo account** — if your app requires login, provide test credentials
- **Notes for reviewer** — explain any non-obvious features, required hardware, or special setup
- **Contact info** — phone number and email for the review team to reach you

## Phase 3 — Signing & Build Upload

### Signing

- **Automatic signing** recommended for most apps — Xcode manages certificates and profiles
- **Manual signing** for CI/CD or enterprise distribution
- Certificates: Apple Development (debug) + Apple Distribution (release)
- Provisioning profiles: tied to Bundle ID + device list (dev) or distribution method

### Build Upload

Three ways to upload:

1. **Xcode** → Product → Archive → Distribute App → App Store Connect
2. **`xcodebuild` + `altool`/`xcrun notarytool`** — terminal workflow (see [[tooling.md]])
3. **`asc` CLI** — `asc upload build` for automated pipelines

**Skill: `/asc-automation`** → `.claude/commands/asc-automation.md`
CLI automation for uploads, TestFlight, metadata sync.

**Skill: `/xcode-terminal`** → `.claude/commands/xcode-terminal.md`
Archive and export commands for terminal-based workflows.

## Phase 4 — TestFlight

Before public release, test with real users:

- **Internal testing** — up to 100 team members, builds available immediately after processing
- **External testing** — up to 10,000 testers, requires beta review (usually <24 hours)
- **Test groups** — organize testers by purpose (QA, stakeholders, beta users)
- **Build expiry** — TestFlight builds expire after 90 days
- **Crash reports** — available in App Store Connect under TestFlight → Crashes

## Phase 5 — App Review

### Review Timeline

- **Typical**: 24-48 hours
- **Expedited review**: request via App Store Connect if you have a critical bug fix (Apple grants these selectively)

### Common Rejection Reasons

1. **Crashes or bugs** — test on minimum supported device
2. **Broken links** — privacy policy URL, support URL must be live
3. **Incomplete information** — missing demo account, vague description
4. **Guideline 4.3 (Spam)** — app too similar to existing apps or your other apps
5. **Guideline 2.1 (Performance)** — app doesn't work as described
6. **Guideline 5.1.1 (Data Collection)** — privacy manifest doesn't match actual data collection
7. **In-app purchase issues** — using external payment links without entitlement, not offering "restore purchases"

### If Rejected

- Read the rejection reason carefully — it references specific guideline numbers
- Reply in the Resolution Center with your fix or explanation
- Resubmit the same build (if metadata-only fix) or upload a new build
- Don't argue unless you genuinely believe the reviewer misunderstood — they can escalate to the App Review Board

## Phase 6 — Release Management

- **Manual release** — you control when the approved build goes live
- **Automatic release** — goes live immediately after approval
- **Phased release** — rolls out to 1%, 2%, 5%, 10%, 20%, 50%, 100% over 7 days. Pause anytime.

## Cross-References

- In-app purchases and StoreKit setup → [[distribution.md]] StoreKit section
- CI/CD pipeline for automated builds → [[distribution.md]] CI/CD section
- Privacy manifest implementation details → `/app-store-submit` skill
- Build tools and terminal commands → [[tooling.md]]
