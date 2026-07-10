# Release 2.0 Extension Rules

## Allowed without v2

1. New optional API fields on STABLE endpoints
2. New STABLE endpoints under existing `/api/v1/<domain>/`
3. New database tables and additive columns
4. New permissions registered centrally
5. New domain events with new names and versions
6. New marketplace listings, connectors, workspaces
7. New frontend pages under `/app/*` and `/marketplace/*`

## Requires architecture review

1. Removing or renaming API fields
2. Changing state machine transitions for released records
3. Cross-tenant data access patterns
4. New authentication methods
5. Destructive migrations

## Prohibited

1. Breaking Epic 2 authentication
2. Weakening tenant isolation
3. Bypassing clinical approval gates
4. Auto-releasing imported results
5. Secrets in source or logs
6. Removing stable API routes without deprecation cycle
7. Mock payment success in production runtime

## Process

1. Implement against frozen contracts
2. Run full regression + domain verify scripts
3. Update extension docs if adding new stable contract surface
4. One release commit per Epic (release isolation)
