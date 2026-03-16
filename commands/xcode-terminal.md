---
name: xcode-terminal
description: "Use when building, testing, archiving, or controlling simulators from the terminal. Covers xcodebuild, simctl, xctrace, xcbeautify, and the asc CLI for App Store Connect."
argument-hint: "[action: build, test, archive, simulator, profile]"
allowed-tools: ["Bash", "Read", "Glob", "Grep", "Write"]
---

# Xcode Terminal Operations

Complete reference for iOS development from the terminal.

> **Prefer `/xcodebuildmcp`** for build, test, run, debug, and simulator ops — it returns structured output via MCP tools. Use this skill for archive/export, xctrace profiling, code signing, and CI-specific workflows that XcodeBuildMCP doesn't cover.

## xcodebuild

### Discovery
```bash
xcodebuild -list -workspace MyApp.xcworkspace  # schemes, targets, configs
xcodebuild -showBuildSettings -scheme MyScheme   # all build settings
```

### Build
```bash
# Basic
xcodebuild -workspace MyApp.xcworkspace -scheme MyScheme build

# Release with signing disabled (for CI checks)
xcodebuild -scheme MyScheme -configuration Release build CODE_SIGNING_ALLOWED=NO

# With xcbeautify (recommended)
set -o pipefail && xcodebuild -scheme MyScheme build 2>&1 | xcbeautify
```

### Test
```bash
# Run all tests
xcodebuild test -scheme MyScheme \
  -destination 'platform=iOS Simulator,name=iPhone 15,OS=latest'

# Specific test
xcodebuild test -scheme MyScheme \
  -only-testing:MyTests/LoginTests/testValidLogin \
  -destination 'platform=iOS Simulator,name=iPhone 15'

# Parallel testing (3 simulator clones)
xcodebuild test -scheme MyScheme \
  -parallel-testing-enabled YES \
  -parallel-testing-worker-count 3 \
  -destination 'platform=iOS Simulator,name=iPhone 15'

# Build for testing (CI: build once, test many)
xcodebuild build-for-testing -scheme MyScheme -derivedDataPath ./dd
xcodebuild test-without-building -scheme MyScheme -derivedDataPath ./dd

# Result bundle for CI artifacts
xcodebuild test -scheme MyScheme -resultBundlePath ./results.xcresult
```

### Archive & Export
```bash
# Archive
xcodebuild clean archive \
  -workspace MyApp.xcworkspace \
  -scheme MyScheme \
  -configuration Release \
  -archivePath ./build/MyApp.xcarchive \
  -destination 'generic/platform=iOS'

# Export IPA
xcodebuild -exportArchive \
  -archivePath ./build/MyApp.xcarchive \
  -exportPath ./build/ipa \
  -exportOptionsPlist ExportOptions.plist \
  -allowProvisioningUpdates
```

**ExportOptions.plist** (App Store):
```xml
<plist version="1.0"><dict>
  <key>method</key><string>app-store-connect</string>
  <key>teamID</key><string>YOUR_TEAM_ID</string>
</dict></plist>
```

Export methods: `app-store-connect`, `ad-hoc`, `development`, `enterprise`

### Code Signing from Terminal
```bash
# Automatic
xcodebuild archive -scheme MyScheme -allowProvisioningUpdates

# Manual
xcodebuild archive -scheme MyScheme \
  CODE_SIGN_STYLE=Manual \
  DEVELOPMENT_TEAM=XXX111AAA \
  PROVISIONING_PROFILE_SPECIFIER="My Profile" \
  CODE_SIGN_IDENTITY="iPhone Distribution"
```

## xcrun simctl — Simulator Control

### Device Management
```bash
xcrun simctl list devices --json         # list all (JSON)
xcrun simctl boot "iPhone 15 Pro"        # boot by name
xcrun simctl shutdown booted             # shutdown current
xcrun simctl erase booted                # factory reset
xcrun simctl delete unavailable          # clean old devices
xcrun simctl create "Test Phone" \
  com.apple.CoreSimulator.SimDeviceType.iPhone-15 \
  com.apple.CoreSimulator.SimRuntime.iOS-17-0
```

### App Operations
```bash
xcrun simctl install booted /path/to/MyApp.app
xcrun simctl launch booted com.myapp.bundle --arg1 val1
xcrun simctl terminate booted com.myapp.bundle
xcrun simctl uninstall booted com.myapp.bundle
xcrun simctl openurl booted "myapp://deeplink/profile"
```

### Screenshots & Video
```bash
xcrun simctl io booted screenshot shot.png
xcrun simctl io booted recordVideo recording.mp4  # Ctrl+C to stop
```

### Status Bar Override (for App Store screenshots)
```bash
xcrun simctl status_bar booted override \
  --time "9:41" --dataNetwork wifi --wifiBars 3 \
  --cellularBars 4 --batteryState charged --batteryLevel 100

xcrun simctl status_bar booted clear
```

### Push Notifications
```bash
# From file
xcrun simctl push booted com.myapp.bundle notification.apns

# Inline
echo '{"aps":{"alert":"Test"}}' | xcrun simctl push booted com.myapp.bundle -
```

### Media & Data
```bash
xcrun simctl addmedia booted photo.jpg video.mp4  # add to Photos
```

## xctrace — Performance Profiling

```bash
xcrun xctrace list templates                        # available templates
xcrun xctrace record --template 'Time Profiler' \
  --output profile.trace --time-limit 30s \
  --launch -- /path/to/binary

xcrun xctrace record --template 'Allocations' \
  --attach MyApp --output memory.trace

xcrun xctrace export --input profile.trace --toc    # table of contents
xcrun xctrace symbolicate --input profile.trace \
  --dsym /path/to/MyApp.dSYM
```

Templates: Time Profiler, Allocations, Leaks, System Trace, Network, CPU Counters.

## xcbeautify — Build Output Formatting

```bash
brew install xcbeautify  # install

set -o pipefail && xcodebuild build -scheme X 2>&1 | xcbeautify
swift test 2>&1 | xcbeautify

# CI renderers
xcodebuild build -scheme X | xcbeautify --renderer github-actions
```

Replaces xcpretty. Written in Swift, no Ruby dependency. Pre-installed on GitHub Actions macOS runners.

## xcode-select — Version Management

```bash
xcode-select --install              # install CLI tools
xcode-select --print-path           # current Xcode
sudo xcode-select --switch /Applications/Xcode-16.app
sudo xcode-select --reset           # back to default
```

## Swift Package Manager CLI

```bash
swift package init --type executable  # new package
swift build                           # debug build
swift build -c release                # release build
swift test                            # run tests
swift test --filter MyTests/test*     # filtered
swift test --parallel --enable-code-coverage
swift package resolve                 # resolve deps
swift package update                  # update deps
swift package show-dependencies       # dep tree
swift package clean                   # clean build
swift package reset                   # full clean + deps
```

## asc CLI — App Store Connect (if installed)

```bash
# Upload + distribute in one command
asc publish testflight --app APP_ID --ipa ./app.ipa --group GROUP_ID --wait
asc publish appstore --app APP_ID --ipa ./app.ipa --version "1.2.3" --wait --submit --confirm

# Build management
asc builds latest --app APP_ID --version "1.2.3" --platform IOS
asc builds list --app APP_ID --sort -uploadedDate --limit 10
```

Install: `brew install nicklama/tap/asc` or see github.com/rudrankriyam/App-Store-Connect-CLI

## Common CI/CD Recipes

### Full Pipeline
```bash
# Build → Test → Archive → Export → Upload
set -o pipefail
xcodebuild clean build-for-testing -scheme MyScheme | xcbeautify
xcodebuild test-without-building -scheme MyScheme -resultBundlePath results.xcresult | xcbeautify
xcodebuild archive -scheme MyScheme -archivePath build/App.xcarchive | xcbeautify
xcodebuild -exportArchive -archivePath build/App.xcarchive -exportPath build/ipa -exportOptionsPlist Export.plist
```

### Screenshot Automation
```bash
xcrun simctl boot "iPhone 15 Pro"
xcrun simctl status_bar booted override --time "9:41" --batteryState charged --batteryLevel 100
xcrun simctl install booted build/MyApp.app
xcrun simctl launch booted com.myapp.bundle
sleep 3
xcrun simctl io booted screenshot screenshots/home.png
```

## Knowledge Docs
Reference: `.claude/docs/ios-development/cicd-build-tooling.md`, `.claude/docs/ios-development/xcode-terminal.md`
