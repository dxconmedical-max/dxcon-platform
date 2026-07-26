# Reception M1 — Preview / Staging Deploy Report

**Role:** Release Manager  
**Phase:** Release 1 Deployment Phase  
**Date (UTC):** 2026-07-25  
**Branch:** `feature/reception-m1`  
**Environment:** Vercel Preview (Staging)  
**Scope:** Frontend Preview deploy only. No merge. No Milestone 2.

---

## 1. Build

| Check | Result |
|-------|--------|
| Command | `cd apps/web && npm run build` |
| Result | **PASS** |
| Local duration | **10s** |
| Compile | ✓ Compiled successfully in 3.6s |
| Routes include | `/app/reception`, `/app/reception/search`, `/app/reception/register`, `/app/reception/workflow` |

---

## 2. Preview deployment

| Field | Value |
|-------|--------|
| Deployment URL | https://dxcon-platform-j4zqiy9dd-dxcon-med.vercel.app |
| Inspector URL | https://vercel.com/dxcon-med/dxcon-platform/C1Y5HhmUHYE6m99pEuTy1H3ed4hm |
| Deployment ID | `dpl_C1Y5HhmUHYE6m99pEuTy1H3ed4hm` |
| Build ID | `bld_bm6cr2uun` |
| Commit hash | `7729a9c15c969372c699dd19e41a576bc4493026` |
| Git branch (meta) | `feature/reception-m1` |
| Commit message | Reception M1: patient catalog pricing and order workflow |
| Ready state | `READY` |
| Target | Preview |
| Vercel build duration | **23s** (`Build Completed in /vercel/output [23s]`) |
| Deploy wall clock | **122s** (upload + remote build + promote) |
| Project | `dxcon-med/dxcon-platform` (`prj_GSav7JjemjncZug6mVa25QJGDx3Y`) |

Deploy command (repo root; Vercel Root Directory = `apps/web`):

```bash
npx vercel deploy --yes --cwd . \
  --meta gitCommitSha=7729a9c15c969372c699dd19e41a576bc4493026 \
  --meta gitBranch=feature/reception-m1
```

**Not promoted to production.** Production remains `https://dxcon.com.vn`.

---

## 3. Verification

Anonymous browser access is gated by **Vercel Deployment Protection (SSO)**. Checks used authenticated `vercel curl` with protection bypass.

### 3.1 Route availability (M1 surfaces)

| Surface | Path | Result | Notes |
|---------|------|--------|-------|
| Reception home | `/app/reception` | **PASS** | HTTP **307** → `/login?next=%2Fapp%2Freception` |
| Patient search | `/app/reception/search` | **PASS** | HTTP **307** → `/login?next=%2Fapp%2Freception%2Fsearch` |
| Patient create | `/app/reception/register` | **PASS** | HTTP **307** → `/login?next=%2Fapp%2Freception%2Fregister` |
| Catalog / pricing / create order | `/app/reception/workflow` | **PASS** | HTTP **307** → `/login?next=%2Fapp%2Freception%2Fworkflow` (M1 workflow hosts catalog, pricing, order create) |

Interpretation: All M1 routes are **deployed and reachable**. Unauthenticated access correctly redirects through app auth middleware (auth freeze intact).

### 3.2 Login shell + assets + API config

| Check | Result |
|-------|--------|
| `GET /login` | **PASS** — HTTP **200**, HTML ~8553 bytes |
| CSS `/_next/static/chunks/2j1mwzb9uv2tw.css` | **PASS** — HTTP **200**, 39768 bytes |
| JS `/_next/static/chunks/0iu3z6vzu_fxz.js` | **PASS** — HTTP **200**, 44414 bytes |
| CSP `connect-src` | includes `https://api.dxcon.com.vn` |
| Localhost in login HTML | **None** |

### 3.3 Authenticated workflow actions

| Action | Status |
|--------|--------|
| Patient search (authenticated API) | **Not executed in this deploy gate** — requires live Reception session on Preview (SSO + DxCon login) |
| Patient create | **Not executed in this deploy gate** — same |
| Catalog selection | **Not executed in this deploy gate** — same |
| Pricing confirmation | **Not executed in this deploy gate** — same |
| Create order | **Not executed in this deploy gate** — same |

Route-level deploy verification for those surfaces is **PASS** via `/app/reception/search`, `/register`, and `/workflow` above. Full authenticated E2E remains a separate Production / Preview login verification step.

---

## 4. Collected identifiers

| Item | Value |
|------|--------|
| Deployment URL | https://dxcon-platform-j4zqiy9dd-dxcon-med.vercel.app |
| Build ID | `bld_bm6cr2uun` |
| Deployment ID | `dpl_C1Y5HhmUHYE6m99pEuTy1H3ed4hm` |
| Commit hash | `7729a9c15c969372c699dd19e41a576bc4493026` |
| Local build duration | 10s |
| Remote build duration | 23s |
| Deploy wall clock | 122s |

---

## 5. Access notes

1. Preview URL requires Vercel SSO for interactive browser access.
2. After SSO, sign in to DxCon with a Reception / Super Admin account to exercise search → create → catalog → pricing → order.
3. Prior Preview (superseded for this phase): `dpl_B7ZjehRDMMwxLP6eDrti3MVTrinZ` / `https://dxcon-platform-jkgzd1et2-dxcon-med.vercel.app`

---

## 6. Out of scope (stopped)

- No production promote
- No backend / Render redeploy
- No database migrations
- No merge into `release/v1.0.0`
- No Milestone 2 work
- No business-logic code changes in this deploy step

---

## 7. Summary

| Item | Status |
|------|--------|
| Frontend production build | PASS |
| Preview deploy | PASS |
| `/app/reception` | PASS (307 → login) |
| Patient search route | PASS (307 → login) |
| Patient create route | PASS (307 → login) |
| Catalog / pricing / order workflow route | PASS (307 → login) |
| JS / CSS / API base | PASS |
| Authenticated E2E actions | Deferred (session required) |
| Production promote | NOT DONE |

**Release Manager stop point:** Preview/Staging deployment complete. Waiting for further approval before merge or production promote.
