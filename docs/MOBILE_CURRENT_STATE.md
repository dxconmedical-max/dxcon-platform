# Mobile Current State — Release 9.0

**Inspected:** `apps/mobile/`

---

## Framework

| Question | Answer |
|---|---|
| React Native? | No |
| Expo? | No |
| Flutter? | **Yes** — `apps/mobile/pubspec.yaml` (`dxcon_mobile`, SDK ^3.12.2) |
| Duplicates? | Single Flutter monorepo app with multi-role features |

---

## Existing product surface

| Area | Path |
|---|---|
| Patient | `lib/features/patient/` |
| Collector | `lib/features/collector/` |
| Lab | `lib/features/lab/` |
| Doctor / Clinic / Admin / Executive | under `lib/features/` |
| Auth | `lib/features/auth/` + Dio API client |
| Secure storage | `flutter_secure_storage` |
| Offline | `hive` / connectivity packages present |
| Camera / QR | `mobile_scanner`, `image_picker` |
| Push | `firebase_messaging` abstraction present |

---

## Environments

Configured via `--dart-define` (`lib/config/environment.dart`): `APP_ENV`, `API_BASE_URL`, `DEMO_MODE`. Defaults already target production API host — staging builds must inject staging URL.

---

## Status

| Item | Status |
|---|---|
| Valid mobile codebase exists | PASS |
| Create a second framework app | **Do not** |
| Full mobile feature delivery | NOT_STARTED (foundation prep only this release) |
