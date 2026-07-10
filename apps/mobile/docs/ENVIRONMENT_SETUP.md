# DxCon Mobile — Environment Setup

## Environments

| Environment | `APP_ENV` | API |
|-------------|-----------|-----|
| development | `development` | local or staging |
| testing | `testing` | test stack |
| staging | `staging` | staging API |
| production | `production` | `https://api.dxcon.com.vn` |

## Production defaults (compile-time)

```
API_BASE_URL=https://api.dxcon.com.vn
PUBLIC_SITE_URL=https://dxcon.com.vn
WEB_APP_URL=https://app.dxcon.com.vn
APP_ENV=production
DEMO_MODE=false
```

## Run with dart-define

```bash
flutter run \
  --dart-define=API_BASE_URL=https://api.dxcon.com.vn \
  --dart-define=APP_ENV=production \
  --dart-define=DEMO_MODE=false
```

## Secrets

Never commit API keys, Firebase config secrets, Sentry DSN, or signing credentials.
Use CI secrets and local untracked files for `google-services.json` and `GoogleService-Info.plist`.
