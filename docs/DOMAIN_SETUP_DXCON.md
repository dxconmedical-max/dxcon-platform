# DxCon Domain Setup — dxcon.com.vn

Production domain architecture for DxCon Release 1.0 (Sprint 011).

## Domain map

| Host | Purpose | Target |
|------|---------|--------|
| `dxcon.com.vn` | Public marketing / landing | Web app `/home` |
| `www.dxcon.com.vn` | Public marketing (alias) | Web app `/home` |
| `app.dxcon.com.vn` | Production web application | Web app `/login` |
| `admin.dxcon.com.vn` | Admin workspace (alias) | Same as `app` |
| `doctor.dxcon.com.vn` | Doctor portal entry | Same as `app` |
| `patient.dxcon.com.vn` | Patient portal entry | Same as `app` |
| `lab.dxcon.com.vn` | Laboratory workspace entry | Same as `app` |
| `clinic.dxcon.com.vn` | Clinic partner entry | Same as `app` |
| `collector.dxcon.com.vn` | Collector workspace entry | Same as `app` |
| `api.dxcon.com.vn` | Production API (verified on Render) | `dxcon-ap.onrender.com` |

Legacy API host `https://dxcon-ap.onrender.com` remains supported for backward compatibility.

## Environment variables

```bash
PUBLIC_SITE_URL=https://dxcon.com.vn
WEB_APP_URL=https://app.dxcon.com.vn
API_BASE_URL=https://api.dxcon.com.vn
DEMO_MODE=false
CORS_ORIGINS=https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn,https://admin.dxcon.com.vn,https://doctor.dxcon.com.vn,https://patient.dxcon.com.vn,https://lab.dxcon.com.vn,https://clinic.dxcon.com.vn,https://collector.dxcon.com.vn
```

## Cloudflare DNS records

| Type | Name | Target | Notes |
|------|------|--------|-------|
| CNAME | `api` | `dxcon-ap.onrender.com` | **Verified** on Render |
| CNAME | `app` | Production web Render service | Flask/Gunicorn web target |
| CNAME | `www` | Production landing target | Can point to same web service |
| CNAME | `admin` | Same as `app` | Workspace alias |
| CNAME | `doctor` | Same as `app` | Workspace alias |
| CNAME | `patient` | Same as `app` | Workspace alias |
| CNAME | `lab` | Same as `app` | Workspace alias |
| CNAME | `clinic` | Same as `app` | Workspace alias |
| CNAME | `collector` | Same as `app` | Workspace alias |
| A/ALIAS | `@` (`dxcon.com.vn`) | Cloudflare proxy or web target | Apex record per registrar |

## Cloudflare SSL / HTTPS

- SSL mode: **Full (strict)**
- **Always Use HTTPS**: ON
- **Automatic HTTPS Rewrites**: ON
- Minimum TLS: 1.2

## Render configuration

### API service (existing)

- Custom domain: `api.dxcon.com.vn` — **already verified**
- Health check: `GET /health` → `status: OK`
- Legacy URL: `https://dxcon-ap.onrender.com`

### Web service (Flask)

- Build: `pip install -r backend/requirements.txt`
- Start: `gunicorn -w ${WEB_CONCURRENCY:-4} -b 0.0.0.0:${PORT:-8000} "app:create_app()"`
- Custom domains: `app.dxcon.com.vn`, workspace aliases, optionally `www.dxcon.com.vn`
- Set production env vars above

## User journey

```
dxcon.com.vn  →  /home  (public landing)
app.dxcon.com.vn  →  /login  →  role workspace
```

Post-login routing (Sprint 011):

| Role | Workspace |
|------|-----------|
| SUPER_ADMIN, DXCON_ADMIN, ADMIN | `/app/admin` |
| EXECUTIVE | `/app/executive` |
| RECEPTION | `/app/reception` |
| DOCTOR, PARTNER_DOCTOR | `/app/doctor` |
| LAB_MANAGER, LAB_TECHNICIAN, LAB | `/app/lab` |
| COLLECTOR | `/app/collector` |
| CLINIC_OWNER | `/app/clinic` |
| PATIENT | `/app/patient` |
| Unknown | `/app` |

## Verification

```bash
python backend/scripts/verify_production_web_gateway.py
curl -s https://api.dxcon.com.vn/health
```

Reports:

- `backend/generated_release/PRODUCTION_WEB_GATEWAY_REPORT.json`
- `backend/generated_release/DOMAIN_CONFIGURATION_REPORT.json`

## Future split (Module 10)

The current production gateway is Flask-rendered (`backend/app/web/`). A dedicated SPA under `apps/web` can be introduced later without changing API contracts. The shared browser client lives at `backend/app/static/js/dxcon-api-client.js`.
