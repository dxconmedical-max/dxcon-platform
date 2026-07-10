# ADR-004 Enterprise Authorization

**Status:** Accepted (Frozen Release 2.0)

## Decision

RBAC + ABAC with backend-enforced permissions. Role templates map to fine-grained permissions.

## Consequences

- `permission_required` on protected routes.
- Frontend capabilities are UX-only.
