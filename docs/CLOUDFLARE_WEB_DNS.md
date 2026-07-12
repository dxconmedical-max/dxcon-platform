# Cloudflare web DNS

Configure DNS for DxCon web domains pointing to Vercel.

## Domains

- `dxcon.com.vn` — marketing
- `www.dxcon.com.vn` — marketing (redirect to apex in app middleware)
- `app.dxcon.com.vn` — application

## Steps

1. In **Vercel** → Project → Domains, add each domain above
2. Vercel displays required DNS records (typically `CNAME` or `A` records)
3. In **Cloudflare** → DNS, create records using the **exact values from Vercel**
4. For `www`, either:
   - CNAME to Vercel as instructed, or
   - rely on middleware apex redirect after DNS resolves
5. Wait for propagation and verify in Vercel domain dashboard

## Important

- Do not invent DNS targets — copy from Vercel domain configuration UI
- API host `api.dxcon.com.vn` is separate from web DNS (Render/backend provider)
- SSL/TLS: use Full (strict) when origin certificates are valid

## Verification

- `https://dxcon.com.vn` loads marketing site
- `https://app.dxcon.com.vn/login` loads sign-in
- Sign-in completes against `https://api.dxcon.com.vn` without CORS errors
