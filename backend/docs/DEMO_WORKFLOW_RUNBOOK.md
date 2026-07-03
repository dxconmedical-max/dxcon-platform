# Demo Workflow Runbook

Pilot runbook for DxCon live demo and workflow verification after demo seed data is applied.

## Demo URL

- Production/staging: `https://dxcon-ap.onrender.com/`
- Local: `http://127.0.0.1:5000/`

## Demo dashboards

| Dashboard | Route |
|-----------|-------|
| Landing | `/` |
| Executive | `/executive-v9` |
| CRM Pipeline | `/crm-pipeline` |
| Logistics | `/logistics` |
| Reception | `/reception` |
| Doctor Workbench | `/doctor/dashboard` |
| Patient Portal Demo | `/patient/demo` |
| Collector Portal | `/collector` |

## Demo accounts

| Role | Email pattern | Password |
|------|---------------|----------|
| Super Admin | `demo-superadmin@demo.dxcon.test` | `DemoPass123!` |
| Admin/Staff | `demo-admin-01@demo.dxcon.test` .. `demo-admin-05@demo.dxcon.test` | `DemoPass123!` |
| Doctors | `demo-doctor-01@demo.dxcon.test` .. `demo-doctor-10@demo.dxcon.test` | `DemoPass123!` |

Demo code prefixes: `DEMO-PAT-*`, `DEMO-ORD-*`, `DEMO-TST-*`, `DEMO-LAB-*`, `DEMO-SHP-*`.

## Workflow scripts

```bash
cd backend
python3 scripts/seed_demo_data.py --dry-run
python3 scripts/seed_demo_data.py --apply
python3 scripts/seed_demo_data.py --summary
python3 scripts/verify_demo_workflow.py
python3 scripts/verify_demo_readiness.py
python3 scripts/smoke_production_api.py
```

Reports:

- `backend/generated_release/DEMO_SEED_REPORT.json`
- `backend/generated_release/DEMO_WORKFLOW_REPORT.json`
- `backend/generated_release/DEMO_READINESS_REPORT.json`
- `backend/generated_release/PRODUCTION_SMOKE_REPORT.json`

## Known limitations

- Redis may report `DEGRADED` on Render while app remains `OK`.
- CRM leads/opportunities may be absent; CRM dashboard shows billing placeholders.
- Logistics falls back to sample collections, shipments, or demo order status when tracking tables are empty.
- Doctor result review is a placeholder until lab results are seeded.
- Patient portal demo opens individual patients via `?patient_id=DEMO-PAT-001`.
- Seed script never calls `db.create_all()` in staging/production.

## Pilot checklist

- [ ] `/health`, `/ready`, and `/live` return JSON status `OK`
- [ ] Landing page links open all demo dashboards
- [ ] Executive dashboard shows user/patient/test/order totals
- [ ] Reception dashboard lists recent demo patients and orders
- [ ] Logistics dashboard shows collections, shipments, or order fallback
- [ ] Doctor workbench lists recent demo orders
- [ ] Patient portal demo lists demo patients and sample orders
- [ ] `verify_demo_workflow.py` passes locally and on Render shell
- [ ] Demo login works for super admin and doctor accounts

## Rollback warning

Demo seed data is additive and idempotent. Do not truncate production tables. Remove demo rows only in controlled non-production environments.
