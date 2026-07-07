# LIS Integration Status (Pilot)

## Supported for pilot

- **Manual result entry** (Laboratory Workspace)
- **CSV import foundation** (LIS import engine)

## Planned / Not production ready

- **HL7 adapter**: PLANNED (placeholder)
- **REST connector**: PLANNED (stub)

## Impact on pilot readiness

- HL7/REST should **not block internal pilot**.
- HL7/REST must not be marketed as production-ready until implemented and verified.

## Generated status report

Run:

```bash
python backend/scripts/verify_pilot_blockers.py
```

Outputs:
- `backend/generated_release/LIS_INTEGRATION_STATUS.json`

