# Authorization Freeze — Release 2.0

## Decision model

1. **Backend is authoritative** — all protected routes enforce permissions server-side.
2. **Role alone never grants access** — role maps to permissions; permissions gate resources.
3. **Frontend hiding is not security** — UI uses capabilities for UX only.
4. **Tenant isolation** — organization_id from token scopes all queries.
5. **Global scope** — platform SUPER_ADMIN / SYSTEM_ADMIN only.

## Registries

| Registry | Path |
|----------|------|
| Global role permissions | `app/core/permissions.py` |
| Org-scoped RBAC | `app/partner_foundation/rbac.py` |
| Integration permissions | `app/integration/constants.py` |
| MDM gates | `app/mdm/security.py` |

## Enforcement

- `@permission_required(...)` and `@roles_required(...)` in `app/core/authz.py`
- Integration routes: `app/integration/security/__init__.py`
- Marketplace (Epic 5): `MARKETPLACE_*`, `PAYMENT_*` permissions

## Audit format

Authorization denials are logged with actor, organization, resource, permission attempted, outcome `DENIED`.

## Cross-tenant access

Explicitly prohibited unless platform admin with audit trail. Partner data never crosses organization boundaries.

## Verification

```bash
python backend/scripts/verify_permission_registry.py
```

See `AUTHORIZATION_FREEZE_REPORT.json`.
