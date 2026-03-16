---
name: app-store-submit
description: "Use when preparing an iOS app for App Store submission. Covers privacy manifests, compliance, TestFlight, and rejection prevention."
argument-hint: "[app name or submission context]"
allowed-tools: ["Read", "Glob", "Grep", "Bash", "AskUserQuestion"]
---

# App Store Submission Checklist

Guide through App Store submission preparation, privacy compliance, and rejection prevention.

## When to Use
- Preparing first App Store submission
- Updating app for iOS 26 SDK deadline (April 28, 2026)
- Adding privacy manifests
- Setting up TestFlight
- Debugging App Store rejection

## Pre-Submission Audit

Run through each section. Check off items as you go.

### 1. Privacy Manifest (PrivacyInfo.xcprivacy)

Check if app uses required reason APIs:
- FileTimestamp APIs → need reason code (DDA9.1, C617.1, 3B52.1, or 0A2A.1)
- UserDefaults → need CA92.1
- DiskSpace APIs → need 7D9E.1
- SystemBootTime → need 35F9.1

Verify: `grep -r "PrivacyInfo.xcprivacy" .` — file exists in bundle.

Check third-party SDKs: each must include their own privacy manifest.

### 2. Export Compliance

If using only standard iOS encryption (HTTPS via URLSession):
```xml
<key>ITSAppUsesNonExemptEncryption</key>
<false/>
```

### 3. Metadata

- [ ] App name, subtitle, category
- [ ] Description (no misleading claims)
- [ ] Keywords
- [ ] Screenshots for all required device sizes
- [ ] Privacy policy URL (must be live)
- [ ] Support URL
- [ ] Age rating questionnaire completed

### 4. Build Configuration

- [ ] Built with correct SDK (iOS 26 after April 2026)
- [ ] Version and build number incremented
- [ ] Release configuration (not Debug)
- [ ] Bitcode disabled (deprecated)
- [ ] Minimum deployment target set correctly

### 5. App Review Preparation

- [ ] Demo account credentials (if login required)
- [ ] Review notes explaining non-obvious features
- [ ] All flows tested on clean install
- [ ] No placeholder content or broken links
- [ ] IAP restore purchases button exists (if applicable)

### 6. TestFlight (Recommended Before Submission)

**Via Xcode**: Archive → Distribute → TestFlight
**Via asc CLI** (if installed):
```bash
asc publish testflight --app APP_ID --ipa ./app.ipa --group GROUP_ID --wait --notify
```
- Internal testing: up to 100 users, no review
- External testing: up to 10,000, first build reviewed
- Builds expire after 90 days

### 7. Submission Health Check (asc CLI)

If `asc` CLI is available, run these pre-flight checks:
```bash
asc builds info --build BUILD_ID              # processingState = VALID?
asc apps update --id APP --content-rights "DOES_NOT_USE_THIRD_PARTY_CONTENT"
asc versions update --version-id VER --copyright "2026 Your Company"
asc localizations list --version VER_ID       # all locales filled?
```

For encryption compliance (if build flags `usesNonExemptEncryption: true`):
```bash
asc encryption declarations create --app APP --contains-proprietary-cryptography=false
asc encryption declarations assign-builds --id DECL_ID --build BUILD_ID
```

See `/asc-automation` skill for full asc CLI reference.

## Top Rejection Reasons (Prevention)

1. **Guideline 2.1 (40%)**: Test all flows, no crashes, no placeholders
2. **Privacy**: Include manifest, nutrition labels, privacy policy
3. **IAP 3.1.1**: Digital goods through Apple IAP only, restore button required
4. **Metadata 2.3**: Accurate description, working links, no unverifiable claims

## Code Signing

- Local dev: Xcode automatic signing
- CI/CD: fastlane match (readonly in CI)
- Annual renewal: match_nuke → match with readonly: false

## Knowledge Docs
Reference: `.claude/docs/ios-development/app-store-distribution.md`
