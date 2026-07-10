# Schema Evolution Policy — Release 2.0

## Rules

1. **Additive by default** — new optional fields in v1.0 schemas.
2. **Version field required** on canonical payloads crossing integration boundaries.
3. **Consumers tolerate unknown fields**.
4. **Producers must not remove required fields** without version bump.
5. **Database columns** follow `MIGRATION_POLICY.md` (additive only in 2.x).

## Version bump triggers

- Renaming canonical field
- Changing field type semantics
- Making optional field required
- Removing field

## Migration path

1. Publish new schema version (e.g. 2.0).
2. Support both versions during transition.
3. Deprecate old version with sunset date.
4. Update integration mapping rules per connector.
