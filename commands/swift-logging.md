---
name: swift-logging
description: "Use when adding logging to Swift code, choosing between os.Logger and swift-log, debugging with Console.app/log CLI, adding signposts for Instruments, exporting logs with OSLogStore, or reviewing logging patterns for privacy/performance."
user-invocable: true
---

# Swift Logging Skill

Covers Apple's `os.Logger` (Unified Logging), `apple/swift-log` (cross-platform), `OSSignposter` (performance intervals), and `OSLogStore` (programmatic log reading).

## Agent Rules

1. **Default to `os.Logger`** on Apple platforms. Only recommend `swift-log` for server-side Swift or cross-platform packages.
2. **Never log PII at `.public` privacy.** Use `.private` or `.private(mask: .hash)` for user data.
3. **Don't use `print()` for logging.** It allocates synchronously, can't be filtered, and ships in release builds. Replace with `os.Logger`.
4. **Match log levels to persistence behavior.** `.debug` is discarded unless streaming. `.info` is memory-only. `.notice`+ persists to disk.
5. **Don't wrap os.Logger in a custom abstraction** unless the project genuinely needs cross-platform support. The native API is already well-designed.
6. **Use subsystem = bundle identifier, category = module name.** This is Apple's recommended convention.
7. **Prefer static Logger properties** via an extension on `Logger` rather than creating loggers per-instance.

## Triage — First 60 Seconds

When the user asks about logging, determine:

| Question | Routes To |
|----------|-----------|
| Adding logging to an Apple app | → `os-logger.md` |
| Server-side Swift or cross-platform package | → `swift-log.md` |
| Performance measurement with Instruments | → `signposts.md` |
| Exporting logs for bug reports / in-app viewer | → `log-store.md` |
| Choosing between os.Logger and swift-log | → `best-practices.md` § Decision Framework |
| Privacy annotations for user data | → `best-practices.md` § Privacy |
| Viewing/filtering logs in Console.app or CLI | → `best-practices.md` § Debugging Tools |
| Log level guidance (what goes where) | → `best-practices.md` § Level Guide |

## Quick Setup Pattern

For most Apple apps, this is all you need:

```swift
import OSLog

extension Logger {
    private static let subsystem = Bundle.main.bundleIdentifier!

    static let network  = Logger(subsystem: subsystem, category: "Network")
    static let data     = Logger(subsystem: subsystem, category: "Data")
    static let auth     = Logger(subsystem: subsystem, category: "Auth")
    static let ui       = Logger(subsystem: subsystem, category: "UI")
}

// Usage
Logger.network.info("GET \(endpoint, privacy: .public)")
Logger.auth.error("Token expired: \(error, privacy: .public)")
```

## Reference Files

Load only the reference you need:

- `os-logger.md` — os.Logger API: initializers, levels, privacy annotations, formatting, performance
- `swift-log.md` — apple/swift-log: Logger, LogHandler, LoggingSystem, MultiplexLogHandler, MetadataProvider
- `signposts.md` — OSSignposter intervals, events, Instruments integration
- `log-store.md` — OSLogStore: programmatic reading, filtering, export patterns
- `best-practices.md` — Decision framework, level guide, privacy rules, debugging tools, subsystem/category conventions

Reference path: `.claude/docs/swift-logging/`

## Verification Checklist

Before finishing logging work:

- [ ] No `print()` statements left in production code paths
- [ ] PII uses `.private` or `.private(mask: .hash)`, never `.public`
- [ ] Subsystem matches bundle identifier
- [ ] Categories are consistent across the module
- [ ] Debug-level logs don't perform expensive computation unconditionally
- [ ] Error-level logs include the error description with `.public` privacy
- [ ] Static Logger properties used (not per-instance creation)
