# DxCon Launch Checklist

**Last updated:** 2026-07-05  
**Use for:** Release 1.0 Pilot and commercial go-live  
**Related:** [`GO_LIVE_RUNBOOK.md`](GO_LIVE_RUNBOOK.md), [`PROJECT_MANUAL.md`](PROJECT_MANUAL.md)

Mark each item: ☐ Not started · ◐ In progress · ☑ Done

---

## Domain

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Production domain registered (e.g. `dxcon.health`) | ☐ | |
| 2 | Staging subdomain configured | ☐ | |
| 3 | WWW → apex redirect | ☐ | |
| 4 | Marketing site (`/home`) served on public domain | ☐ | |

---

## DNS

| # | Item | Status | Notes |
|---|------|--------|-------|
| 5 | A/AAAA or CNAME to hosting provider | ☐ | |
| 6 | API subdomain if split (optional) | ☐ | |
| 7 | MX records for mail (if self-hosted) | ☐ | |
| 8 | TTL lowered before cutover (≤300s) | ☐ | |

---

## SSL

| # | Item | Status | Notes |
|---|------|--------|-------|
| 9 | TLS certificate issued (Let's Encrypt or provider) | ☐ | |
| 10 | HTTPS enforced; HTTP redirect | ☐ | |
| 11 | HSTS enabled for production | ☐ | |
| 12 | Certificate auto-renewal verified | ☐ | |

---

## Email

| # | Item | Status | Notes |
|---|------|--------|-------|
| 13 | Transactional email provider configured (SMTP/API) | ☐ | |
| 14 | SPF record published | ☐ | |
| 15 | DKIM signing enabled | ☐ | |
| 16 | DMARC policy set | ☐ | |
| 17 | Test: password reset / notification delivery | ☐ | |

---

## Master Data

| # | Item | Status | Notes |
|---|------|--------|-------|
| 18 | MDM templates reviewed for pilot tenant | ☐ | `backend/templates/mdm/` |
| 19 | Reference data imported (tests, labs, clinics, pricing) | ☐ | `/app/mdm` |
| 20 | Import report archived | ☐ | `MASTER_DATA_IMPORT_REPORT.json` |
| 21 | Legacy sync to operational tables verified | ☐ | `verify_mdm.py` |

---

## Real Users

| # | Item | Status | Notes |
|---|------|--------|-------|
| 22 | Demo self-registration disabled for privileged roles | ☐ | |
| 23 | Admin accounts created per site | ☐ | |
| 24 | Role matrix documented (reception, lab, doctor, collector) | ☐ | |
| 25 | Password policy enforced | ☐ | |
| 26 | No shared demo passwords in production | ☐ | |

---

## UAT

| # | Item | Status | Notes |
|---|------|--------|-------|
| 27 | Reception UAT PASS | ☐ | `verify_uat_reception.py` |
| 28 | Collector UAT PASS | ☐ | `verify_uat_collector.py` |
| 29 | Lab UAT PASS | ☐ | `verify_uat_lab.py` |
| 30 | Doctor UAT PASS | ☐ | `verify_uat_doctor.py` |
| 31 | Patient UAT PASS | ☐ | `verify_uat_patient.py` |
| 32 | UAT final report generated | ☐ | `UAT_FINAL_REPORT.json` |

---

## Backup

| # | Item | Status | Notes |
|---|------|--------|-------|
| 33 | Automated DB backup schedule | ☐ | [`BACKUP_RUNBOOK.md`](BACKUP_RUNBOOK.md) |
| 34 | Backup restore tested (staging) | ☐ | [`RESTORE_RUNBOOK.md`](RESTORE_RUNBOOK.md) |
| 35 | RPO/RTO documented | ☐ | [`DISASTER_RECOVERY.md`](DISASTER_RECOVERY.md) |
| 36 | Backup verification API healthy | ☐ | `/api/v1/operations/backups` |

---

## Monitoring

| # | Item | Status | Notes |
|---|------|--------|-------|
| 37 | Prometheus scraping API metrics | ☐ | |
| 38 | Grafana dashboards loaded | ☐ | |
| 39 | Alertmanager routes configured | ☐ | |
| 40 | Health jobs: `/health`, `/ready`, `/live` | ☐ | |
| 41 | JSON logs with `request_id` | ☐ | `LOG_FORMAT=json` |
| 42 | `verify_monitoring_stack.py` PASS | ☐ | |

---

## Security

| # | Item | Status | Notes |
|---|------|--------|-------|
| 43 | `SECRET_KEY` / `JWT_SECRET_KEY` from env only | ☐ | |
| 44 | `security_preflight.py` PASS (8/8) | ☐ | |
| 45 | Public routes reviewed | ☐ | `verify_public_routes.py` |
| 46 | Logistics/collector APIs authenticated | ☐ | |
| 47 | Dependency audit clean or accepted risks | ☐ | |
| 48 | Penetration test or security sign-off | ☐ | |

---

## Pilot

| # | Item | Status | Notes |
|---|------|--------|-------|
| 49 | Pilot clinic onboarded | ☐ | `/pilot-status` |
| 50 | Pilot lab onboarded | ☐ | |
| 51 | Collector network assigned | ☐ | |
| 52 | Pilot checklist signed | ☐ | `/pilot-checklist` |
| 53 | Support escalation path documented | ☐ | [`SUPPORT_GUIDE.md`](SUPPORT_GUIDE.md) |

---

## Go Live

| # | Item | Status | Notes |
|---|------|--------|-------|
| 54 | Maintenance window procedure tested | ☐ | |
| 55 | Go-live runbook executed | ☐ | [`GO_LIVE_RUNBOOK.md`](GO_LIVE_RUNBOOK.md) |
| 56 | `final_ga_smoke.py` PASS | ☐ | |
| 57 | Executive dashboard live | ☐ | `/app/executive` |
| 58 | Rollback plan confirmed with team | ☐ | [`ROLLBACK_RUNBOOK.md`](ROLLBACK_RUNBOOK.md) |
| 59 | Post go-live 24h watch scheduled | ☐ | |
| 60 | Release tagged in git | ☐ | `v1.0.0-pilot` |

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product | | | |
| Engineering | | | |
| Operations | | | |
| Pilot customer | | | |

---

## Automation

```bash
# Partial automated checks
python3 backend/scripts/verify_readiness_pack.py
python3 backend/scripts/verify_pilot_readiness.py
python3 backend/scripts/verify_production_deployment.py
```

Report output: `backend/generated_release/GO_LIVE_CHECKLIST.json` (when generated by readiness pack).
