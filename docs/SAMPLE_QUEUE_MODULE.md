# Sample Queue — Release 2 Step 8

**Status:** Implemented  
**Scope:** Sample logistics queue, realtime tracking, history, audit  
**Out of scope:** Full Flutter collector field app (M8 / M11)

---

## Workflow

```
Collected → Transport → Received → Sorting → Laboratory → Completed
```

Enqueue requires a collection job; may auto accept/collect when `sync_collection` is true.

Early advances sync Business Engine logistics:

| Stage | Sync |
|-------|------|
| transport | `handover_sample` |
| received | `receive_sample_at_lab` |
| laboratory | `ensure_lab_queue_item` (best effort) |

---

## Models

- `BizSampleQueueItem` — current stage + timestamps
- `BizSampleQueueEvent` — immutable history

Migration: `backend/migrations/019_sample_queue.sql`

---

## Service

`backend/app/reception_workspace/sample_queue_engine.py`

- `ensure_sample_queue_item` / `advance_sample_queue`
- `track_sample` / `update_sample_tracking` / `get_sample_queue_history`
- `sample_queue_dashboard` / `sample_queue_refresh` (version token)
- Audit via `write_reception_audit` (`sample_queue_entered|advanced|tracking`)

---

## APIs (`/api/v1/reception/workspace`)

| Method | Path |
|--------|------|
| GET | `/sample-queue` |
| GET | `/sample-queue/stats` |
| GET | `/sample-queue/refresh?version=` |
| POST | `/sample-queue/orders/:ref/enqueue` |
| POST | `/sample-queue/orders/:ref/advance` |
| GET | `/sample-queue/orders/:ref/track` |
| GET | `/sample-queue/orders/:ref/history` |
| POST | `/sample-queue/orders/:ref/tracking` |

---

## UI

- Page: `/app/reception/m2/sample-queue`
- Component: `SampleQueueWorkbench` — board, live poll (5s), track + history panel

---

## Tests

`backend/tests/test_sample_queue_engine.py`
