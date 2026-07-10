# ADR-002 PostgreSQL as Primary Database

**Status:** Accepted (Frozen Release 2.0)

## Decision

PostgreSQL is the production database. SQLite is test-only.

## Consequences

- Migrations are SQL files applied in order.
- JSONB used where flexible metadata needed.
