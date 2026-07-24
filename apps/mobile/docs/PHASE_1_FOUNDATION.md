# Flutter Mobile — Phase 1 Foundation

**Gate:** Web go-live `f5d2f45` (P0=0).  
**Scope:** Architecture, env/flavors, secure session, login/logout, role routing, API client, errors, offline-safe reads.  
**Out of scope this run:** Phase 2 patient portal product, Phase 3 collector field product.

## Delivered

1. **Architecture** — Riverpod + go_router shells per workspace; Dio API client; Hive offline cache.
2. **Environment** — `--dart-define` / `config/*.env.json`; Android flavors `development` | `staging` | `production`.
3. **Secure storage** — Keychain / EncryptedSharedPreferences; no tokens in Hive; clear on logout.
4. **Auth** — Real `/api/v1/auth/login|logout|refresh|me|memberships|capabilities|switch-organization`.
5. **Role routing** — workspace → shell home (patient, collector, doctor, lab, clinic/reception, executive, admin).
6. **Errors** — Normalized `ApiError` (401/403/422/429/5xx/network/timeout).
7. **Offline-safe reads** — `OfflineReadCache` + `OfflineReader` serve TTL cache when offline or on network/5xx.
8. **Release guards** — No demo/mocks / localhost API in release builds.
9. **Analytics/crash** — Stub/off unless approved DSN/flags passed at build time.
10. **Tests + CI** — Unit tests + `tool/verify_mobile_phase1.dart`; `.github/workflows/mobile-ci.yml`.

## Explicit STOP

**Phase 1 complete for production verification.** Await approval before Phase 2.

## Phase 2 blockers (do not start yet)

- Patient portal UX and marketplace/booking product flows need product sign-off after Phase 1 auth verification on device.
- Push / Firebase remains `BLOCKED_BY_CONFIGURATION` (no committed `google-services.json` / `GoogleService-Info.plist`).
- Device token registration API gap (`POST /api/v1/mobile/devices`) — see `generated-release/MOBILE_BACKEND_GAPS.json`.
- Production Android signing keystore must be provisioned in CI secrets (not in repo).
- iOS provisioning / App Store Connect API key for release codesign.
- Certificate pinning recommended but not enabled until pin set is approved.
