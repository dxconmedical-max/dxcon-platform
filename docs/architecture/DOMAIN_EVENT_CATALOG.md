# Domain Event Catalog — Release 2.0

## Event envelope (frozen)

| Field | Required | Description |
|-------|----------|-------------|
| event_id | yes | UUID |
| event_type | yes | Dot-notation name |
| event_version | yes | Semver e.g. `1.0` |
| occurred_at | yes | ISO 8601 UTC |
| organization_id | yes | Tenant scope |
| actor_id | yes | User or system actor |
| correlation_id | no | Request/trace chain |
| causation_id | no | Parent event id |
| resource_type | yes | e.g. Order, Sample |
| resource_id | yes | Entity id |
| payload | yes | Event-specific data (no PHI in logs) |
| metadata | no | Safe diagnostic metadata |

## Core events (frozen names)

- patient.created
- order.created, order.confirmed
- payment.confirmed
- collection.assigned
- sample.collected, sample.in_transit, sample.received, sample.rejected
- result.entered, result.validated
- report.approved, report.released
- appointment.created
- consultation.requested
- prescription.created
- incident.created

## Legacy implementation mapping

Current `DomainEvent` dataclass uses PascalCase types (`PatientCreated`, `OrderCreated`, ...). New emitters should migrate to dot-notation with full envelope. See `DOMAIN_EVENT_FREEZE_REPORT.json`.

## Rules

1. Event names cannot be repurposed.
2. Breaking payload changes require new `event_version`.
3. Consumers must ignore unknown fields.
4. Medical payloads must not be logged in plain text.

## Implementation

- `app/events/domain_event.py` — dataclass
- `app/events/event_bus.py` — persist + dispatch
- `app/core/statuses.py` — `VALID_DOMAIN_EVENTS`
