---
name: ios-release-pipeline
description: "iOS/visionOS release pipeline patterns for solo/small team: branching, versioning, CI/CD, submission automation, phased rollout, hotfixes, changelogs, post-release monitoring. Use when shipping an iOS or visionOS app update."
---

# iOS/visionOS Release Pipeline Reference

When shipping an iOS or visionOS app update, follow these patterns.

## Branching

GitHub Flow: `main` is always releasable. Short-lived branches only.
```
feature/<name>     # new work
fix/<name>         # bug fix
hotfix/<name>      # branch from release TAG, not main head
release/<version>  # optional, only for big stabilization periods
```
Tag every App Store submission:
```bash
git tag -a v1.3.0 -m "Release 1.3.0" && git push origin v1.3.0
```

## Version Management

Two keys, separate concerns:
- `CFBundleShortVersionString` / `MARKETING_VERSION` — user-facing (SemVer: 1.3.0)
- `CFBundleVersion` / `CURRENT_PROJECT_VERSION` — build number, must increase monotonically

Prerequisite: Build Settings → Versioning System = **Apple Generic**

```bash
# Bump build number (git commit count — no CI commit needed)
BUILD=$(git rev-list --count HEAD)
xcrun agvtool new-version -all $BUILD

# Bump marketing version
xcrun agvtool new-marketing-version 1.3.0
```

Fastlane equivalent:
```ruby
increment_build_number(build_number: number_of_commits)
increment_version_number(version_number: "1.3.0")
```

## CI/CD

**Solo dev default: Xcode Cloud.** Handles code signing automatically. Supports visionOS.

Three workflows:
1. **PR Validation** — trigger: PR to main → Build + Unit Tests only
2. **TestFlight Deploy** — trigger: push/tag to main → Archive + upload to TestFlight
3. **App Store Release** — trigger: manual or `release/*` tag → Archive + App Store upload

Fastlane inside Xcode Cloud (ci_post_clone.sh):
```bash
#!/bin/bash
brew install fastlane
```

GitHub Actions alternative needs Fastlane Match for code signing — more setup, more portable.

## Pre-Release Gate Script

Run before triggering archive. Fail fast.

```bash
#!/bin/bash
set -e; ERRORS=0

# Privacy manifest
find . -name "PrivacyInfo.xcprivacy" | grep -q . || { echo "ERROR: PrivacyInfo.xcprivacy missing"; ERRORS=$((ERRORS+1)); }

# No localhost URLs in source
grep -r "http://localhost" --include="*.swift" . 2>/dev/null | grep -v "//" && { echo "ERROR: localhost URL in source"; ERRORS=$((ERRORS+1)); }

# Marketing version set
MKTG=$(xcrun agvtool what-marketing-version -terse1 2>/dev/null)
[[ "$MKTG" == "0.0.0" || -z "$MKTG" ]] && { echo "ERROR: version is '$MKTG'"; ERRORS=$((ERRORS+1)); }

# Release notes not empty
[[ ! -s "fastlane/metadata/en-US/release_notes.txt" ]] && { echo "ERROR: release_notes.txt empty"; ERRORS=$((ERRORS+1)); }

# Unit tests
xcodebuild test -scheme MyApp -testPlan UnitTests \
  -destination 'platform=iOS Simulator,name=iPhone 16' -quiet || ERRORS=$((ERRORS+1))

[[ $ERRORS -gt 0 ]] && { echo "Gate FAILED ($ERRORS errors)"; exit 1; }
echo "Gate PASSED"
```

## Testing Strategy

- **Pre-commit hook:** selective unit tests only (fast — under 30s target)
- **CI on PR:** unit + integration tests
- **CI before archive:** full suite including one smoke UI test

Use Swift Testing (`@Test`, `#expect`) for new tests (Xcode 16+, iOS 17+). Skip screenshot tests — too fragile for solo dev maintenance.

## App Store Submission

Metadata file structure (store in git):
```
fastlane/metadata/en-US/
  name.txt           # 30 char max
  subtitle.txt       # 30 char max
  description.txt    # 4000 char max
  release_notes.txt  # 4000 char max (plain text only)
  keywords.txt       # 100 char max, comma-separated
```

Upload via Fastlane:
```ruby
lane :release do
  build_app(scheme: "MyApp", configuration: "Release")
  upload_to_app_store(
    submit_for_review: true,
    automatic_release: false,   # manual release after QA
    skip_screenshots: true,
    force: true
  )
end
```

Or via asc CLI (preferred for metadata-only updates):
```bash
asc apps versions update --app-id $APP_ID --version "1.3.0" \
  --whats-new "$(cat fastlane/metadata/en-US/release_notes.txt)"
```

## Changelog Automation

```bash
brew install git-cliff
```

`cliff.toml` — filter chore/docs/style/ci from user-facing notes:
```toml
[git]
conventional_commits = true
commit_parsers = [
  { message = "^feat", group = "Features" },
  { message = "^fix", group = "Bug Fixes" },
  { message = "^perf", group = "Performance" },
  { message = "^chore|^docs|^style|^ci", skip = true },
]
```

```bash
# Full CHANGELOG.md
git cliff --tag v1.3.0 --output CHANGELOG.md

# App Store release notes (plain text, 3900 char safe limit)
git cliff --tag v1.3.0 --strip all --current \
  | sed 's/^## .*//' | sed 's/^### //' | sed 's/^- /• /' \
  | head -c 3900 > fastlane/metadata/en-US/release_notes.txt
```

## Phased Rollout

Enable before review approval in ASC: Version page → Phased Release → "Release update over 7-day period"

Schedule: 1% → 2% → 5% → 10% → 20% → 50% → 100% (one step per 24h)

Pause triggers:
- Crash rate >2× baseline
- Crash rate absolute increase >0.5%
- 1-star review mentions crash or data loss

Pause before the next 24h mark — percentage doubles at that mark.

```bash
# Pause via asc CLI
asc apps versions phasedReleases update --app-id $APP_ID --version "1.3.0" --state PAUSED
# Release to all immediately
asc apps versions phasedReleases update --app-id $APP_ID --version "1.3.0" --state COMPLETE
```

**Hotfixes:** Do NOT use phased rollout — release to 100% immediately.

## Hotfix Workflow

```bash
# Branch from the release tag, not from current main
git checkout v1.3.0
git checkout -b hotfix/crash-on-launch

# Fix, then bump patch version
xcrun agvtool new-marketing-version 1.3.1
xcrun agvtool new-version -all $(git rev-list --count HEAD)
git add -A && git commit -m "chore: bump to 1.3.1"
git tag -a v1.3.1 -m "Hotfix 1.3.1"

# Merge back to main
git checkout main && git merge hotfix/crash-on-launch
git push origin main --tags

# Expedited review if needed:
# https://developer.apple.com/contact/app-store/
# State: crash affecting X% of users, version X.X.X, include timeline impact
```

## Post-Release Monitoring

**Monitoring stack:**
1. Sentry or Firebase Crashlytics — real-time crash alerts (MetricKit alone is too slow)
2. Xcode Organizer — crash rate, energy, hang rate (check T+1h)
3. MetricKit — deep diagnostics, delivered once per 24h
4. App Store Connect Analytics — install and session trends

Timeline:
| Time | Check |
|------|-------|
| T+1h | Xcode Organizer crash rate, Sentry dashboard |
| T+4h | App Store reviews (1-2 stars) |
| T+24h | MetricKit payload arrives — compare to previous version baseline |
| T+48h | ~2-5% reached — pause if any anomaly |
| Day 4 | 10% — solid signal. Safe to accelerate if clean. |

## Quick Commands

```bash
# Full release sequence
bash scripts/release-gate.sh           # pre-flight check
xcrun agvtool new-marketing-version X.Y.Z
xcrun agvtool new-version -all $(git rev-list --count HEAD)
git cliff --tag vX.Y.Z --output CHANGELOG.md
git cliff --tag vX.Y.Z --strip all --current | head -c 3900 > fastlane/metadata/en-US/release_notes.txt
git tag -a vX.Y.Z -m "Release X.Y.Z" && git push origin vX.Y.Z
fastlane release   # or trigger Xcode Cloud workflow
```

## Key Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `git-cliff` | Changelog from conventional commits | `brew install git-cliff` |
| `asc` CLI | App Store Connect automation | https://asccli.sh |
| Fastlane | Build/sign/upload automation | `gem install fastlane` |
| Xcode Cloud | CI/CD with native code signing | Built into Xcode |

Full expertise: `~/.claude/research/ios-release-pipeline/expertise.md`
