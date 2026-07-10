# API Versioning Policy — Release 2.0

## Principles

1. **URL versioning** — major version in path (`/api/v1/`, `/api/v2/`).
2. **Additive evolution** — STABLE v1 endpoints accept new optional fields.
3. **Explicit deprecation** — deprecated endpoints document replacement and sunset date.
4. **OpenAPI as inventory** — `backend/generated_api/openapi.json` is the machine-readable contract.

## When to create v2

- Removing or renaming request/response fields
- Changing field semantics (type coercion not sufficient)
- Changing authentication requirements for existing clients
- Changing error code meaning for existing clients

## Deprecation process

1. Mark endpoint `DEPRECATED` in inventory and OpenAPI `deprecated: true`.
2. Add response header `Sunset: <RFC 8594 date>`.
3. Document replacement in `API_V1_FREEZE.md`.
4. Maintain deprecated endpoint for at least one pilot cycle.
5. Remove only in next major release with migration guide.

## Client guidance

- Clients must tolerate unknown JSON fields.
- Clients must not depend on undocumented fields.
- Mobile and web clients pin to `/api/v1/` until v2 migration is announced.

## Related documents

- `API_V1_FREEZE.md`
- `ERROR_CONTRACT.md`
- `FRONTEND_CONTRACT_FREEZE.md`
- `MOBILE_API_CONTRACT.md`
