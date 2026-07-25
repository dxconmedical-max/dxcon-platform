# Release Freeze Report — DxCon v1.0.0

**Role:** Release Manager  
**Freeze (UTC):** 2026-07-25T13:16:23Z  
**Action:** Release Freeze executed  
**Release 2:** **NOT STARTED — STOP**

---

## 1. Pre-freeze verification

| Check | Result | Evidence |
|-------|--------|----------|
| Auth module frozen and unchanged | **PASS** | `verify:auth-freeze` PASS; `test:auth-freeze` 64 passed / 1 skipped; no auth-path diffs in merge |
| Admin module unchanged | **PASS** | No admin path diffs `origin/release/v1.0.0...feature/reception-m1` |
| Reception M1 production verification | **PASS** | Release Manager acceptance — `docs/RECEPTION_M1_SIGNOFF.md` §3.4 |
| CI green | **PASS** (local mandatory gates) | Auth-freeze + M1 Vitest + backend `test_reception_workspace` + `test_rc_security_gate` (17 OK). Remote GitHub Actions CLI unavailable in freeze environment (`gh` missing). |
| Build green | **PASS** | `apps/web` `npm run build` PASS (reception routes present) |
| No uncommitted source changes (post-freeze commit) | **PASS** (target) | Freeze docs committed; generated artifacts excluded |

---

## 2. Merge

| Field | Value |
|-------|--------|
| Source | `feature/reception-m1` (`7729a9c`) |
| Target | `release/v1.0.0` (was `c3183a5`) |
| Strategy | `--no-ff` |
| Merge commit | `86f3d8516bb6a5315314076b78cc224a737539b8` |

### Merged commits

1. `ad0beb1` — Fix `/ready` to re-verify migrations in request context  
2. `21b8978` — Add go-live verification report for v1.0.0 cutover  
3. `7729a9c` — Reception M1: patient catalog pricing and order workflow  
4. `86f3d85` — Release Freeze merge commit  

---

## 3. Changed modules

| Path / area | Type |
|-------------|------|
| `apps/web/src/app/app/reception/**` | Reception M1 UI + tests |
| `backend/app/api/system/routes.py` | `/ready` fix |
| `docs/**` (freeze package) | Release documentation |

---

## 4. Frozen modules

| Module | Freeze rule |
|--------|-------------|
| **Auth** | No changes to `authStore`, `AuthProvider`, `AuthErrorBoundary`, `useAuth`/`useRequireAuth`, `AppShell` auth bootstrap, `middleware` auth, session/cookies, `services/auth`, login wiring without dedicated hotfix + `test:auth-freeze` + `verify:auth-freeze` |
| **Admin** | No drive-by edits on Release 1 line |
| **Release 1.0.0** | Code + tag frozen; only hotfixes allowed |

---

## 5. Release tag

| Field | Value |
|-------|--------|
| Name | `v1.0.0` |
| Annotated message | DxCon Release 1.0.0 Freeze |
| Previous `v1.0.0` target | `0b345bbdaa822238f6aaf476efb410f6b7a01be6` (ancestor GA) |
| New target | Freeze tip on `release/v1.0.0` 8f24a041cb74c800d36cd0d8fe10cb200c7ccc75 |
| Retag rationale | Explicit Release Manager Freeze instruction to create `v1.0.0` for this release line |

---

## 6. Deployment IDs

| Environment | ID / URL |
|-------------|----------|
| Preview deployment | `dpl_C1Y5HhmUHYE6m99pEuTy1H3ed4hm` |
| Preview build | `bld_bm6cr2uun` |
| Preview URL | https://dxcon-platform-j4zqiy9dd-dxcon-med.vercel.app |
| Preview commit | `7729a9c` |

Production promote of freeze tip is an ops follow-up, not performed by this freeze script beyond merge/tag.

---

## 7. Production URLs

- https://dxcon.com.vn  
- https://www.dxcon.com.vn  
- https://api.dxcon.com.vn  

---

## 8. Production verification result

**PASS** (mandatory Release Manager acceptance).

Supporting artifacts:

- `docs/RECEPTION_M1_SIGNOFF.md` — COMPLETE  
- `docs/RECEPTION_M1_PRODUCTION_VERIFICATION.md` — raw runbook (order create proven; residual GET observation logged)  
- Synthetic prod order: `ORD-20260725130537-03F985` / patient `P-20260725125042-ED8778`

---

## 9. Known issues

| ID | Summary | Hotfix? |
|----|---------|---------|
| KI-R1-001 | Post-create order GET `status 0` / network banner (intermittent PV) | Yes, if reproducible |
| KI-R1-002 | Production API revision alignment to `v1.0.0` | Ops deploy |
| KI-R1-003 | Manual migrations (no Alembic) | No (process) |
| KI-R1-004 | CSP unsafe-inline/eval | Planned hardening |
| KI-R1-005 | `app.dxcon.com.vn` DNS | Ops |

---

## 10. Hotfix policy

1. **Branch:** Create `hotfix/v1.0.0-<slug>` from `v1.0.0` / `release/v1.0.0`.  
2. **Scope:** Minimal fix only — no Release 2 features.  
3. **Auth:** If auth files must change, require Auth Freeze exception + full `test:auth-freeze` + `verify:auth-freeze`.  
4. **Admin:** Avoid unless the incident is Admin-scoped.  
5. **Verify:** Reproduce fix locally; run affected unit/integration gates; build green.  
6. **Merge:** PR into `release/v1.0.0` only; no force-push of branch history.  
7. **Tag:** Annotate as `v1.0.0-hotfix.N` (do **not** silently rewrite history). Moving `v1.0.0` requires explicit Release Manager approval.  
8. **Docs:** Append hotfix entry to `CHANGELOG.md` and note in this freeze report addendum.  
9. **Deploy:** Promote hotfix build to production with recorded deployment IDs.  
10. **Stop:** Do not open Release 2 work on the hotfix branch.

---

## 11. Stop conditions honored

- Release Freeze complete  
- Release 2 **not** started  
- Auth / Admin freeze boundaries preserved  

**STOP.**
