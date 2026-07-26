# Laboratory Queue — Release 2 Step 7

**Status:** Implemented  
**Scope:** Lab queue after paid + barcode; waiting → processing → completed → verified; dashboard, priority, statistics, realtime refresh  
**Out of scope:** Full accession / medical validation depth (M7)

---

## Workflow

```
Paid → Barcode → Lab Queue → Waiting → Processing → Completed → Verified
```

Enqueue uses existing laboratory handoff (creates collection path → `lab_received`) and inserts `BizLabQueueItem` at **waiting**.

---

## Model

`BizLabQueueItem` (`biz_lab_queue_items`)

| Field | Notes |
|-------|--------|
| `stage` | `waiting` · `processing` · `completed` · `verified` |
| `priority` | `urgent` · `high` · `routine` · `low` |
| timestamps | `entered_at`, `started_at`, `completed_at`, `verified_at` |

Migration: `backend/migrations/018_lab_queue.sql`

---

## Service

`backend/app/reception_workspace/lab_queue_engine.py`

- `ensure_lab_queue_item` (also called from `handoff_to_laboratory`)
- `advance_lab_queue` / `set_lab_queue_priority`
- `lab_queue_dashboard` / `lab_queue_statistics` / `lab_queue_refresh` (version token)

---

## APIs (`/api/v1/reception/workspace`)

| Method | Path |
|--------|------|
| GET | `/lab-queue` — dashboard (items, stats, version) |
| GET | `/lab-queue/stats` |
| GET | `/lab-queue/refresh?version=&since=` |
| POST | `/lab-queue/orders/:ref/enqueue` — handoff + optional priority |
| POST | `/lab-queue/orders/:ref/advance` — `{ to }` |
| POST | `/lab-queue/orders/:ref/priority` — `{ priority }` |

Existing: `POST|GET /orders/:ref/lab-handoff` (now returns `lab_queue`)

---

## UI

- Page: `/app/reception/m2/lab-queue`
- Component: `LabQueueWorkbench` — filters, stats strip, priority controls, advance actions, **5s live poll**

---

## Realtime refresh

Client polls `/lab-queue/refresh` with last `version`. Response includes `changed`; when unchanged, item list may be empty and UI keeps the last board.

---

## Tests

`backend/tests/test_lab_queue_engine.py`
