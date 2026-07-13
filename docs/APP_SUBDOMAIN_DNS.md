# App Subdomain DNS Setup — app.dxcon.com.vn

**Release:** 8.1 · **Sprint:** 9

---

## Overview

| Domain | Role |
| --- | --- |
| `dxcon.com.vn` | Public website (already configured) |
| `www.dxcon.com.vn` | Redirects to apex (middleware) |
| `app.dxcon.com.vn` | **New** — authentication + protected workspaces |
| `api.dxcon.com.vn` | Backend API (Render) |

---

## Step-by-step (Vercel + Cloudflare)

### Step 1 — Add domain in Vercel

1. Open **Vercel → dxcon-web project → Settings → Domains**.
2. Click **Add** and enter: `app.dxcon.com.vn`
3. Vercel will display the required DNS record. **Copy the exact value shown** — do not guess.

Typical Vercel DNS target formats:
- `cname.vercel-dns.com` (CNAME), or
- `76.76.21.21` (A record)

> **Use the value Vercel displays for your project.** The target above is illustrative only.

### Step 2 — Create DNS record in Cloudflare

1. Open **Cloudflare → dxcon.com.vn → DNS → Records**.
2. Add a new record:

| Type | Name | Target | Proxy |
| --- | --- | --- | --- |
| CNAME (or A) | `app` | *(exact value from Vercel Step 1)* | **DNS only** (grey cloud) |

3. **Keep Cloudflare proxy disabled** (grey cloud) until HTTPS is verified. Orange-cloud proxy can interfere with Vercel certificate issuance.

### Step 3 — Wait for certificate

1. Return to Vercel → Domains.
2. Wait until `app.dxcon.com.vn` shows **Valid Configuration** with a green checkmark.
3. Vercel issues the TLS certificate automatically (usually 1–15 minutes).

### Step 4 — Verify HTTPS

```bash
curl -sI https://app.dxcon.com.vn/login | head -5
```

**Expected:** `HTTP/2 200` (or `307` redirect to login).

### Step 5 — Verify application routing

```bash
# Unauthenticated /app should redirect to login
curl -sI https://app.dxcon.com.vn/app | grep -i location

# Public host should redirect app paths to app host
curl -sI https://dxcon.com.vn/login | grep -i location
```

**Expected:**
- `app.dxcon.com.vn/app` → `location: .../login?next=/app`
- `dxcon.com.vn/login` → `location: https://app.dxcon.com.vn/login`

### Step 6 — Set Vercel environment variables

Confirm in Vercel Production env:

```
NEXT_PUBLIC_APP_URL=https://app.dxcon.com.vn
```

### Step 7 — Smoke test

```bash
node apps/web/scripts/production-smoke-test.mjs
```

---

## Cloudflare proxy (optional, later)

Only enable orange-cloud proxy **after**:

1. HTTPS works with DNS-only (grey cloud)
2. Vercel certificate is valid
3. Full login + API flow tested end-to-end

If enabling proxy later, set SSL mode to **Full (strict)** in Cloudflare.

---

## Rollback

To remove `app.dxcon.com.vn`:

1. Delete the DNS record in Cloudflare.
2. Remove the domain from Vercel → Domains.
3. Users can still access auth routes on preview deployments for testing.

---

## Blockers

| Blocker | Severity | Action |
| --- | --- | --- |
| DNS record not created | Critical | Complete Steps 1–2 |
| Certificate pending | High | Wait; confirm DNS-only proxy |
| `NEXT_PUBLIC_APP_URL` not set | Critical | Set in Vercel env before deploy |
