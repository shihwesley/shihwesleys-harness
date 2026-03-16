---
name: ios-app-release-2025
description: "iOS/visionOS commercial app release process — App Store prep, legal/compliance, monetization, marketing, technical readiness, launch, post-launch. Use when preparing an app for public release."
---

# iOS/visionOS App Release Reference (2025-2026)

When preparing an app for commercial release, follow these patterns and requirements.

## App Store Metadata

| Field | Limit | Key Rule |
|-------|-------|----------|
| App Name | 30 chars | Primary keyword here |
| Subtitle | 30 chars | Secondary keywords + value prop |
| Keywords | 100 chars | No duplicates with title/subtitle |
| Description | 4,000 chars | Only updates with new version |
| Promotional Text | 170 chars | Updates anytime, no new build |

Screenshots: min 1, max 10 per device size. Required sizes: iPhone 6.9" (1320x2868), 6.5" (1242x2688), 5.5" (1242x2208). visionOS: 3840x2160. Preview videos: max 3, max 30 sec each.

## Privacy & Compliance Checklist

```
[ ] PrivacyInfo.xcprivacy — mandatory since May 2024
    - NSPrivacyTracking (bool)
    - NSPrivacyTrackingDomains (array)
    - NSPrivacyAccessedAPITypes + reason codes
    - NSPrivacyCollectedDataTypes
[ ] Privacy policy URL in App Store Connect AND accessible in-app
[ ] Privacy nutrition labels match actual data practices
[ ] ATT prompt if accessing IDFA or cross-app tracking
[ ] Account deletion from within app (if accounts exist)
[ ] ITSAppUsesNonExemptEncryption = NO in Info.plist (if only OS encryption)
[ ] GDPR: consent mechanism, data minimization, DPA with processors, right to erasure
[ ] CCPA: "Do Not Sell" mechanism, disclosure + access + deletion rights
```

Required Reason API codes:
- UserDefaults: CA92.1
- DiskSpace: 7D9E.1
- FileTimestamp: 3B52.1
- SystemBootTime: 35F9.1

## StoreKit 2 Patterns

```swift
// Fetch
let products = try await Product.products(for: productIDs)

// Purchase
let result = try await product.purchase()

// Entitlements
for await entitlement in Transaction.currentEntitlements { ... }

// Updates
for await update in Transaction.updates { ... }

// NEVER hardcode prices — use product.displayPrice
// NEVER hardcode product IDs — serve from remote config
```

SwiftUI views: `SubscriptionStoreView` (full paywall), `StoreView` (general), `ProductView` (single item), `SubscriptionOfferView` (2025, promotional).

## Monetization Quick Rules

- Subscription pricing: $5/month minimum for consumer apps. Underpricing kills perceived value.
- Free trials boost US LTV by 64%. 7-day for entertainment, 30-day for productivity.
- Apple commission: 30% year 1, 15% after (auto-renewable). 15% for Small Business Program (<$1M).
- A/B test paywalls — frequent testers see up to 100x revenue vs non-testers.
- Show paywall after onboarding, not before user experiences value.
- Monthly churn target: under 5%.

## Technical Readiness

```
[ ] Crash reporting integrated (Sentry, TelemetryDeck, or Crashlytics)
[ ] Analytics: privacy-first (TelemetryDeck) or full (Mixpanel)
[ ] Performance profiled with Instruments (CPU, memory, energy)
[ ] Accessibility audit: VoiceOver, Dynamic Type, Switch Control, Reduce Motion, Dark Mode
[ ] Localization: at minimum App Store metadata; ideally in-app strings
[ ] Debug logs stripped from Release build (use os_log with levels)
[ ] Tested on: latest iPhone, previous gen, SE, iPad (if supported), Vision Pro (if visionOS)
[ ] Support current iOS + previous 2 major versions
[ ] Starting April 2026: must build with iOS 26 SDK
```

## Launch Checklist

```
[ ] All metadata finalized
[ ] Screenshots for all device sizes
[ ] Privacy policy live
[ ] PrivacyInfo.xcprivacy complete
[ ] Privacy labels match reality
[ ] Age rating questionnaire done
[ ] Export compliance answered
[ ] IAPs configured and tested
[ ] App Review notes written (demo creds, special setup)
[ ] TestFlight testing complete on all target devices
[ ] Featuring Nomination submitted (2+ weeks lead time, ideally 3 months)
[ ] Build uploaded and submitted for review (24-72h)
```

## Apple Featuring Criteria

Submit Featuring Nomination in App Store Connect. Apple evaluates: UX quality, UI design, innovation, uniqueness, accessibility, localization. Featured apps see up to 200% install increase. Adopt latest Apple tech, maintain 4+ stars, localize broadly.

## Post-Launch

- Respond to all reviews (especially negative)
- Update cadence: weekly bugfixes, monthly improvements, quarterly features, annual architecture review
- Track Day 1/7/28 retention in App Store Connect
- A/B test screenshots and icons via Product Page Optimization
- Regular updates signal active maintenance to ranking algorithms

## Common Rejection Reasons

1. Crashes or broken flows (2.1 Performance)
2. Misleading metadata (2.3 Accurate Metadata)
3. Paywall/IAP issues (3.1.1 In-App Purchase)
4. Missing account deletion
5. Privacy manifest omissions
6. Other platform logos in screenshots

~40% of first-time submissions are rejected. Test thoroughly.

## visionOS Specifics

- Say "spatial computing app" — never AR/VR/XR/MR
- Lowercase "v" in visionOS, keep Apple terms in English
- Icon: circular 3D (background + 1-2 layers)
- Screenshots: 3840x2160, show window/volume/immersive contexts
- Declare motion information for apps with camera movement
- HIG compliance strictly enforced — no flat iPad ports

For deeper information, query the knowledge store or read:
`~/.claude/research/ios-app-release-2025/expertise.md`
