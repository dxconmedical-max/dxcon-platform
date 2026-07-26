# Milestone 5 — Lab Queue

**Track:** Reception M2 / Laboratory (shared)  
**Status:** Implemented (Release 2 Step 7)

Reception → Laboratory queue handoff; order appears on lab intake queue.

**Depends on:** M1–M4 handoff packet (paid + barcode).

## Delivered

- `BizLabQueueItem` + `lab_queue_engine.py`
- Stages: waiting → processing → completed → verified
- Priority, statistics, live refresh
- Page: `/app/reception/m2/lab-queue`
- Tests: `backend/tests/test_lab_queue_engine.py`
- Doc: `docs/LAB_QUEUE_MODULE.md`

**Out of scope:** Full lab accession/validation (M7).
