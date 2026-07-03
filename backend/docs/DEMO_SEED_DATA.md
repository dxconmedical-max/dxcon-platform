# Demo Seed Data

Idempotent demo dataset for DxCon staging and production demos.

## Safety rules

- **Never** run destructive delete/truncate in production.
- The seed script only **creates missing rows** using deterministic demo codes/emails.
- Running the script multiple times does **not** duplicate demo records.
- Use `--dry-run` first on every environment.

## Run locally

```bash
export DATABASE_URL=sqlite:///dxcon.db
python -m compileall -q backend/app backend/scripts backend/tests
python backend/scripts/seed_demo_data.py --dry-run
python backend/scripts/seed_demo_data.py --apply
python backend/scripts/seed_demo_data.py --summary
```

## Run on Render

1. Open the Render web service shell (or one-off job) with `DATABASE_URL` linked to PostgreSQL.
2. Run:

```bash
cd backend
python scripts/seed_demo_data.py --dry-run
python scripts/seed_demo_data.py --apply
python scripts/seed_demo_data.py --summary
```

3. Review `backend/generated_release/DEMO_SEED_REPORT.json`.

## Expected demo accounts

| Account | Email | Role |
|---------|-------|------|
| Super Admin | `demo-superadmin@demo.dxcon.test` | `SUPER_ADMIN` |
| Admin/Staff | `demo-admin-01@demo.dxcon.test` .. `demo-admin-05@demo.dxcon.test` | `ADMIN` / `ACCOUNTING` |
| Doctors | `demo-doctor-01@demo.dxcon.test` .. `demo-doctor-10@demo.dxcon.test` | `DOCTOR` |

Default demo password: `DemoPass123!`

Deterministic code prefixes:

- `DEMO-LAB-*` laboratories
- `DEMO-CLN-*` clinic partners
- `DEMO-PAT-*` patients
- `DEMO-TST-*` test catalog
- `DEMO-ORD-*` orders
- `DEMO-COL-*` collectors/drivers
- `DEMO-SHP-*` shipments
- `DEMO-INV-*` invoices
- `DEMO-NOT-*` notifications

## Minimum dataset targets

| Domain | Target |
|--------|--------|
| Super Admin users | 1 |
| Admin/Staff users | 5 |
| Doctors | 10 |
| Laboratories | 5 |
| Clinics/Partners | 10 |
| Patients | 100 |
| Test catalog items | 200 |
| Orders | 50 |
| Order items | 50 |
| Sample collections | 20 |
| Collectors/Drivers | 10 |
| Shipments | 20 |
| Invoices | 10 |
| Notifications | 10 |

Optional models/tables that are missing are skipped and recorded in the report as:

```json
{"skipped": true, "reason": "model_not_found"}
```

or

```json
{"skipped": true, "reason": "table_not_found"}
```

## Rollback warning

This pack does **not** delete demo data automatically. To remove demo rows, restore from backup or run a controlled manual cleanup in a non-production environment only.

## Report output

`backend/generated_release/DEMO_SEED_REPORT.json`

Fields:

- `created_counts`
- `existing_counts`
- `skipped_models`
- `errors`
- `runtime_seconds`
