# ADR-011 Audit-First Design

**Status:** Accepted (Frozen Release 2.0)

## Decision

All security-relevant and clinical mutations produce audit records.

## Consequences

- No PHI in general application logs.
- Integration, marketplace, and auth events audited.
