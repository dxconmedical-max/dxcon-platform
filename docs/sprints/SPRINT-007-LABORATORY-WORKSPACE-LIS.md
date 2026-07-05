# Sprint 007 — Laboratory Operational Workspace + LIS Integration Foundation

## Goal

Production laboratory workspace at `/app/lab` with sample receive, accession, testing, QC, validation, and LIS CSV/JSON import foundation.

## Verify

```bash
python3 -m compileall backend/app backend/scripts backend/tests
python3 -m unittest discover -s backend/tests -v -k lab_workspace
python3 backend/scripts/verify_laboratory_workspace.py
python3 backend/scripts/verify_lis_integration.py
```

## Reports

- `generated_release/LAB_WORKSPACE_REPORT.json`
- `generated_release/LIS_INTEGRATION_REPORT.json`
- `generated_release/LAB_SECURITY_REPORT.json`
