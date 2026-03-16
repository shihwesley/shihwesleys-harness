---
description: "App Store submission process: required assets, privacy compliance, review guidelines, TestFlight, signing, metadata, and rejection prevention"
keywords: [app-store, submission, privacy-manifest, review-guidelines, testflight, signing, screenshots, metadata]
---

# App Store Submission Flow

The full path from "code is done" to "app is live." This is a process guide — follow it top to bottom when preparing a release.

## Phase 1 — Pre-Submission Checklist

Required before touching App Store Connect:

- **PrivacyInfo.xcprivacy** — privacy manifest (required since iOS 17, strictly enforced from iOS 26 SDK)
- **Info.plist keys** — usage descriptions for every permission. Missing = automatic rejection.
- **App icons** — 1024x1024, no alpha. Launch screen (static, no code).
- **Export compliance, age rating, EULA** — declarations in App Store Connect
- **Privacy policy URL** — mandatory, publicly accessible
- **Code requirements** — recent SDK (Xcode 16+/iOS 17 minimum as of 2026), no private APIs, no test credentials, crash-free launch

**Skill: `/app-store-submit`** → `.claude/commands/app-store-submit.md`
Full details on privacy manifests, compliance, code requirements, and rejection prevention.

**Doc: `app-store-distribution.md`** → `.claude/docs/ios-development/app-store-distribution.md`
Distribution requirements, iOS 26 SDK deadline (Apr 28, 2026), build tooling mandates.

## Phase 2 — App Store Connect & Screenshots

- Metadata: app name (30 chars), subtitle, description, keywords, release notes, support URL
- Screenshots: 6.9" iPhone required (others auto-scaled), 13" iPad if supporting iPad, Vision Pro if on visionOS
- Review info: demo account if login required, reviewer notes, contact info

## Phase 3 — Signing & Build Upload

- Automatic signing recommended; manual for CI/CD
- Upload via Xcode Archive, `xcodebuild` + `altool`, or `asc` CLI

**Skill: `/asc-automation`** → `.claude/commands/asc-automation.md`
**Skill: `/xcode-terminal`** → `.claude/commands/xcode-terminal.md`

## Phase 4 — TestFlight & Review

- Internal testing (100 members, immediate) and external testing (10k testers, beta review ~24h)
- Builds expire after 90 days
- Review typically 24-48 hours; expedited review available for critical fixes
- Top rejection reasons: crashes, broken URLs, missing demo accounts, guideline 4.3 (spam), 5.1.1 (privacy manifest mismatch)
- If rejected: read the guideline reference, fix, reply in Resolution Center

## Phase 5 — Release Management

- Manual, automatic, or phased release (1% → 100% over 7 days, pauseable)

## Cross-References

- In-app purchases and StoreKit setup → [[distribution.md]] StoreKit section
- CI/CD pipeline for automated builds → [[distribution.md]] CI/CD section
- Privacy manifest implementation details → `/app-store-submit` skill
- Build tools and terminal commands → [[tooling.md]]
