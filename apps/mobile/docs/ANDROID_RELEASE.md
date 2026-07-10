# Android Release

- **Application ID:** `vn.com.dxcon.mobile`
- **App name:** DxCon

## Permissions

Internet, camera, location, notifications (see `AndroidManifest.xml`).

## Network security

`res/xml/network_security_config.xml` — cleartext disabled.

## Deep links

- `dxcon://`
- `https://app.dxcon.com.vn`

## Signing

Do **not** commit keystore or passwords.
Configure release signing in CI via secrets.
Debug builds use debug keystore.

## Notification channels

Configure per category when FCM is enabled (booking, collector, payment, etc.).
