# Staging DNS Setup — Release 9.0

**Do not invent DNS targets.** Copy exact values from Vercel / Render after domains are attached.  
**Do not change** production records for `dxcon.com.vn`, `www.dxcon.com.vn`, or `api.dxcon.com.vn`.

---

## Domains

| Domain | Provider | Expected record |
|---|---|---|
| `staging.dxcon.com.vn` | Vercel → Cloudflare | CNAME or A (from Vercel) |
| `app-staging.dxcon.com.vn` | Vercel → Cloudflare | CNAME or A (from Vercel) |
| `api-staging.dxcon.com.vn` | Render → Cloudflare | CNAME (from Render) |

---

## Procedure (each domain)

1. Add domain in Vercel or Render UI.  
2. Copy the exact DNS target shown.  
3. In Cloudflare → DNS → Add record.  
4. Set **Proxy status: DNS only** (grey cloud).  
5. Wait for provider SSL “Valid”.  
6. Test HTTPS.  
7. Only then reconsider orange-cloud proxy (optional, later).

---

## Record worksheet

| Domain | Type | Name | Target (from provider) | Proxy | SSL status | HTTPS test | PASS/FAIL | Evidence |
|---|---|---|---|---|---|---|---|---|
| staging.dxcon.com.vn | | staging | __________ | DNS only | | | | |
| app-staging.dxcon.com.vn | | app-staging | __________ | DNS only | | | | |
| api-staging.dxcon.com.vn | | api-staging | __________ | DNS only | | | | |

---

## Verification commands

```bash
curl -sI https://staging.dxcon.com.vn/ | head -5
curl -sI https://app-staging.dxcon.com.vn/login | head -5
curl -s https://api-staging.dxcon.com.vn/api/v1/system/health
```

Expected: HTTP 200 (or redirect to login for protected app paths). No change to production hosts.
