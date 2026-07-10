# Release 2.0 Known Limitations

## Architecture

1. Domain event envelope not fully aligned with dataclass (gap documented in freeze report).
2. Permission registry split across multiple modules.
3. Dual integration APIs (`/integration` vs `integration_platform`) — use Epic 3.5 foundation for new work.
4. DB-backed retry queues — pilot-scale only.

## Identity

1. Password reset returns 501 without SMTP.
2. MFA not platform-wide.
3. Client-side token storage in web app.

## Clinical

1. Order state names in code differ slightly from frozen target names.
2. Full FHIR/HL7 conformance not claimed.

## Operations

1. Background worker placeholder for async jobs.
2. Operations Center module in progress, not fully wired.

## Marketplace (pre-Epic 5)

1. Legacy marketplace booking model lacks pricing snapshot and QR payment.
2. Public marketplace UI in Next.js not yet live on production domain.

These limitations are tracked; Epic 5 addresses marketplace gaps without changing frozen foundations.
