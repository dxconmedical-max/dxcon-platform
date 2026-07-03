# Demo Seed Runbook

Operational runbook for loading and verifying the DxCon demo dataset.

## Prerequisites

- `DATABASE_URL` configured and reachable
- Application migrations/tables present
- Backup taken before applying to shared staging/production

## 1. Dry run (required first)

```bash
cd backend
export DATABASE_URL=postgresql://...
python scripts/seed_demo_data.py --dry-run
```

Review:

- `backend/generated_release/DEMO_SEED_REPORT.json`
- planned `created_counts`
- any `skipped_models`

Dry run does **not** write data.

## 2. Apply demo data

```bash
cd backend
python scripts/seed_demo_data.py --apply
```

The seed is **idempotent**. Re-running `--apply` only creates missing demo rows.

## 3. Verify created records

```bash
python scripts/seed_demo_data.py --summary
python scripts/verify_demo_readiness.py
python scripts/smoke_production_api.py --base-url https://dxcon-ap.onrender.com
```

Check report fields:

- `created_counts`
- `existing_counts`
- `errors` must be empty

SQL spot checks (PostgreSQL example):

```sql
SELECT count(*) FROM users WHERE email LIKE 'demo-%@demo.dxcon.test';
SELECT count(*) FROM patients WHERE patient_code LIKE 'DEMO-PAT-%';
SELECT count(*) FROM orders WHERE order_code LIKE 'DEMO-ORD-%';
```

## Demo accounts

| Purpose | Email | Password |
|---------|-------|----------|
| Super Admin | `demo-superadmin@demo.dxcon.test` | `DemoPass123!` |
| Admin/Staff | `demo-admin-01@demo.dxcon.test` .. `demo-admin-05@demo.dxcon.test` | `DemoPass123!` |
| Doctors | `demo-doctor-01@demo.dxcon.test` .. `demo-doctor-10@demo.dxcon.test` | `DemoPass123!` |

Deterministic record prefixes:

- `DEMO-LAB-*`, `DEMO-CLN-*`, `DEMO-PAT-*`, `DEMO-TST-*`, `DEMO-ORD-*`, `DEMO-COL-*`, `DEMO-SHP-*`, `DEMO-INV-*`, `DEMO-NOT-*`

## Render execution

1. Open Render shell for the web service or run a one-off job with linked PostgreSQL.
2. Ensure `DATABASE_URL` is exported.
3. Run dry-run, then apply, then summary.
4. Hit `/` and `/health` on the public URL to confirm demo landing and probes.

## Safety warnings

- **Never** run destructive delete/truncate in production.
- This pack does not remove demo rows automatically.
- Use `--dry-run` before every environment.
- Prefer staging first; apply to production only for controlled pilot demos.
- Rotate demo passwords after public demos if needed.

## Rollback

Restore from backup or redeploy a known-good database snapshot. Do not attempt manual mass delete in production without an approved maintenance window.

## Related docs

- `backend/docs/DEMO_SEED_DATA.md`
- `backend/docs/PRODUCTION_SMOKE_TEST.md`
