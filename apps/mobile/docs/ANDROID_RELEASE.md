# Android Release

- **Application ID:** `vn.com.dxcon.mobile` (production flavor)
- **Flavors:** `development` (`.dev`), `staging` (`.staging`), `production`
- **App name:** DxCon (flavor overrides via `app_name`)

## Permissions

Internet, camera, location, notifications (see `AndroidManifest.xml`).
Phase 1 login only requires Internet; other permissions are declared for later phases and remain unused until those features ship.

## Network security

`res/xml/network_security_config.xml` — cleartext disabled.

## Deep links

- `dxcon://`
- `https://app.dxcon.com.vn`

## Build

```bash
flutter build apk --flavor production \
  --dart-define-from-file=config/production.env.json
```

## Signing

Do **not** commit keystore or passwords.
Configure release signing in CI via secrets.
Debug builds use debug keystore.

## Notification channels

Configure per category when FCM is enabled (booking, collector, payment, etc.).
