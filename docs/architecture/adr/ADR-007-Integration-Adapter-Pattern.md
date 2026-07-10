# ADR-007 Integration Adapter Pattern

**Status:** Accepted (Frozen Release 2.0)

## Decision

Vendor-neutral `ConnectorAdapter` per protocol. No vendor logic in clinical modules.

## Consequences

- Epic 3.5 `app/integration/` is the integration foundation.
- Foundation adapters must not claim false production readiness.
