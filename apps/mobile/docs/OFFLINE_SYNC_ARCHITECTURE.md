# Offline Sync Architecture

## Cached data (tenant-scoped keys)

- Safe reference data
- Assigned collector jobs
- Patient booking summaries
- Released report metadata

## Sync queue

Operations queued with `idempotency_key` and exponential backoff.
Statuses: PENDING, SYNCING, SUCCEEDED, FAILED, CONFLICT, CANCELLED.

## Rules

- Sensitive cache encrypted where platform supports it
- Clear cache on organization switch
- Never silently overwrite server state
- **No offline report release**
- **No offline final lab approval**
- Permanent validation failures are not auto-retried

## Persistence

Hive boxes: `dxcon_sync_queue`, `dxcon_cache`

## Scaling note

High-volume offline queues should migrate to background sync worker when platform worker is GA.
