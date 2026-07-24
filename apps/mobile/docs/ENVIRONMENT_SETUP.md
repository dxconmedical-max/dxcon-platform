# DxCon Mobile — Environment Setup

## Environments

| Environment | `APP_ENV` | Flavor | API (default) |
|-------------|-----------|--------|---------------|
| development | `development` | `development` | local / emulator (`config/development.env.json`) |
| staging | `staging` | `staging` | staging API |
| production | `production` | `production` | `https://api.dxcon.com.vn` |

## Compile-time config (no secrets in source)

Checked-in templates (non-secret URLs only):

- `config/development.env.json`
- `config/staging.env.json`
- `config/production.env.json`

Local secret overrides (gitignored): `config/local/`

```bash
flutter run --flavor production \
  --dart-define-from-file=config/production.env.json

# Optional: merge a local untracked file for Sentry DSN etc.
flutter run --flavor staging \
  --dart-define-from-file=config/staging.env.json \
  --dart-define=SENTRY_DSN="$SENTRY_DSN"
```

## Production defaults

```
API_BASE_URL=https://api.dxcon.com.vn
PUBLIC_SITE_URL=https://dxcon.com.vn
WEB_APP_URL=https://app.dxcon.com.vn
APP_ENV=production
DEMO_MODE=false
ANALYTICS_ENABLED=false
SENTRY_DSN=   # empty → crash reporting no-op
```

## Secrets policy

Never commit API keys, Firebase config secrets, Sentry DSN, or signing credentials.
Use CI secrets and local untracked files for `google-services.json` and `GoogleService-Info.plist`.

## Release guards

`ReleaseGuards.assertSafeForRelease()` fails release builds when `DEMO_MODE=true` or API URL targets localhost.
