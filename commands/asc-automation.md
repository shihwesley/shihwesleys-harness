---
name: asc-automation
description: "Use when automating App Store Connect tasks: uploading builds, managing TestFlight, syncing metadata, managing signing assets, or checking submission health. Requires the `asc` CLI (github.com/rudrankriyam/App-Store-Connect-CLI)."
argument-hint: "[task: upload, testflight, metadata, signing, submit]"
allowed-tools: ["Bash", "Read", "Write", "Glob"]
---

# App Store Connect CLI Automation

Consolidated reference for the `asc` CLI. Covers builds, TestFlight, signing, metadata, submissions, and screenshots.

## Prerequisites

```bash
# Install
brew install nicklama/tap/asc  # or build from source

# Auth (keychain — recommended)
asc auth login

# Or env vars
export ASC_KEY_ID="your-key-id"
export ASC_ISSUER_ID="your-issuer-id"
export ASC_PRIVATE_KEY_PATH="~/.appstoreconnect/private_keys/AuthKey_XXXX.p8"

# Default app (avoids --app everywhere)
export ASC_APP_ID="your-app-id"
```

**Output**: JSON by default. `--output table` or `--output markdown` for human reading. `--paginate` for full lists.

## ID Resolution

Most commands need IDs. Resolve from names:

```bash
asc apps list --bundle-id "com.example.app"     # app ID
asc builds latest --app APP --version "1.2.3"   # build ID
asc versions list --app APP                      # version ID
asc beta-groups list --app APP                   # group IDs
```

## Release Flow

### One-Command Releases
```bash
# TestFlight
asc publish testflight --app APP --ipa ./app.ipa --group GROUP_ID --wait --notify

# App Store
asc publish appstore --app APP --ipa ./app.ipa --version "1.2.3" --wait --submit --confirm
```

### Manual Sequence (more control)
```bash
asc builds upload --app APP --ipa ./app.ipa
asc builds latest --app APP --version "1.2.3"           # get BUILD_ID
asc builds add-groups --build BUILD_ID --group GROUP_ID  # TestFlight
asc versions attach-build --version-id VER --build BUILD_ID
asc submit create --app APP --version "1.2.3" --build BUILD_ID --confirm
```

## TestFlight Management

```bash
# Groups
asc beta-groups create --app APP --name "Beta Testers"
asc beta-groups list --app APP --paginate

# Testers
asc beta-testers add --app APP --email "user@example.com" --group "Beta Testers"
asc beta-testers list --app APP --paginate

# What to Test notes
asc builds test-notes create --build BUILD_ID --locale "en-US" --whats-new "Test login flow"

# Export config
asc testflight sync pull --app APP --output ./testflight.yaml --include-builds --include-testers
```

## Signing Setup

```bash
# Bundle IDs
asc bundle-ids create --identifier "com.example.app" --name "Example" --platform IOS
asc bundle-ids capabilities add --bundle BUNDLE_ID --capability ICLOUD

# Certificates
asc certificates list --certificate-type IOS_DISTRIBUTION
asc certificates create --certificate-type IOS_DISTRIBUTION --csr ./cert.csr

# Provisioning Profiles
asc profiles create --name "AppStore Profile" --profile-type IOS_APP_STORE \
  --bundle BUNDLE_ID --certificate CERT_ID
asc profiles download --id PROFILE_ID --output ./profiles/

# Rotation
asc certificates revoke --id CERT_ID --confirm
asc profiles delete --id PROFILE_ID --confirm
```

## Metadata Sync

```bash
# Download current metadata
asc localizations download --version VER_ID --path ./localizations

# Upload updated metadata
asc localizations upload --version VER_ID --path ./localizations

# Fastlane format migration
asc migrate export --app APP --output ./metadata       # export
asc migrate validate --fastlane-dir ./metadata         # check limits
asc migrate import --app APP --fastlane-dir ./metadata # import
```

## Submission Health (Pre-flight)

Run before submitting:

```bash
# 1. Build processed?
asc builds info --build BUILD_ID  # processingState = VALID

# 2. Encryption compliance
asc encryption declarations create --app APP \
  --app-description "Uses standard HTTPS/TLS" \
  --contains-proprietary-cryptography=false \
  --contains-third-party-cryptography=true
asc encryption declarations assign-builds --id DECL_ID --build BUILD_ID

# 3. Content rights
asc apps update --id APP --content-rights "DOES_NOT_USE_THIRD_PARTY_CONTENT"

# 4. Copyright
asc versions update --version-id VER --copyright "2026 Your Company"

# 5. Localizations complete?
asc localizations list --version VER_ID

# 6. Check/cancel submission
asc submit status --version-id VER_ID
asc submit cancel --id SUB_ID --confirm
```

## Build Lifecycle

```bash
# Cleanup old builds
asc builds expire-all --app APP --older-than 90d --dry-run   # preview
asc builds expire-all --app APP --older-than 90d --confirm   # apply
asc builds expire --build BUILD_ID                            # single
```

## Screenshot Pipeline

```bash
# Settings file: .asc/shots.settings.json
# Capture plan: .asc/screenshots.json

# Frame screenshots
asc screenshots frame --settings .asc/shots.settings.json

# Upload to App Store Connect
asc screenshots upload --settings .asc/shots.settings.json

# List supported frame devices
asc screenshots list-frame-devices
```

## Source
Based on skills from [github.com/rudrankriyam/app-store-connect-cli-skills](https://github.com/rudrankriyam/app-store-connect-cli-skills)
