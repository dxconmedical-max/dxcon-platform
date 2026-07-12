# Production CORS setup

Browser requests from the DxCon web application require explicit CORS allowlisting on the API.

## Required production origins

```
https://dxcon.com.vn
https://www.dxcon.com.vn
https://app.dxcon.com.vn
```

## Backend configuration

Set `CORS_ORIGINS` in the API environment (comma-separated, no wildcard in production):

```
CORS_ORIGINS=https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn
```

Reference: `backend/.env.production.example`

## Vercel preview origins

During rollout, add explicit preview origins when needed:

```
CORS_ORIGINS=https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn,https://<project>-<branch>.vercel.app
```

Do **not** use `*` with credentials. Do not weaken tenant isolation or authorization.

## Verification

1. Deploy web to Vercel with production env vars
2. Open browser devtools → Network on `/login`
3. Confirm `POST https://api.dxcon.com.vn/api/v1/auth/login` succeeds without CORS errors

## Security notes

- CORS is enforced in `backend/app/core/security.py` via Flask-CORS
- Production readiness checks reject wildcard origins (`backend/app/infrastructure/production_readiness.py`)
