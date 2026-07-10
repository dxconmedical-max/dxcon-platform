# ADR-006 Event-Driven Extension

**Status:** Accepted (Frozen Release 2.0)

## Decision

Domain events with frozen envelope enable async integrations and notifications.

## Consequences

- EventBus persists events.
- New features subscribe without modifying core write paths.
