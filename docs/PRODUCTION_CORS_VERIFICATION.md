# Production CORS Verification

**Release:** 8.1 · **Sprint:** 9

---

## Required production allowlist

```
CORS_ORIGINS=https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn
```

Set this in the **Render dashboard** for the `dxcon-api` service (not in `render.yaml` today).

---

## Backend implementation

| Item | Location |
| --- | --- |
| CORS init | `backend/app/core/security.py` `init_security()` |
| Config source | `CORS_ORIGINS` env var (`backend/app/core/config.py` line 62) |
| Scope | `/api/*` routes only |
| Credentials | `supports_credentials=True` when explicit origins are set |
| Wildcard block | In strict envs (`production/staging/uat`), `*` is forced to empty → startup fails |

---

## Production readiness guard

`backend/app/infrastructure/production_readiness.py` `validate_cors()`:

- Raises `RuntimeError("CORS_ORIGINS must be explicit in staging/production")` if origins is `*` or empty in a strict env.
- Called by `validate_production_config()` on startup when `APP_ENV` is strict.

---

## Required headers

| Header | Allowed |
| --- | --- |
| `Authorization` | ✅ (via flask-cors default) |
| `Content-Type` | ✅ |
| `X-Organization-ID` | ✅ (custom header, allowed by flask-cors) |
| `X-Correlation-ID` | ✅ |
| `Idempotency-Key` | ✅ |

---

## Verification steps

### 1. Preflight (from browser console on `https://app.dxcon.com.vn`)

```javascript
fetch('https://api.dxcon.com.vn/api/v1/system/health', {
  method: 'OPTIONS',
  headers: {
    'Origin': 'https://app.dxcon.com.vn',
    'Access-Control-Request-Method': 'GET',
    'Access-Control-Request-Headers': 'Authorization,Content-Type'
  }
}).then(r => {
  console.log('status', r.status);
  console.log('ACAO', r.headers.get('Access-Control-Allow-Origin'));
  console.log('ACAC', r.headers.get('Access-Control-Allow-Credentials'));
});
```

**Expected:** status 200, `Access-Control-Allow-Origin: https://app.dxcon.com.vn`, `Access-Control-Allow-Credentials: true`.

### 2. Health endpoint

```bash
curl -s https://api.dxcon.com.vn/api/v1/system/health | jq .
```

**Expected:** `200` with health payload. No CORS headers needed for direct curl.

### 3. Authenticated rejection

```bash
curl -s -o /dev/null -w "%{http_code}" \
  https://api.dxcon.com.vn/api/v1/auth/me
```

**Expected:** `401` (not `500`).

### 4. Automated smoke test

```bash
python backend/scripts/production_api_smoke_test.py
```

---

## Preview origin policy

Vercel preview deployments (`*.vercel.app`) are **not** in the production allowlist by default. For staging/UAT testing against the production API, either:

1. Deploy a staging backend with its own `CORS_ORIGINS` including the preview hostname, or
2. Add the specific preview origin to a **staging** backend's `CORS_ORIGINS` (never add `*` to production).

---

## Failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| CORS error in browser | `CORS_ORIGINS` not set on Render | Add the three origins in Render env |
| Service won't start | Wildcard `*` in production | Set explicit origins |
| Login works but API calls fail | Wrong origin (e.g. `app.` missing) | Add all three origins |
| OPTIONS returns 404 | Route not under `/api/*` | CORS only applies to `/api/*`; health is at `/api/v1/system/health` ✅ |

---

## Render environment variable

Add to Render → `dxcon-api` → Environment:

```
CORS_ORIGINS=https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn
```

Also required (from `backend/.env.production.example`):

```
REDIS_URL=<your-redis-url>
SMTP_HOST=<your-smtp-host>
SMTP_PORT=587
SMTP_USER=<user>
SMTP_PASSWORD=<secret>
SMTP_FROM=noreply@dxcon.com
SMTP_USE_TLS=true
```
