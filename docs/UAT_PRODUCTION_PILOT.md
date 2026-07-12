# UAT — Production pilot

Executable checklist for Release 6.0 Production Sprint 1.

## Environment

- Web: Vercel production or preview with production API URL
- API: `https://api.dxcon.com.vn`
- `NEXT_PUBLIC_DEMO_MODE=false`

---

### UAT-01 Public website

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Open `/` | Landing loads, no fake live metrics | |
| 2 | Click Services | `/services` loads | |
| 3 | Click Solutions | `/solutions` loads | |
| 4 | Click Sign In | Login page on app host | |
| 5 | Resize to mobile | Layout remains usable | |

### UAT-02 Admin login

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Login admin | Workspace redirect | |
| 2 | Refresh browser | Session restored | |
| 3 | Open admin dashboard | Metrics or honest warning | |
| 4 | Logout | Returns to login | |

### UAT-03 Doctor authorization

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Login doctor | `/app/doctor` | |
| 2 | Open patients list | Table or empty state | |
| 3 | Visit `/app/admin` | Forbidden/redirect | |

### UAT-04 Clinic owner

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Login clinic owner | `/app/clinic` | |
| 2 | Open orders | List or empty state | |

### UAT-05 Lab user

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Login lab manager | `/app/lab` | |
| 2 | Open samples queue | List or empty state | |

### UAT-06 Collector

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Login collector | `/app/collector` | |
| 2 | Open jobs | Empty state if no collector context | |

### UAT-07 Patient

| Step | Action | Expected | Pass |
|------|--------|----------|------|
| 1 | Login patient | `/app/patient` | |
| 2 | Open results | Released reports or empty | |
| 3 | Attempt other patient URL | Denied | |

---

## Automated gate (required before sign-off)

```bash
cd apps/web
npm run lint && npm run typecheck && npm run test
npm run verify:production-pilot
NEXT_PUBLIC_API_BASE_URL=https://api.dxcon.com.vn \
NEXT_PUBLIC_PUBLIC_SITE_URL=https://dxcon.com.vn \
NEXT_PUBLIC_APP_URL=https://app.dxcon.com.vn \
NEXT_PUBLIC_APP_ENV=production \
NEXT_PUBLIC_DEMO_MODE=false \
npm run build
```
