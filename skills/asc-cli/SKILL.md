---
name: asc-cli
description: "App Store Connect CLI (asc) patterns, commands, and CI setup. Use when automating App Store submissions, TestFlight distribution, metadata, screenshots, or signing via the asc CLI tool."
---

# App Store Connect CLI (asc) Reference

When working with `asc`, apply these patterns.

## Installation

```bash
brew install asc
# or
curl -fsSL https://asccli.sh/install | bash
```

## Auth Setup

Requires App Store Connect API key (not Apple ID).
Generate at: App Store Connect → Users and Access → Integrations → Keys

```bash
asc auth login \
  --name "MyApp" \
  --key-id "ABC123" \
  --issuer-id "DEF456" \
  --private-key /path/to/AuthKey.p8

asc doctor  # diagnose auth issues
```

## Core Release Loop

```bash
asc builds upload --app "APP_ID" --file "./MyApp.ipa"
asc validate --app "APP_ID" --version "X.Y.Z"
asc submit --app "APP_ID" --version "X.Y.Z"
```

## TestFlight (one command)

```bash
asc publish testflight \
  --ipa "./build/MyApp.ipa" \
  --group "Internal,External" \
  --wait \
  --notify
```

## CI Environment Variables

```bash
ASC_BYPASS_KEYCHAIN=1      # required — no Keychain in CI
ASC_NO_UPDATE=1            # suppress update checks
ASC_APP_ID=...
ASC_KEY_ID=...
ASC_ISSUER_ID=...
ASC_PRIVATE_KEY_B64=...    # base64-encoded .p8 file contents
```

## GitHub Actions

```yaml
- uses: rudrankriyam/setup-asc@v1
  with:
    version: latest
- run: asc publish testflight --ipa "./build/MyApp.ipa" --group "Internal" --wait
```

## Common Commands

```bash
asc apps list --output table        # find numeric App ID
asc testflight builds list --app "ID" --output table
asc localizations list --app "ID"
asc screenshots list --app "ID"
asc certificates list
asc profiles list
asc bundle-ids list
asc status --app "ID"               # release pipeline dashboard
asc diff ...                        # preview changes without applying
asc workflow run --file .asc/workflow.json --workflow release
```

## Output / Scripting

- Default output: minified JSON (good for piping)
- `--output table` for humans, `--output markdown` for docs
- `--paginate` on list commands to fetch all pages
- `--pretty` for readable JSON
- `--api-debug` for HTTP debugging (redacts secrets)
- `--profile NAME` to switch between API key configs

## Gotchas

- `--app` takes numeric App ID, not bundle ID (`asc apps list` to find it)
- `ASC_BYPASS_KEYCHAIN=1` is required in all CI environments
- Build processing takes ~5 min after upload; use `--wait` or poll
- Signing automation (`asc signing`) is in active development — not production-ready as of Feb 2026
- `.p8` private key can only be downloaded once from ASC portal

## vs Fastlane

| `asc` | Fastlane |
|-------|----------|
| API key only, no 2FA | Apple ID or API key |
| Single binary, no Ruby | Ruby + Gemfile + CocoaPods |
| JSON-first scripting | Ruby DSL (Fastfile) |
| ~2 months old (Feb 2026) | Mature, large plugin ecosystem |
| No Android | iOS + Android |

Choose `asc` for clean API-key-only automation or AI agent pipelines.
Choose Fastlane if you have existing infrastructure or need plugins/Android.

## Full Expertise

`/Users/quartershots/.claude/research/asc-cli/expertise.md`
