# Staging Pilot Accounts — Release 9.0

**No passwords in Git.** Store credentials in a password manager / vault.

---

## Roles

| Key | Default email (overridable) | Env email | Env password | Workspace |
|---|---|---|---|---|
| super_admin | `admin@staging.dxcon.local` | `STAGING_ADMIN_EMAIL` | `STAGING_ADMIN_PASSWORD` | `/app/admin` |
| reception | `reception@staging.dxcon.local` | `STAGING_RECEPTION_EMAIL` | `STAGING_RECEPTION_PASSWORD` | `/app/reception` |
| collector | `collector@staging.dxcon.local` | `STAGING_COLLECTOR_EMAIL` | `STAGING_COLLECTOR_PASSWORD` | `/app/collector` |
| lab_technician | `lab@staging.dxcon.local` | `STAGING_LAB_EMAIL` | `STAGING_LAB_PASSWORD` | `/app/lab` |
| doctor | `doctor@staging.dxcon.local` | `STAGING_DOCTOR_EMAIL` | `STAGING_DOCTOR_PASSWORD` | `/app/doctor` |
| clinic | `clinic@staging.dxcon.local` | `STAGING_CLINIC_EMAIL` | `STAGING_CLINIC_PASSWORD` | `/app/clinic` |
| patient | `patient@staging.dxcon.local` | `STAGING_PATIENT_EMAIL` | `STAGING_PATIENT_PASSWORD` | `/app/patient` |

All data is **synthetic**. No real person names or PHI.

---

## Bootstrap

```bash
export APP_ENV=staging
export DATABASE_URL="<STAGING_POSTGRESQL_URL>"

# Plan
python backend/scripts/bootstrap_staging_pilot.py --dry-run

# Create (passwords from env, or one-time generate)
python backend/scripts/bootstrap_staging_pilot.py --apply
# or
python backend/scripts/bootstrap_staging_pilot.py --apply --generate-missing-passwords
```

Guards:

- Refuses `APP_ENV=production`
- Idempotent (skips existing emails)
- Does not re-print passwords after creation unless newly generated with `--generate-missing-passwords`

Report: `generated-release/STAGING_BOOTSTRAP_REPORT.json`

---

## Tenant isolation notes

For UAT-15 create a **second organization** via admin UI after login (do not hardcode second-org secrets in Git). Keep Patient A / Patient B in separate accounts for isolation tests.
