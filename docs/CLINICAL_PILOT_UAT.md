# Clinical Pilot UAT

Release 8.0 Sprint 6 internal pilot checklist.

## Automated flow

```bash
cd backend
CLINICAL_PILOT_SIMULATOR_ENABLED=true python3 scripts/run_clinical_pilot_flow.py
python3 scripts/verify_clinical_governance.py
```

## Manual UAT

| # | Step | Expected |
|---|------|----------|
| 1 | Create/confirm order | Order in testing state |
| 2 | Collect/accession specimen | LIMS timeline updated |
| 3 | Ingest simulated analyzer result | Preliminary, not released |
| 4 | Technician validate | `TECHNICIAN_VALIDATED` |
| 5 | Doctor approve | Report `approved` + signature |
| 6 | Governed release | Report `released`, token issued |
| 7 | Patient views results | Released only |
| 8 | Verify public token | No PHI; authenticity only |

## Pass criteria

All Sprint 6 gate checks PASS; no critical security blockers.
