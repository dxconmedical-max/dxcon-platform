# Release 2.0 Architecture Baseline

**Frozen:** 2026-07-10  
**Certificate:** `backend/generated_release/RELEASE_2_BASELINE_CERTIFICATE.json`

## What is frozen

1. API v1 stable contract
2. Database ownership and migration policy
3. Identity and authentication flows
4. Authorization and permission naming
5. Canonical healthcare data schemas v1.0
6. Domain event catalog and envelope
7. Clinical state machines
8. Integration adapter contracts (Epic 3.5)
9. Frontend capability payload
10. Mobile API requirements

## Production endpoints

- API: https://api.dxcon.com.vn
- Web: https://dxcon.com.vn
- App: https://app.dxcon.com.vn

## Extension rule

All Release 2.x Epics **extend** this baseline. See `RELEASE_2_EXTENSION_RULES.md`.

## Verification suite

```bash
python backend/scripts/verify_architecture_freeze.py
python backend/scripts/verify_api_contract.py
python backend/scripts/verify_permission_registry.py
python backend/scripts/verify_tenant_model_coverage.py
python backend/scripts/verify_domain_event_contract.py
python backend/scripts/verify_clinical_state_machines.py
```

## Guardrails

CI must run architecture guardrails (`ARCHITECTURE_GUARDRAILS_REPORT.json`).
