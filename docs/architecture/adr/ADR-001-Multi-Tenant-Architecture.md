# ADR-001 Multi-Tenant Architecture

**Status:** Accepted (Frozen Release 2.0)

## Context

DxCon serves multiple laboratories, clinics, and partners on one platform.

## Decision

- Every business entity is scoped by `organization_id`.
- JWT carries active organization context.
- Cross-tenant access is denied by default.

## Consequences

- All new tables must include tenant column or be explicitly exempt.
- Queries must filter by organization from token.
