# ADR-010 Clinical Record Immutability

**Status:** Accepted (Frozen Release 2.0)

## Decision

Released reports and approved results are immutable. Amendments create new versions.

## Consequences

- State machine blocks backward transitions from RELEASED.
- Imported results require validation before release.
