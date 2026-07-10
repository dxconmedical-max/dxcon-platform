# iOS Release

- **Bundle ID:** `vn.com.dxcon.mobile`
- **Display name:** DxCon

## URL schemes

- `dxcon://` custom scheme
- Universal links readiness for `https://app.dxcon.com.vn`

## Usage descriptions

Camera, photo library, and location strings in `Info.plist`.

## Background modes

Prepared for location during active collector sessions — enable when product approves.

## Signing

Do **not** commit certificates or provisioning profiles.
Use Xcode Cloud or CI with App Store Connect API key.

## Push

Requires `GoogleService-Info.plist` and APNs configuration — currently `BLOCKED_BY_CONFIGURATION`.
