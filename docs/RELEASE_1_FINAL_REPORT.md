# Release 1 Final Report — DxCon v1.0.0

**Role:** Release Manager  
**Generated (UTC):** 2026-07-25T13:16:23Z  
**Status:** **COMPLETE — RELEASE FROZEN**  
**Release 2:** Not started

---

## 1. Identity

| Field | Value |
|-------|--------|
| Release | **1.0.0** |
| Tag | `v1.0.0` |
| Branch | `release/v1.0.0` |
| Freeze merge commit | `86f3d8516bb6a5315314076b78cc224a737539b8` |
| Freeze tip (tagged) | `26ef537bbfeced6a25d0be1d7f0ba705e1afa462` |
| Pre-merge tip | `c3183a50efb1fa60effa83765e15af87c436df7e` |
| Feature tip merged | `7729a9c15c969372c699dd19e41a576bc4493026` (`feature/reception-m1`) |

---

## 2. Merged commits

Commits brought onto `release/v1.0.0` by the freeze merge (plus merge commit):

| SHA | Subject |
|-----|---------|
| `86f3d85` | Release Freeze: merge feature/reception-m1 into release/v1.0.0 |
| `7729a9c` | Reception M1: patient catalog pricing and order workflow |
| `21b8978` | Add go-live verification report for v1.0.0 cutover. |
| `ad0beb1` | Fix /ready to re-verify migrations in request context. |

---

## 3. Changed modules

| Module | Change |
|--------|--------|
| Reception (web) | M1 workflow UI + tests (`Milestone1Steps`, `OrderSteps`, reception pages) |
| System API | `/ready` migration re-verify in request context |
| Docs | Go-live / freeze / final / sign-off / baseline package |

**Not changed:** Auth runtime, Admin module paths.

---

## 4. Frozen modules

| Module | Policy |
|--------|--------|
| Authentication | **FROZEN** — `docs/AUTH_FREEZE.md`; no runtime edits without hotfix + regression approval |
| Admin | Unchanged by Release 1 freeze merge; treat as stable |
| Release 1 line | Branch + tag `v1.0.0` frozen; further fixes via hotfix policy only |

---

## 5. Release tag

| Item | Value |
|------|--------|
| Tag | `v1.0.0` |
| Points to | `26ef537bbfeced6a25d0be1d7f0ba705e1afa462` |
| Prior tag object (superseded on same name) | Annotated tag previously at `0b345bb` (2026-07-02 GA ancestor) — moved to Release 1 freeze tip by explicit Release Manager freeze |

---

## 6. Deployment IDs (Release 1 Preview evidence)

| Field | Value |
|-------|--------|
| Preview URL | https://dxcon-platform-j4zqiy9dd-dxcon-med.vercel.app |
| Deployment ID | `dpl_C1Y5HhmUHYE6m99pEuTy1H3ed4hm` |
| Build ID | `bld_bm6cr2uun` |
| Commit | `7729a9c15c969372c699dd19e41a576bc4493026` |
| Target | Preview (not auto-promoted by freeze) |

Source: `docs/RECEPTION_M1_DEPLOY_REPORT.md`

---

## 7. Production URLs

| Surface | URL |
|---------|-----|
| Web | https://dxcon.com.vn |
| Web (www) | https://www.dxcon.com.vn |
| API | https://api.dxcon.com.vn |

---

## 8. Production verification result

| Gate | Result |
|------|--------|
| Reception M1 Production Verification (mandatory / RM) | **PASS** — accepted in `docs/RECEPTION_M1_SIGNOFF.md` |
| Order create on production | Proven (`ORD-20260725130537-03F985`) |
| Residual observation | One post-create `GET …/orders/<code>` browser `status 0` — see Known Issues |

---

## 9. Known issues

| ID | Issue | Severity | Disposition |
|----|-------|----------|-------------|
| KI-R1-001 | Intermittent/post-create order detail fetch `status 0` / UI network banner during automated PV | Medium | Hotfix-eligible; does not reopen freeze |
| KI-R1-002 | Live API historically lagged RC SHA / staging labels | Ops | Align deploy to `v1.0.0` on cutover |
| KI-R1-003 | Alembic not adopted; manual SQL migrations | Process | Carry forward |
| KI-R1-004 | CSP `unsafe-inline` / `unsafe-eval` | Low/Med | Post-freeze hardening |
| KI-R1-005 | `app.dxcon.com.vn` DNS historically missing | Low | Ops |

---

## 10. Hotfix policy

See `docs/RELEASE_FREEZE_REPORT.md` § Hotfix policy.

---

## 11. Explicit non-actions

- **Did not** start Release 2  
- **Did not** modify Auth freeze runtime  
- **Did not** change Admin module  
- **Did not** auto-promote Preview to production as part of this freeze step  

---

## 12. Sign-off

| Field | Value |
|-------|--------|
| Release Manager | Release 1 Freeze executed 2026-07-25 |
| Verdict | **FROZEN** |
