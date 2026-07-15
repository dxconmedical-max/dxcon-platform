# Mobile API Dependency Matrix — Release 9.0

| Mobile capability | Backend endpoints (prefix `/api/v1`) | Staging prerequisite |
|---|---|---|
| Login / refresh / me | `auth/login`, `auth/refresh`, `auth/me`, `auth/logout` | Staging API + CORS for mobile origin if needed |
| Memberships / org switch | `auth/memberships`, `auth/switch-organization`, `auth/capabilities` | Pilot orgs |
| Patient marketplace browse | public marketplace + patient commerce routes | Migration 020 + seed listings |
| Booking / slots / quotation | patient commerce / marketplace booking APIs | Slot engine + 020 |
| Payments status | marketplace payment APIs | MANUAL_BANK_QR only; no MOCK_TEST in staging |
| Orders / results | orders + clinical release APIs | Migrations 019–020; no auto-release |
| Collector jobs | collector / logistics routes | IoT/logistics 017 as needed |
| Lab accession / specimens | lims `specimens`, `accessions`, lab routes | Migration 016 |
| Analyzer ingest (lab) | analyzer integration routes | Migration 018; simulator staging-only |
| Report verify | clinical verify token route | Explicit release done |

## CORS note for mobile

Native apps typically do not require browser CORS. Flutter web (if used) requires staging CORS origins for the web origin. Keep `CORS_ORIGINS` staging-only.
