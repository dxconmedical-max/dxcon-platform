# Mobile Security

## Implemented

- Secure token storage (Keychain / EncryptedSharedPreferences)
- TLS-only network security config (Android)
- Demo mode disabled in production builds
- Deep-link validation (`dxcon://` and `app.dxcon.com.vn`)
- Open redirect detection
- QR URL scans require confirmation before navigation
- Session timeout via token expiry + 401 handling
- Logout cache purge (secure storage + tenant Hive boxes)
- Analytics and crash reporting exclude PHI and credentials

## Readiness (not fully enabled)

- Certificate pinning
- Screenshot protection on sensitive screens
- Background blur for protected content
- Root/jailbreak blocking

## Clipboard

Avoid copying tokens or clinical data to clipboard; use secure viewers for PDFs.
