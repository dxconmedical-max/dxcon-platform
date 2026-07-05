# White Label Guide (Phase 7.9)

## Purpose

Per-tenant branding via `TenantOrganizationSetting` keys: logo URL, primary color, app name, support email.

## Hub

- Web: `/white-label`
- API: `/api/v1/white-label/*`

## Brand Keys

Seeded by `ensure_white_label()` in the white label service.

## Verification

`python scripts/verify_white_label.py`
