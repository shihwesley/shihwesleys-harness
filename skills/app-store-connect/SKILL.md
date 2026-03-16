---
name: app-store-connect
description: "App Store Connect automation for iOS/visionOS: REST API, JWT auth, TestFlight, metadata management, build upload, submission flow. Use when automating any part of the App Store release pipeline."
---

# App Store Connect Reference

When automating App Store Connect tasks, follow these patterns.

## Auth — API Keys + JWT

Get keys: App Store Connect → Users and Access → Integrations → Keys → "+"
Download `.p8` immediately (only available once). Record Key ID and Issuer ID.

**Roles for automation:**
- `App Manager` — everything release-related: upload, TestFlight, metadata, submit
- `Developer` — upload only (can't update testers or submit for review)

JWT requirements:
- Algorithm: ES256
- `aud`: `"appstoreconnect-v1"`
- Max expiry: **20 minutes** (1200s) — 401 if exceeded

Don't implement JWT manually. Use asc CLI, fastlane, or a SDK.

Fastlane API key JSON (store at `~/Developer/AppStoreConnect/api_key.json`):
```json
{
  "key_id": "XXXXXXXXXX",
  "issuer_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "key": "-----BEGIN PRIVATE KEY-----\nXXX...\n-----END PRIVATE KEY-----"
}
```

CI: pass key as base64 env var, never write `.p8` to disk without cleanup:
```bash
ASC_PRIVATE_KEY_B64=$(base64 < AuthKey_KEYID.p8)
```

## Build Upload (2025/2026)

Pick one:

| Tool | Auth | Best for |
|------|------|----------|
| `asc builds upload` | API key | Scripts, AI agents, new projects |
| Fastlane `upload_to_app_store` | API key or Apple ID | Existing setups, screenshot automation |
| Transporter (GUI) | API key or Apple ID | One-off uploads, no scripting |
| `xcrun altool --upload-app` | Apple ID or API key | Legacy only — avoid for new work |

`xcrun altool` for **notarization is dead** since Nov 2023. Use `xcrun notarytool` for macOS notarization. For iOS/visionOS, it's irrelevant.

asc CLI upload:
```bash
asc builds upload --app "123456789" --file "./MyApp.ipa"
# or one-command TestFlight:
asc publish testflight --ipa "./MyApp.ipa" --group "Internal,Beta" --wait --notify
```

Build processing: ~5 minutes after upload before the build is assignable.

## TestFlight

| | Internal | External |
|---|---|---|
| Max | 100 | 10,000 |
| Who | ASC team members | Anyone |
| Review | No | Yes (first build per version only) |
| Expiry | 90 days | 90 days |

External review for subsequent builds of the same version number is usually skipped.

Setup sequence: upload → wait ~5min → set test info → assign to group → (external: submit for beta review).

Via asc:
```bash
asc publish testflight --ipa "./MyApp.ipa" --group "Internal" --wait
asc testflight builds list --app "APP_ID" --output table
```

Via fastlane:
```ruby
upload_to_testflight(
  api_key_path: "~/Developer/AppStoreConnect/api_key.json",
  groups: ["Internal"],
  changelog: File.read("fastlane/metadata/en-US/release_notes.txt")
)
```

## Metadata Management

**Update without new build:** Only `promotionalText` (170 chars). Everything else needs a new version.

Metadata limits:
- Name: 30 | Subtitle: 30 | Keywords: 100 (comma-separated, no spaces)
- Description: 4,000 | What's new: 4,000 | Promotional text: 170

Store metadata in git (fastlane convention):
```
fastlane/metadata/en-US/
  name.txt
  subtitle.txt
  keywords.txt
  description.txt
  promotional_text.txt
  release_notes.txt
```

Via API (PATCH localization):
```json
PATCH /v1/appStoreVersionLocalizations/{id}
{
  "data": {
    "type": "appStoreVersionLocalizations",
    "id": "LOC_ID",
    "attributes": {
      "description": "...",
      "keywords": "kw1,kw2,kw3",
      "whatsNew": "..."
    }
  }
}
```

Via asc:
```bash
asc apps versions update --app-id $APP_ID --version "1.3.0" \
  --whats-new "$(cat fastlane/metadata/en-US/release_notes.txt)"
```

## Submission Flow

```
1. Upload build
2. Create/select version in ASC
3. Attach build to version
4. Fill metadata + screenshots
5. Age rating, export compliance, App Review notes
6. Submit for review (24-72h)
7. Approve → choose release option
```

Release options: MANUAL (you click), AFTER_APPROVAL (auto), or phased rollout.

Via asc:
```bash
asc validate --app "APP_ID" --version "1.3.0"
asc submit --app "APP_ID" --version "1.3.0"
```

Phased rollout: 7-day schedule, 1%→2%→5%→10%→20%→50%→100%.
Pause if crash rate spikes:
```bash
asc apps versions phasedReleases update --app-id $APP_ID --version "1.3.0" --state PAUSED
```

## Solo Dev Automation

**Automate:** TestFlight upload, metadata text sync, build number bump, release notes from changelog, pre-submission gates, phased release control.

**Do manually:** Age rating, export compliance, App Review notes, initial external group setup, pricing.

**Philosophy:** Human-initiated automation. Run fastlane/asc locally when ready to submit. Skip CI/CD unless you have a team — the maintenance cost isn't worth it for one person.

Minimal fastlane setup:
```ruby
# fastlane/Fastfile
platform :visionos do
  lane :beta do
    build_app(scheme: "MyApp", destination: "generic/platform=visionOS")
    upload_to_testflight(
      api_key_path: "~/Developer/AppStoreConnect/api_key.json",
      groups: ["Internal"]
    )
  end

  lane :release do
    build_app(scheme: "MyApp", destination: "generic/platform=visionOS")
    upload_to_app_store(
      api_key_path: "~/Developer/AppStoreConnect/api_key.json",
      submit_for_review: true,
      automatic_release: false,
      skip_screenshots: true,
      force: true
    )
  end
end
```

```ruby
# fastlane/Gymfile
export_xcargs("-allowProvisioningUpdates")
output_directory("./build")
```

Skip Match and Bundler for solo dev — Xcode automatic codesigning + direct `gem install fastlane` is simpler.

## Gotchas

- `--app` flag takes **numeric App ID**, not bundle ID (`asc apps list` to find it)
- JWT expiry is 20 min max — 401 otherwise
- `.p8` downloads once — back it up to 1Password immediately
- Build processing ~5 min after upload — use `--wait` or poll
- External beta first build requires review per version (subsequent may skip)
- Export compliance per version — set `ITSAppUsesNonExemptEncryption = NO` in Info.plist if you only use OS encryption to skip the manual questionnaire
- Fastlane visionOS support: 2.230.0+ (December 2025)
- asc signing (`asc signing`) not production-ready as of Feb 2026

## API Quick Reference

```
Base URL: https://api.appstoreconnect.apple.com/v1/

GET  /v1/apps                               # list apps
GET  /v1/apps/{id}/appStoreVersions         # versions
POST /v1/appStoreVersions                   # create version
PATCH /v1/appStoreVersionLocalizations/{id} # update metadata
GET  /v1/builds                             # list builds
POST /v1/betaGroups/{id}/relationships/betaTesters  # add testers
POST /v1/reviewSubmissions                  # create submission
PATCH /v1/reviewSubmissions/{id}            # submit (isSubmitted: true)
PATCH /v1/appStoreVersionPhasedReleases/{id} # control rollout
```

Tip: Can't find the right endpoint? Open ASC in browser, perform the action, inspect network traffic in DevTools.

Full expertise: `~/.claude/research/app-store-connect/expertise.md`
Also see: `~/.claude/skills/asc-cli/SKILL.md` | `~/.claude/skills/ios-release-pipeline/SKILL.md`
