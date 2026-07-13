# API 403 Root Cause Analysis — Release 8.1

**Generated:** 2026-07-13
**Target:** `https://api.dxcon.com.vn`

---

## Summary

| Observation | Finding |
|---|---|
| Earlier smoke test 403 | **Intermittent** — not reproducible at time of Phase 3 diagnosis |
| Current health endpoint | **HTTP 200** via curl and Node fetch |
| Auth `/me` without token | **HTTP 401** (correct) |
| Root application issue | **Misconfigured CORS_ORIGINS** on live Render deployment |

---

## Diagnostic evidence

### Health endpoint (`GET /api/v1/system/health`)

```
HTTP/2 200
server: cloudflare
x-render-origin-server: gunicorn
rndr-id: <render-request-id>
cf-ray: <cloudflare-ray>
```

Response reaches **Gunicorn on Render** through **Cloudflare** — not blocked at edge during diagnosis.

### CORS misconfiguration (Critical)

Live response includes:

```
access-control-allow-origin: https://dxcon-ap.onrender.com
access-control-allow-credentials: true
```

Production `CORS_ORIGINS` on Render is set to the **Render default hostname**, not:

```
https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn
```

**Impact:** Browser requests from `app.dxcon.com.vn` will fail CORS preflight even when the API returns 200.

### OPTIONS preflight

With `Origin: https://app.dxcon.com.vn`, OPTIONS to `/api/v1/system/health` returns 200 but **no `Access-Control-Allow-Origin`** header — confirms `app.dxcon.com.vn` is not in the allowed list.

---

## 403 classification

| Source | Ruled in/out |
|---|---|
| Flask authorization on `/health` | **Out** — health is public, returns 200 |
| Cloudflare WAF / bot protection | **Possible** for automated clients (intermittent 403) |
| Cloudflare Access | **Unknown** — no Access headers observed |
| Render platform block | **Out** during diagnosis |
| Rate limiting | **Possible** under heavy automated test load |
| Missing User-Agent | **Possible** — smoke tests now send `DxCon-SmokeTest/8.1` |
| Wrong endpoint tested | **Out** — `/api/v1/system/health` is correct |

---

## Recommended actions (manual)

1. **Render dashboard** → `dxcon-api` → set:
   ```
   CORS_ORIGINS=https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn
   ```
2. Redeploy backend after env change.
3. Verify:
   ```bash
   curl -si https://api.dxcon.com.vn/api/v1/system/health \
     -H "Origin: https://app.dxcon.com.vn" | grep -i access-control
   ```
   Expected: `access-control-allow-origin: https://app.dxcon.com.vn`
4. Keep Cloudflare on **DNS only** for API unless WAF rules are verified.
5. Do not bypass authentication on protected routes.

---

## Safest interim DNS mode

If Cloudflare proxy causes intermittent 403:

- Set `api.dxcon.com.vn` CNAME to Render target with **grey cloud (DNS only)**
- Verify HTTPS via Render certificate
- Test CORS from browser on `app.dxcon.com.vn` before re-enabling proxy
