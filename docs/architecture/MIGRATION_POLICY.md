# Migration Policy — Release 2.0

## Requirements

Every migration must:

1. Be additive and idempotent where possible (`IF NOT EXISTS`).
2. Include a rollback note in the migration header comment.
3. Pass `verify_architecture_freeze.py` destructive-SQL guardrail.
4. Be applied in numeric order on production PostgreSQL.

## Prohibited in Release 2.x

- `DROP TABLE` on production tables
- `DROP COLUMN` without compatibility period
- `TRUNCATE` on business data
- Data migrations that destroy audit history

## Rollback notes

Each migration file should document:

```sql
-- Rollback: manual — drop new tables only if empty and no dependent data
```

## Application

Migrations are applied via deployment pipeline or `production_readiness_lib.apply_migrations()` subset during verification. Production applies full migration set before release.

## Schema evolution

See `SCHEMA_EVOLUTION_POLICY.md` for canonical JSON schema versioning.
