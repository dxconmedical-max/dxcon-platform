# DxCon Production Cutover Runbook

**Status:** Planning document only. Public production remains **NO-GO** until all blockers in §10 are cleared.

**Verified locally (not public cutover):** P0-A/B/C/D PASS · P0-8 local durable runtime PASS · P0-9 audit PASS · application stack healthy on Compose.

**Do not:** commit secrets, generate fake TLS certs, run destructive restore against production, delete Docker volumes, or weaken security gates.

---

## 1. Pre-cutover checklist

- [ ] Branch/release artifact selected and freeze window agreed
- [ ] `deployment/env/production.env` exists **locally/untracked** (never commit); copied from `production.env.example`
- [ ] All placeholders in `production.env` replaced with real values (see §5)
- [ ] `EMAIL_DRY_RUN=false` only after real SMTP is verified
- [ ] DNS records created and resolving (see §2)
- [ ] Real TLS certificates provisioned under `deployment/certs/` (see §3)
- [ ] `deployment/nginx/https.conf` created from `https.conf.example` (gitignored)
- [ ] Offsite backup target + encryption keys ready (see §6)
- [ ] Isolated restore target prepared (staging DB; **not** production)
- [ ] Monitoring stack wired for **production** labels/targets (see §7)
- [ ] On-call / alert routing verified
- [ ] Rollback owner and communication channel assigned (see §9)
- [ ] Maintenance window communicated to stakeholders

---

## 2. Required DNS records

Hostnames are taken from repository configuration (`deployment/env/production.env.example`, `backend/app/core/security.py`).

Replace `<EDGE_IP_OR_LB>` and `<CDN_OR_EDGE>` with your real targets. **Do not invent IPs.**

| Record | Type | Name | Value (placeholder) | Purpose |
|--------|------|------|---------------------|---------|
| Apex | A / AAAA / CNAME | `dxcon.com.vn` | `<EDGE_IP_OR_LB>` | Public site / CORS origin |
| WWW | CNAME / A | `www.dxcon.com.vn` | `<EDGE_IP_OR_LB>` or apex | Public site |
| App | CNAME / A | `app.dxcon.com.vn` | `<EDGE_IP_OR_LB>` | `WEB_APP_URL` |
| Admin | CNAME / A | `admin.dxcon.com.vn` | `<EDGE_IP_OR_LB>` | Admin CORS origin |
| API | CNAME / A | `api.dxcon.com.vn` | `<EDGE_IP_OR_LB>` | `API_BASE_URL` / API clients |
| Doctor | CNAME / A | `doctor.dxcon.com.vn` | `<EDGE_IP_OR_LB>` | Role CORS origin |
| Patient | CNAME / A | `patient.dxcon.com.vn` | `<EDGE_IP_OR_LB>` | Role CORS origin |
| Lab | CNAME / A | `lab.dxcon.com.vn` | `<EDGE_IP_OR_LB>` | Role CORS origin |
| Clinic | CNAME / A | `clinic.dxcon.com.vn` | `<EDGE_IP_OR_LB>` | Role CORS origin |
| Collector | CNAME / A | `collector.dxcon.com.vn` | `<EDGE_IP_OR_LB>` | Role CORS origin |

Optional ACME / mail (if used by your CA or SMTP provider):

| Record | Type | Name | Value |
|--------|------|------|-------|
| ACME HTTP-01 | — | path served by nginx `/.well-known/acme-challenge/` | per CA |
| ACME DNS-01 | TXT | `_acme-challenge.<host>` | `<CA_TOKEN>` |
| SPF/DKIM/DMARC | TXT | per SMTP provider docs | `<PROVIDER_VALUES>` |

**Verify before cutover:**

```bash
dig +short dxcon.com.vn
dig +short www.dxcon.com.vn app.dxcon.com.vn admin.dxcon.com.vn api.dxcon.com.vn
dig +short doctor.dxcon.com.vn patient.dxcon.com.vn lab.dxcon.com.vn clinic.dxcon.com.vn collector.dxcon.com.vn
```

---

## 3. TLS provisioning procedure

### What already exists

| Asset | Path | Notes |
|-------|------|-------|
| HTTP edge (local/durable) | `deployment/nginx/default.conf` | Listen `:80` only |
| TLS template | `deployment/nginx/https.conf.example` | HTTP→HTTPS redirect + TLS 1.2/1.3 |
| TLS Compose overlay | `docker-compose.production.tls.yml` | Mounts certs + `https.conf` |
| Gitignore | `deployment/certs/`, `deployment/nginx/https.conf` | Private material must stay untracked |

### Expected certificate files (do not commit)

```text
deployment/certs/fullchain.pem
deployment/certs/privkey.pem
```

### Activation steps (after real certificates exist)

```bash
# 1) Place CA-issued certs (examples — use your CA/process)
mkdir -p deployment/certs
# copy real fullchain.pem and privkey.pem into deployment/certs/
chmod 600 deployment/certs/privkey.pem

# 2) Activate nginx HTTPS config from template
cp deployment/nginx/https.conf.example deployment/nginx/https.conf
# edit server_name if you pin exact hostnames

# 3) Bring nginx up with TLS overlay (no volume wipe)
docker compose \
  -f docker-compose.production.yml \
  -f docker-compose.production.tls.yml \
  up -d nginx

# 4) Validate
docker compose -f docker-compose.production.yml exec nginx nginx -t
curl -fsS https://api.dxcon.com.vn/live
curl -fsS https://api.dxcon.com.vn/ready
curl -sI http://api.dxcon.com.vn/ | head   # expect 301 → https
```

**Do not** generate self-signed certificates for public cutover. Self-signed is not production-ready.

---

## 4. SMTP setup

### Required environment keys

| Variable | Requirement |
|----------|-------------|
| `SMTP_HOST` | Real provider hostname (not `smtp.example.com`) |
| `SMTP_PORT` | Typically `587` (STARTTLS) or provider docs |
| `SMTP_USE_TLS` | `true` for STARTTLS/TLS as configured by app |
| `SMTP_USER` | Provider username |
| `SMTP_PASSWORD` | Provider password/app password (**never commit**) |
| `SMTP_FROM` | Verified sender (e.g. `noreply@your-domain`) |
| `EMAIL_DRY_RUN` | **`false` for public cutover** |

Local durable proof may use `EMAIL_DRY_RUN=true`. Public cutover must verify **real delivery** to a controlled inbox.

### Verification (no secrets in logs)

```bash
# Confirm flags only — do not print passwords
grep -E '^(EMAIL_DRY_RUN|SMTP_HOST|SMTP_PORT|SMTP_FROM|SMTP_USE_TLS)=' deployment/env/production.env \
  | sed -E 's/(PASSWORD)=.*/\1=***/'
# Send a controlled test via your verified application/admin path or provider console
```

---

## 5. Secret management

### Injection model currently supported

| Mechanism | Status |
|-----------|--------|
| Compose `env_file: deployment/env/production.env` | **Supported (current)** |
| Docker Secrets / Swarm secrets | **Not wired** in production compose |
| Cloud secret manager (AWS/GCP/Azure/Vault) | **Not implemented** in this repo path |
| Example templates | `deployment/env/production.env.example` — placeholders only |

**Operational requirement:** Before public cutover, inject secrets via a controlled mechanism (orchestrator secrets, cloud SM, or sealed env on the host). External secret manager is **not** implemented in-compose — treat as a blocker until ops process is documented and enforced.

### Required production secrets / sensitive keys

| Key | Purpose |
|-----|---------|
| `SECRET_KEY` | Flask/session signing (≥32 chars, non-placeholder) |
| `JWT_SECRET_KEY` | JWT signing (≥32 chars, non-placeholder, **distinct** from `SECRET_KEY`) |
| `POSTGRES_PASSWORD` | Postgres role password (must match `DATABASE_URL`) |
| `DATABASE_URL` | PostgreSQL URL (`postgresql://…`) — no `replace-me` |
| `SMTP_PASSWORD` | Mail provider credential |
| `REDIS_URL` | Redis URL (add auth if Redis leaves private network) |
| Optional: `S3_*`, integration/webhook signing secrets | If those features are enabled in production |

### Rules

- Never commit `deployment/env/production.env`
- Never put real values in `*.example`
- Never print secrets in CI logs, chat, or runbooks
- Confirm `/ready` and `/live` payloads contain **no** secret material
- Application fail-closed validation rejects placeholder/short production secrets

---

## 6. Database backup

### What already exists

| Asset | Path |
|-------|------|
| Postgres dump script | `deployment/scripts/backup_postgres.sh` |
| Uploads archive script | `deployment/scripts/backup_uploads.sh` |
| Dry-run restore helper | `deployment/scripts/restore_postgres_dry_run.sh` |
| Verify wrapper | `deployment/scripts/verify_backup_restore.sh` |
| Rehearsal tooling | `backend/scripts/backup_restore_rehearsal.py`, `backup_restore_lib.py` |
| Docs | `docs/BACKUP.md`, `docs/BACKUP_RESTORE_RUNBOOK.md` |

### Host dependency

`pg_dump` / `pg_restore` must be available on the operator host **or** run inside a Postgres/client container:

```bash
# Example: dump via running postgres service (no volume delete)
docker compose -f docker-compose.production.yml exec -T postgres \
  pg_dump -U dxcon -d dxcon | gzip > "./backups/postgres/dxcon-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
```

If `pg_dump` is missing on the host, install client tools or always dump via the container as above.

### Recommended production policy (ops must implement)

| Item | Guidance |
|------|----------|
| Schedule | At least daily full logical dump; prefer continuous WAL/PITR if using managed Postgres |
| Retention | ≥ 30 days daily (per `docs/BACKUP.md`); define weekly/monthly as needed |
| Encryption | Encrypt at rest (disk encryption + encrypted backup objects) |
| Offsite | Copy to separate account/region/object storage; access-controlled |
| Restore | Restore only to **isolated** staging/scratch DB — **never** as a casual test against production |
| Verification | Quarterly isolated restore + app smoke on restored copy |

### Commands (non-destructive)

```bash
# Backup (host script; requires DATABASE_URL + pg_dump)
export DATABASE_URL='postgresql://dxcon:<REDACTED>@<HOST>:5432/dxcon'
export BACKUP_DIR=./backups/postgres
./deployment/scripts/backup_postgres.sh

# Uploads
export STORAGE_PATH=/var/lib/dxcon/uploads   # or host path mount
export BACKUP_DIR=./backups/uploads
./deployment/scripts/backup_uploads.sh

# Dry-run / library verification (does not wipe production)
./deployment/scripts/verify_backup_restore.sh
# or: python backend/scripts/backup_restore_rehearsal.py --dry-run
```

**Do not** run destructive restore against the live production database during cutover validation.

---

## 7. Monitoring

### What already exists (configs only — not active in production compose)

| Asset | Path |
|-------|------|
| Prometheus scrape config | `deployment/monitoring/prometheus.yml` (labels say **staging**) |
| Alert rules | `deployment/monitoring/alerts/dxcon-alerts.yml` |
| Alertmanager | `deployment/monitoring/alertmanager/alertmanager.yml` |
| Grafana provisioning | `deployment/monitoring/grafana/...` |
| Loki | `deployment/monitoring/loki/loki.yml` |

**Important:** `docker-compose.production.yml` does **not** include Prometheus/Grafana/Alertmanager/Loki services. Monitoring configs exist but are **not active** for production Compose until ops wires them (separate compose overlay or external observability platform).

### Existing alert rules (staging-oriented names)

Already defined in `dxcon-alerts.yml` (examples): `ApiErrorRateHigh`, `DatabaseUnavailable`, `RedisUnavailable`, `QueueBacklogHigh`, `ReadinessFailed`, webhook/notification failure alerts.

### Required production alerts (must be verified live)

| Alert need | Suggested approach |
|------------|--------------------|
| API down | Blackbox/up scrape or container health + synthetic `GET /live` |
| `/ready` failing | Existing `ReadinessFailed` / scrape `/ready` |
| PostgreSQL unavailable | `DatabaseUnavailable` + postgres exporter |
| Redis unavailable | `RedisUnavailable` + redis exporter |
| Worker stopped | Compose/k8s deadman’s switch or `up{job="worker"}` / process exporter (**add if missing**) |
| Scheduler stopped | Same for scheduler (**add if missing**) |
| High 5xx | `ApiErrorRateHigh` |
| Disk exhaustion | Node/disk exporter alerts (**add if missing**) |
| Repeated job failures | Queue/job failure metrics + logs |

### Wiring outline (ops)

1. Deploy monitoring stack with **production** `external_labels` (not `staging`).
2. Scrape `api:8000` `/metrics/prometheus`, `/ready`, exporters for Postgres/Redis/nginx.
3. Route Alertmanager to on-call (email/Slack/PagerDuty) — configure without committing secrets.
4. Prove each critical alert fires in a controlled test (e.g. temporary scrape pause), then recover.

Until the above is live and verified, monitoring remains a **cutover blocker**.

---

## 8. Deployment order

Execute in this order only:

```text
1. DNS
2. TLS certificates + https.conf
3. Secrets (production.env / secret manager injection)
4. Database backup (pre-change snapshot)
5. Database migration verification
     docker compose -f docker-compose.production.yml exec api \
       python scripts/apply_migrations.py --verify-only
     # apply additive migrations only if required and approved
6. Redis (healthy)
7. API (healthy, /ready=200)
8. Worker (running)
9. Scheduler (running)
10. Nginx (+ TLS overlay)
11. HTTPS verification (cert valid, HTTP→HTTPS redirect)
12. Smoke tests (auth, tenant, IoT, queue, /live, /ready)
13. SMTP real delivery check
14. Monitoring verification (alerts route)
```

### Reference Compose commands

```bash
# Base stack (HTTP edge — local/durable)
docker compose -f docker-compose.production.yml up -d

# Public HTTPS edge (after certs)
docker compose \
  -f docker-compose.production.yml \
  -f docker-compose.production.tls.yml \
  up -d

# Never:
# docker compose down -v
# docker volume rm …
```

---

## 9. Rollback plan (non-destructive)

| Layer | Action |
|-------|--------|
| Application image | Redeploy previous known-good image tags; `up -d` without `-v` |
| Configuration | Restore previous `production.env` from secure backup; recreate api/worker/scheduler |
| Nginx / TLS | Revert to previous `https.conf` or temporarily fall back to HTTP **only** inside private network — do not disable TLS on the public internet without an approved incident plan |
| Migrations | Prefer forward-fix. Do **not** DROP/reset production. If a migration is unsafe, stop rollout and restore from backup onto an isolated instance for forensics |
| Containers | `docker compose … up -d` previous revision; **never** `down -v` |
| Data | Restore from backup only with incident commander approval; prefer restore to isolated DB then cut over DNS if needed |

---

## 10. GO / NO-GO checklist

Production may be marked **GO** only when **all** are true:

- [ ] DNS resolves for apex/www/app/admin/api and role hosts
- [ ] HTTPS works with a **valid** public certificate
- [ ] HTTP redirects to HTTPS
- [ ] `/live` returns success over HTTPS
- [ ] `/ready` returns HTTP 200 and `ready=true` over HTTPS
- [ ] Authentication works (P0-A behavior)
- [ ] Tenant isolation works (P0-C behavior)
- [ ] IoT device authentication works (P0-D behavior)
- [ ] Authorization gates work (P0-B behavior)
- [ ] Worker processes durable queue jobs
- [ ] Scheduler runs due work
- [ ] Real SMTP delivery verified (`EMAIL_DRY_RUN=false`)
- [ ] Automated backup completed to offsite storage
- [ ] Isolated restore verified (non-production target)
- [ ] Monitoring alerts verified end-to-end
- [ ] Secrets not exposed in git, logs, or health payloads
- [ ] No production placeholder credentials remain

**Current public production status: NO-GO** until the infrastructure blockers below are cleared.

---

## Appendix A — Service topology (existing)

From `docker-compose.production.yml`:

| Service | Role |
|---------|------|
| `postgres` | PostgreSQL 16, volume `production_postgres` |
| `redis` | Redis 7 AOF, volume `production_redis` |
| `api` | Gunicorn via `production_start.py api` |
| `worker` | `production_start.py worker` |
| `scheduler` | `production_start.py scheduler` |
| `nginx` | Edge proxy `:80` / `:443` |

Health: API `/ready`; nginx depends on healthy API; Postgres/Redis not published to host ports in Compose.

---

## Appendix B — Related documents

- `docs/BACKUP.md`
- `docs/BACKUP_RESTORE_RUNBOOK.md`
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
- `docs/PILOT_DEPLOYMENT_GUIDE.md`
- `deployment/nginx/https.conf.example`
- `docker-compose.production.tls.yml`
