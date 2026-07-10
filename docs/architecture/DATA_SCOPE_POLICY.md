# Data Scope Policy — Release 2.0

## Scope levels

| Scope | Description | Who |
|-------|-------------|-----|
| **Platform** | All organizations | SUPER_ADMIN, SYSTEM_ADMIN |
| **Organization** | Single tenant | ADMIN, LAB, DOCTOR, etc. |
| **Self** | Own patient/profile | PATIENT |
| **Resource** | Specific entity by ID + org check | All roles |

## Rules

1. Every query on tenant-owned data filters by `organization_id` from JWT.
2. Patients see only their own bookings, results, payments.
3. Partners see only their organization's listings, bookings, messages.
4. Listing public profiles expose only approved public fields.
5. Global scope requires platform role and is audited.

## ABAC foundation

Attribute checks (organization membership, resource ownership, listing status ACTIVE) combine with RBAC permissions. ABAC conditions are evaluated server-side in service layer.

## Feature flags

Feature flags gate optional capabilities but do not replace permission checks.
