# Mobile Backend Guide (Phase 7.4)

## Overview

The Mobile Platform hub (`/mobile-platform`) documents and exposes backend capabilities for the Flutter client at `mobile/dxcon_mobile/`.

## API Surface

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/mobile-platform/readiness` | Platform readiness report |
| `GET /api/v1/mobile-platform/dashboard` | Feature matrix and config |
| `GET /api/v1/auth/*` | Authentication (existing) |
| `GET /api/v1/orders/*` | Orders (existing) |

## Client Configuration

Set `API_BASE_URL` in `mobile/dxcon_mobile/lib/core/config/api_config.dart` to your deployment host.

## Verification

`python scripts/verify_mobile_platform.py`
