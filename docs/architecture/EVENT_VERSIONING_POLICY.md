# Event Versioning Policy — Release 2.0

## Version format

`event_version`: `"1.0"`, `"1.1"`, `"2.0"` (semantic versioning)

## Compatibility

| Change | Version bump |
|--------|--------------|
| Add optional payload field | 1.0 → 1.1 (minor) |
| Remove payload field | 2.0 (major) |
| Change field type | 2.0 (major) |
| Rename event_type | New event name (do not repurpose) |

## Consumer requirements

1. Subscribe by `event_type` + supported `event_version` range.
2. Tolerate additional optional fields.
3. Dead-letter unparseable events to integration exception queue.

## Producer requirements

1. Include full envelope on every emit.
2. Never log full `payload` for clinical events.
3. Register new events in `DOMAIN_EVENT_CATALOG.md`.
