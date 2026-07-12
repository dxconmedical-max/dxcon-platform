# Pilot account setup

Pilot accounts are created with `backend/scripts/prepare_pilot_accounts.py`.

## Safety rules

- **Never** run `--apply` when `APP_ENV=production`
- **Never** hardcode passwords in source code
- Provide credentials via environment variables only
- Script is idempotent (existing emails are skipped)

## Required environment variables

| Variable | Role |
|----------|------|
| `PILOT_ADMIN_EMAIL` / `PILOT_ADMIN_PASSWORD` | DxCon admin |
| `PILOT_CLINIC_OWNER_EMAIL` / `PILOT_CLINIC_OWNER_PASSWORD` | Clinic owner |
| `PILOT_DOCTOR_EMAIL` / `PILOT_DOCTOR_PASSWORD` | Partner doctor |
| `PILOT_LAB_MANAGER_EMAIL` / `PILOT_LAB_MANAGER_PASSWORD` | Lab manager |
| `PILOT_COLLECTOR_EMAIL` / `PILOT_COLLECTOR_PASSWORD` | Collector |
| `PILOT_PATIENT_EMAIL` / `PILOT_PATIENT_PASSWORD` | Patient |

Also required: `DATABASE_URL`

## Usage

```bash
cd backend
export DATABASE_URL=postgresql://...
export PILOT_ADMIN_EMAIL=admin@pilot.example
export PILOT_ADMIN_PASSWORD='temporary-password-change-me'
# ... other PILOT_* vars

python scripts/prepare_pilot_accounts.py --dry-run
python scripts/prepare_pilot_accounts.py --apply
```

Report: `backend/generated_release/PILOT_ACCOUNT_PREP_REPORT.json`

## First-login password change

Require users to change temporary passwords through your organization policy. Backend password reset email flow may return `501` until SMTP reset is enabled.
