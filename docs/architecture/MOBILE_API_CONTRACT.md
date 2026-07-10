# Mobile API Contract — Release 2.0

## Base URL

`https://api.dxcon.com.vn/api/v1/`

## Requirements

| Requirement | Contract |
|-------------|----------|
| Versioning | `/api/v1/` prefix frozen |
| Pagination | `page`, `per_page` or `limit`/`offset`; response includes `count` |
| Idempotency | `Idempotency-Key` header on POST mutations |
| Errors | `ERROR_CONTRACT.md` envelope |
| File upload | Max size per endpoint docs; multipart/form-data |
| Notifications | Device token registration endpoint (foundation) |
| Deep links | `booking_code`, `order_code`, `payment_reference` |

## Offline-safe mutations

Where supported, clients may queue requests with idempotency keys; server deduplicates.

## Authentication

Bearer JWT from `/api/v1/auth/login`. Refresh via `/api/v1/auth/refresh`.

## Patient-facing endpoints

- Marketplace search and booking
- Payment status polling
- Booking history
- Released results (permission-gated)

## Security

- TLS required
- Certificate pinning recommended for mobile apps
- No secrets in app bundle
