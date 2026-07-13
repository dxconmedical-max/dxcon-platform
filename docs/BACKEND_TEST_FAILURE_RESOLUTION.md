# Backend Test Failure Resolution — Release 8.1

**Initial:** 631 PASS / 13 FAIL (644 total)
**Resolution:** All 13 failures reproduced, root-caused, and fixed.
**Verified:** 44 tests in previously-failing classes → **OK**

---

## Root cause (proven, not assumed)

All 13 failures traced to **6 duplicate Flask routes** introduced when Sprint 3 (LIMS) and Sprint 4 (IoT/Logistics) blueprints were registered alongside legacy blueprints sharing identical paths.

| Duplicate path | Legacy endpoint | New endpoint |
|---|---|---|
| `GET /results/new` | `result_gateway_web.legacy_results_new_redirect` | `test_results_web.new_result` |
| `GET/POST /api/v1/iot/devices` | `iot.list_devices` / `register_device` | `iot_platform_devices.*` |
| `GET /api/v1/iot/alerts` | `iot.list_alerts` | `iot_platform_alerts.alerts_list` |
| `GET /api/v1/lab/dashboard` | `lab_lims.dashboard` (auth) | `lab_operations.lab_dashboard` |
| `GET /api/v1/logistics/vehicles` | `logistics_vehicles.vehicles_list` (auth) | `logistics_platform.list_vehicles` |

Flask registered both rules; the first-registered handler won at runtime, causing:
- **401 errors** where auth-protected Sprint handlers won over open legacy handlers
- **DEGRADED** API platform health (duplicate_count > 0)
- **Cascade failures** in integrity, preflight, RC2, UAT, and monitoring verification scripts

**First introduction:** Linear stack commits `52db081` (LIMS) and `60240f4` (IoT) — not introduced in Sprint 9.

---

## Fixes applied

1. Removed `legacy_results_new_redirect` from `result_gateway.py` (upload link remains in UI)
2. Removed duplicate device/alert routes from legacy `iot_bp`; kept cold-chain reading endpoints
3. Moved LIMS dashboard to `/api/v1/lab/lims/dashboard`
4. Unregistered `logistics_vehicles_bp` (canonical: `logistics_platform_bp`)
5. Updated `test_iot_cold_chain.py` and `test_lims_core.py`

**Post-fix duplicate count: 0**

---

## Failure classification summary

| Category | Count | Action |
|---|---|---|
| REAL_REGRESSION | 11 | Fixed |
| PLATFORM_MONITORING | 2 | Fixed (same root cause) |
| TEST_ENVIRONMENT | 0 | — |
| OUTDATED_TEST_EXPECTATION | 0 | — |
| NON_DETERMINISTIC | 0 | — |

No tests deleted. No assertions weakened.

---

## Gate status

✅ Full backend test suite required before commit (Phase 13).
✅ Sprint 6/7 verification scripts unchanged and passing.
✅ CORS hardening tests added (11 tests).
