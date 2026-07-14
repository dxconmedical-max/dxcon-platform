# Release 9.0 — Production Cutover Runbook

**Candidate:** `release/8.1-production-integration`  
**Do not start this runbook until staging smoke + critical UAT pass.**  
**Do not run production migrations without explicit operator approval and a verified backup.**

---

## Preconditions

- [ ] Staging smoke PASS
- [ ] Staging UAT critical path PASS (login, booking, validation, release, isolation)
- [ ] Production backup/snapshot confirmed restorable
- [ ] `CORS_ORIGINS` ready to set exactly as documented
- [ ] Redis and SMTP plan agreed (SMTP may remain disabled with honest UI)

---

## Required sequence

1. **Freeze production changes** (no parallel deploys / schema edits).
2. **Confirm backup/snapshot** of production Postgres (and note restore procedure).
3. **Confirm Render environment variables** (see `docs/RELEASE_9_MANUAL_INFRASTRUCTURE_CHECKLIST.md`).
4. **Confirm Redis connectivity** (`REDIS_URL` set; readiness check OK).
5. **Confirm SMTP** — if not ready, leave password reset disabled (honest UI already in place).
6. **Set Render CORS:**
   ```text
   CORS_ORIGINS=https://dxcon.com.vn,https://www.dxcon.com.vn,https://app.dxcon.com.vn
   ```
7. **Deploy backend** release candidate from `release/8.1-production-integration`.
8. **Verify backend health** — `GET https://api.dxcon.com.vn/api/v1/system/health` → 200; no startup blockers.
9. **Run production migrations** in order **016 → 017 → 018 → 019 → 020** with explicit approval only after backup.
10. **Verify schema + application boot** (post-migration queries in migration plan).
11. **Add `app.dxcon.com.vn` to Vercel** Domains.
12. **Add exact DNS record in Cloudflare as DNS only** (target copied from Vercel UI).
13. **Wait for Vercel SSL certificate** (Valid Configuration).
14. **Configure Vercel production variables** (`NEXT_PUBLIC_*` checklist).
15. **Deploy frontend** release candidate.
16. **Run production smoke test.**
17. **Run critical UAT subset** (login, one clinical path, one commerce path, isolation smoke).
18. **Monitor logs and error rates** for an agreed window.
19. **Approve or roll back.**
20. **Tag release** (e.g. `release/9.0`) **only after** successful validation — do not tag earlier.

---

## Exact `app.dxcon.com.vn` setup

1. Vercel → Project → Domains → Add `app.dxcon.com.vn`.
2. Copy the DNS target **shown by Vercel** (do not invent).
3. Cloudflare → DNS → CNAME `app` → that target → **DNS only** (grey cloud).
4. Wait until Vercel shows certificate Valid.
5. Confirm `https://app.dxcon.com.vn/login` returns 200.
6. Confirm `https://app.dxcon.com.vn/app` redirects unauthenticated users to `/login`.

---

## Rollback procedures

| Layer | Rollback |
|---|---|
| Frontend | Redeploy previous Vercel production deployment |
| Backend | Redeploy previous Render deploy of last known-good commit |
| Migrations | Prefer **forward-fix** migration; restore DB snapshot only if data corruption |
| DNS | Remove/revert `app` record; keep apex site on previous known-good CDN config |
| Environment variables | Restore previous Render/Vercel env values from vault; redeploy |

---

## Go / no-go criteria

| Criterion | Required |
|---|---|
| Health 200 | Yes |
| CORS live allows three production origins | Yes |
| Attacker origin denied | Yes |
| Protected `/app` redirects to login | Yes |
| No auto-release of clinical reports | Yes |
| Payment claims remain honest | Yes |
| Critical UAT pass | Yes |

If any Critical criterion fails → **rollback** and keep production on prior release.
