# ADR-009 Mobile Strategy

**Status:** Accepted (Frozen Release 2.0)

## Decision

Mobile clients consume frozen `/api/v1/` contract. Native apps are API consumers, not separate business logic.

## Consequences

- Pagination, idempotency, error contract required on patient APIs.
- Push notification token registration as foundation.
