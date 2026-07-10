# Mobile Versioning

| Field | Source |
|-------|--------|
| Product version | `pubspec.yaml` `version:` (e.g. 2.0.0) |
| Build number | `version:+N` suffix |
| API compatibility | `API_COMPAT_VERSION` dart-define (default `v1`) |
| Environment badge | `APP_ENV` |

## Upgrade foundation

- **Forced upgrade** — requires backend `minimum_app_version` (gap documented)
- **Optional upgrade** — store prompt + in-app banner

## Release

Increment build number for every store submission.
Semantic version for user-visible releases.
