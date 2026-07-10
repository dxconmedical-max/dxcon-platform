# Permission Naming Convention — Release 2.0

## Format

```
<resource>.<action>
```

Examples: `patients.read`, `orders.write`, `report.release`, `webhooks.manage`

## Epic-specific permissions

### Integration (Epic 3.5)
- `INTEGRATION_VIEW`, `INTEGRATION_MANAGE`, `CONNECTOR_MANAGE`, `MAPPING_MANAGE`, `MESSAGE_RETRY`, `WEBHOOK_MANAGE`, `API_CREDENTIAL_MANAGE`

### Marketplace (Epic 5)
- `MARKETPLACE_VIEW`, `MARKETPLACE_LISTING_MANAGE`, `MARKETPLACE_LISTING_APPROVE`, `MARKETPLACE_PRICE_MANAGE`, `PROMOTION_MANAGE`, `PAYMENT_VIEW`, `PAYMENT_RECONCILE`

## Registration rules

1. New permissions must be added to a central registry (`permissions.py` or domain `constants.py`).
2. `verify_permission_registry.py` must pass after adding permissions.
3. Permissions used in routes must be registered (guardrail).
4. Wildcard `*` reserved for SUPER_ADMIN only.

## Role templates

Roles are templates mapping to permission sets. Custom org roles extend via `partner_foundation/rbac.py`.
