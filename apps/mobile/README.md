# DxCon Mobile (Flutter)

Phase 1 foundation for the unified DxCon mobile client (`apps/mobile`).

**Status:** Phase 1 complete — await production verification before Phase 2 (patient portal) or Phase 3 (collector).

## Architecture (Phase 1)

| Layer | Location |
|-------|----------|
| Environment / flavors | `lib/config/environment.dart`, `config/*.env.json`, Android product flavors |
| Secure session | `lib/core/storage/secure_token_storage.dart` (Keychain / EncryptedSharedPreferences) |
| Auth (login/logout/refresh/org) | `lib/core/auth/*` against frozen `/api/v1/auth/*` |
| Role routing | `lib/core/navigation/role_routing.dart` + `app_router.dart` |
| API client + errors | `lib/core/api/api_client.dart`, `lib/core/errors/api_error.dart` |
| Offline-safe reads | `lib/core/offline/*` (Hive TTL cache + connectivity fallback) |
| Analytics / crash | No-op unless `ANALYTICS_ENABLED` / `SENTRY_DSN` provided at build time |

Does **not** change web auth freeze files or backend contracts.

## Prerequisites

- Flutter stable (SDK ^3.12)
- Android SDK (for APK) and/or Xcode (for iOS)

```bash
cd apps/mobile
flutter pub get
```

## Environment / flavors

Secrets are **never** committed. Use `--dart-define-from-file` and optional local overrides under `config/local/` (gitignored).

| Flavor | Config file | Android applicationId |
|--------|-------------|------------------------|
| development | `config/development.env.json` | `vn.com.dxcon.mobile.dev` |
| staging | `config/staging.env.json` | `vn.com.dxcon.mobile.staging` |
| production | `config/production.env.json` | `vn.com.dxcon.mobile` |

### Run (Android)

```bash
flutter run --flavor production \
  --dart-define-from-file=config/production.env.json

flutter run --flavor development \
  --dart-define-from-file=config/development.env.json
```

### Run (iOS)

```bash
flutter run \
  --dart-define-from-file=config/production.env.json
```

iOS Xcode schemes for flavors can be added when App Store / TestFlight pipelines are approved. Until then, use dart-define files.

### Build

```bash
# Android debug (CI)
flutter build apk --debug --flavor production \
  --dart-define-from-file=config/production.env.json

# Android release (signing via CI secrets — do not commit keystores)
flutter build appbundle --release --flavor production \
  --dart-define-from-file=config/production.env.json

# iOS (no codesign locally / CI readiness)
flutter build ios --no-codesign \
  --dart-define-from-file=config/production.env.json
```

Release builds **reject** `DEMO_MODE=true` and localhost API URLs (`ReleaseGuards`).

## Tests

```bash
flutter test
dart run tool/verify_mobile_phase1.dart
```

## Docs

- `docs/ENVIRONMENT_SETUP.md`
- `docs/MOBILE_TOKEN_SECURITY.md`
- `docs/MOBILE_SECURITY.md`
- `docs/ANDROID_RELEASE.md`
- `docs/IOS_RELEASE.md`
- `docs/PHASE_1_FOUNDATION.md`

## Gate

**STOP after Phase 1.** Do not start Phase 2 (patient portal product flows) or Phase 3 (collector field workflows) until production verification / approval.
