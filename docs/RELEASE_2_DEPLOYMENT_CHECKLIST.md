# Release 2 Deployment Checklist — Reception M2 RC (`2.0.0-rc1`)

**Target branch:** `release/v2.0.0`  
**Auth freeze:** do not deploy auth runtime changes  
**Companion:** `docs/RELEASE_2_GO_LIVE_CHECKLIST.md`, `docs/RELEASE_2_RC_REPORT.md`

---

## 0. Preconditions

- [ ] CI / local RC gates green (see RC report)
- [ ] Exclusive R2 files staged via named `git add` (release isolation)
- [ ] No secrets (`.env`, credentials) in commit
- [ ] Migrations reviewed: `017_reception_receipts.sql`, `018_lab_queue.sql`, `019_sample_queue.sql`

---

## 1. Database (Postgres production)

Order (additive, idempotent `IF NOT EXISTS`):

1. [ ] `backend/migrations/017_reception_receipts.sql` → `biz_receipts`
2. [ ] `backend/migrations/018_lab_queue.sql` → `biz_lab_queue_items`
3. [ ] `backend/migrations/019_sample_queue.sql` → `biz_sample_queue_items`, `biz_sample_queue_events`

Verify:

```sql
SELECT to_regclass('public.biz_receipts');
SELECT to_regclass('public.biz_lab_queue_items');
SELECT to_regclass('public.biz_sample_queue_items');
SELECT to_regclass('public.biz_sample_queue_events');
```

---

## 2. Backend (API — Render / `api.dxcon.com.vn`)

### Env (confirm)

| Key | Expected |
|-----|----------|
| `APP_ENV` | `production` |
| `DEMO_MODE` | `false` |
| `API_AUTH_GATE_ENABLED` | `true` |
| `BUILD_VERSION` | `2.0.0-rc1` (or build SHA) |
| `SECRET_KEY` / `JWT_SECRET_KEY` | rotated; not defaults |
| `DATABASE_URL` | production Postgres |
| `CORS_ORIGINS` | apex + app origins |
| `DXCON_QR_SECRET` | optional; recommended |
| `VNPAY_TMN_CODE` / `VNPAY_HASH_SECRET` | optional sandbox/merchant |

### Deploy

- [ ] Deploy API build from approved `release/v2.0.0` tip
- [ ] `GET /api/v1/system/health` → 200
- [ ] `GET /api/v1/system/ready` → 200
- [ ] Spot-check: `GET /api/v1/reception/workspace/qr/kinds` (auth) → 200
- [ ] Spot-check: `GET /api/v1/reception/workspace/lab-queue` (auth) → 200
- [ ] Spot-check: `GET /api/v1/reception/workspace/sample-queue` (auth) → 200

---

## 3. Frontend (Vercel — `dxcon.com.vn`)

### Env (confirm)

| Key | Expected |
|-----|----------|
| `NEXT_PUBLIC_APP_ENV` | `production` |
| `NEXT_PUBLIC_API_BASE_URL` | `https://api.dxcon.com.vn` |
| `NEXT_PUBLIC_DEMO_MODE` | `false` |
| `NEXT_PUBLIC_APP_URL` / site URL | `https://dxcon.com.vn` |

### Deploy

- [ ] Production build from same release tip as API
- [ ] Confirm routes resolve:
  - `/app/reception/m2`
  - `/app/reception/m2/receipt`
  - `/app/reception/m2/barcode`
  - `/app/reception/m2/qr`
  - `/app/reception/m2/lab-queue`
  - `/app/reception/m2/sample-queue`
- [ ] Login still works (auth freeze)

---

## 4. Post-deploy verification

- [ ] Run go-live smoke (`RELEASE_2_GO_LIVE_CHECKLIST.md`)
- [ ] Confirm no auth-freeze path diffs vs freeze policy
- [ ] Capture deploy IDs (Vercel + Render) in release ticket
- [ ] Watch logs/metrics 30–60 minutes

---

## 5. Rollback

| Layer | Action |
|-------|--------|
| Web | Redeploy previous Vercel production deployment |
| API | Redeploy previous Render release |
| DB | Additive tables may remain; do not drop if receipts/queue rows exist unless RM approves |

---

## 6. Do not

- Force-push `main` / `release/v1.0.0` / move `v1.0.0` tag
- Modify auth freeze runtime files
- Mix unfinished exclusive releases in one commit
- Enable live VNPay without merchant secrets + RM sign-off
