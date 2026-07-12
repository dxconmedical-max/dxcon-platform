# Production smoke test

Run after Vercel deploy and API CORS update.

## 1. Public site

- [ ] `https://dxcon.com.vn` loads landing page
- [ ] Navigation: Services, Solutions, Partners, Pricing, Contact
- [ ] Sign In links to `https://app.dxcon.com.vn/login` (or relative on preview)
- [ ] No fabricated production metrics on hero section
- [ ] Book demo and contact forms work (mailto)

## 2. API health

```bash
curl -s https://api.dxcon.com.vn/health | head
```

Expected: JSON with `status` field

## 3. Authentication

- [ ] Login with pilot admin credentials
- [ ] Redirect to role workspace (`/app/admin` or capabilities workspace)
- [ ] Refresh page — session restores
- [ ] Logout clears session and returns to `/login`

## 4. Organization context

- [ ] Multi-org user sees organization switcher
- [ ] Switch organization reloads workspace permissions

## 5. Workspaces

- [ ] Admin dashboard loads metrics or honest placeholder warning
- [ ] Doctor/patient/lab pilot list pages load without crash
- [ ] Unauthorized route → `/forbidden`

## 6. Security

- [ ] `NEXT_PUBLIC_DEMO_MODE=false` in Vercel production
- [ ] Protected `/app` responses include `Cache-Control: private, no-store`
- [ ] No tokens in URL query strings

## 7. Verification script

```bash
cd apps/web && npm run verify:production-pilot
```

Expected: `PASS`
