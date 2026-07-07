# SMTP Setup (Pilot Safe Degradation)

DxCon supports SMTP email notifications but **does not require live SMTP** to pass internal pilot readiness.

## Modes

### 1) Dry-run mode (recommended for internal pilot)

Set:

```bash
EMAIL_DRY_RUN=true
```

Behavior:
- `/health` reports `email.status=DEGRADED` if `SMTP_HOST` missing
- `/ready` stays **OK** for internal pilot
- Email payloads are **not sent**; they should be recorded via audit / notification events

### 2) SMTP configured mode (required for customer pilot)

Set:

```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
SMTP_FROM=...
SMTP_USE_TLS=true
EMAIL_DRY_RUN=false
```

## Verification

- `GET /api/v1/system/health` includes:
  - `email.status` (`OK` / `DEGRADED`)
  - `email.dry_run` (`true` / `false`)
- `GET /api/v1/system/ready` includes the same `email` object

