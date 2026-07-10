# API v1 Freeze — Release 2.0

**Frozen:** 2026-07-10  
**Production API:** https://api.dxcon.com.vn  
**Baseline certificate:** `backend/generated_release/RELEASE_2_BASELINE_CERTIFICATE.json`

## Scope

All routes under `/api/v1/` are part of the Release 2.0 contract unless classified otherwise.

## Classification

| Class | Rule | Change policy |
|-------|------|---------------|
| **STABLE** | Production `/api/v1/*` excluding experimental/internal markers | No breaking changes; optional fields allowed |
| **EXPERIMENTAL** | Paths containing `sandbox`, `foundation`, `beta`, `plugin`, `experimental` | May change without v2 |
| **DEPRECATED** | Marked deprecated or `/api/v2/` aliases | Must include replacement + sunset metadata |
| **INTERNAL** | Web UI routes, metrics, debug | Not a public contract |

## Stable endpoint inventory

Generated automatically by `backend/scripts/verify_api_contract.py` → `API_V1_FREEZE_REPORT.json`.

At freeze time:
- Total API v1 routes: see report `api_v1_routes`
- Stable routes: see report `stable_count`
- Duplicate routes must remain **zero**

## Breaking change policy

1. Existing STABLE request/response fields cannot be removed in Release 2.x.
2. New optional fields are allowed on STABLE endpoints.
3. Semantic changes to existing fields require `/api/v2`.
4. Error payloads must follow `ERROR_CONTRACT.md`.

## Key stable domains

- `/api/v1/auth/*` — authentication and tenant context
- `/api/v1/patients/*`, `/api/v1/orders/*` — clinical operations
- `/api/v1/marketplace/*` — patient marketplace
- `/api/v1/payments/*`, `/api/v1/billing/*` — financial
- `/api/v1/integration/*` — connector framework (Epic 3.5)
- `/api/v1/mdm/*` — master data
- `/api/v1/lab/*`, `/api/v1/results/*` — laboratory workflow

## Verification

```bash
python backend/scripts/verify_api_contract.py
python backend/scripts/verify_architecture_freeze.py
```
