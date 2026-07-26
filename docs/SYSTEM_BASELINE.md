# DxCon System Baseline — v1.0.0

**Captured (UTC):** 2026-07-25  
**Purpose:** Immutable reference for **frozen** Release 1.0.0.  
**Auth freeze:** Active  
**Release 2:** Not started

---

## 1. Version identity

| Field | Value |
|-------|--------|
| Release | **DxCon v1.0.0** |
| Git tag | `v1.0.0` |
| Branch | `release/v1.0.0` |
| Freeze merge | `86f3d8516bb6a5315314076b78cc224a737539b8` |
| Feature tip merged | `7729a9c15c969372c699dd19e41a576bc4493026` |
| Pre-merge base | `c3183a50efb1fa60effa83765e15af87c436df7e` |

---

## 2. Runtime topology

| Tier | Baseline |
|------|----------|
| Web | Next.js (`apps/web`) — https://dxcon.com.vn |
| API | Backend — https://api.dxcon.com.vn |
| Auth | JWT + session; freeze policy |
| Data | PostgreSQL (production target) |
| Mobile | Flutter Phase 1 |

---

## 3. Completed modules

Auth, Admin, Reception M1 (+ extended contracts on line), Collection, Laboratory, Clinical PDF, Role dashboards, RC1 security, Flutter Phase 1, health probes.

---

## 4. Frozen modules

Auth freeze paths; Admin unchanged by M1; Release 1.0.0 tag/branch.

---

## 5. API contract baseline (Reception M1)

Prefix `/api/v1/reception/workspace`: search, patients/register, patients/<code>, tests, orders, orders/<ref>.

---

## 6. Quality baseline (freeze)

Auth freeze PASS · Admin unchanged PASS · Reception M1 PV PASS (RM) · Vitest/build/backend gates PASS.

---

## 7. Remaining backlog

Hotfix residuals + ops align + future releases (not started).

---

## 8. Known limitations

See `docs/RELEASE_FREEZE_REPORT.md`.

---

## 9. Future milestones

Kick off only via explicit Release 2 start — **not** part of this baseline freeze.

---

## 10. Related documents

`docs/RELEASE_1_FINAL_REPORT.md`, `docs/RELEASE_FREEZE_REPORT.md`, `docs/AUTH_FREEZE.md`, `docs/VERSION.md`
