# Sprint 005 — Multi-Tenant Organization & Partner Foundation

## Goal

Introduce Organization layer, Partner Platform, tenant isolation, and organization-based RBAC without breaking Business Engine or Master Data.

## Modules

1. **Organization** — `organizations` table, CRUD via `/api/v1/partner/organizations`
2. **Organization User** — memberships in `organization_users`, invite/disable
3. **Partner Portals** — `/app/partner`, `/app/clinic`, `/app/corporate`, `/app/insurance`, `/app/partner/doctor`
4. **Dashboards** — clinic, doctor, corporate, insurance widget layouts
5. **RBAC** — `organization_roles` + permission matrix
6. **Isolation** — opt-in `organization_id` filters; nullable columns for backward compatibility
7. **Contracts** — `partner_contracts`
8. **Price Lists** — `organization_price_lists` with tier fallback
9. **Audit** — `organization.*` actions in `audit_logs`
10. **Admin UI** — `/app/admin/*` menu
11. **API** — `/api/v1/partner/*`
12. **Migration** — `004_partner_foundation.sql`

## Verify

```bash
python -m compileall backend/app backend/scripts backend/tests
python -m unittest discover -s backend/tests -v -k partner_foundation
python backend/scripts/verify_partner_foundation.py
```

## Reports

- `generated_release/PARTNER_FOUNDATION_REPORT.json`
- `generated_release/RBAC_REPORT.json`
- `generated_release/TENANT_SECURITY_REPORT.json`
