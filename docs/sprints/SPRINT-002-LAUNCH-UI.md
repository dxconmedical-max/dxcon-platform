# SPRINT-002 — Launch UI / Product Shell

## Sprint ID

`SPRINT-002`

## Title

Launch UI and Product Shell

## Status

`DONE`

## Dates

- **Start:** 2026-06-20
- **End:** 2026-07-05

---

## Goal

Replace scattered pilot pages with a unified product shell: marketing home, login, role-based `/app/*` dashboards, shared CSS, and demo-safe actions.

## Business Value

Pilot users and investors need a coherent product experience — not a list of internal demo links. Launch UI is the commercial face of DxCon before mobile and SaaS.

## Scope

- Shared layout: sidebar, nav, tables, cards, status badges
- `backend/app/static/css/dxcon.css` product stylesheet
- Marketing home `/home` with hero, CTAs, partners section
- Login page with demo role shortcuts
- Role dashboards: Executive, Reception, Doctor, Lab, Collector, Patient, System
- Module pages: patients, orders, reports, samples, collections, finance
- Demo actions (non-destructive) via `launch_ui_actions.py`
- Brand assets: logo, favicon, app icons, `BRAND_GUIDELINES.md`
- Verify script `verify_launch_ui.py`
- Unit tests `test_launch_ui.py`

## Out of Scope

- Full API-backed CRUD for every screen (demo data fallbacks acceptable)
- Mobile Flutter feature parity
- White-label tenant theming in Launch UI

## Deliverables

- [x] `backend/app/web/launch_ui.py`, `launch_ui_lib.py`, `launch_ui_modules.py`
- [x] `backend/app/web/launch_ui_data.py`, `launch_ui_actions.py`
- [x] `/home` marketing hero (Healthcare Ecosystem, Book Demo, Request Quote, Video Demo)
- [x] `/login`, `/login/demo?role=*`
- [x] `/app/executive`, `/app/reception`, `/app/doctor`, `/app/lab`, `/app/collector`, `/app/patient`
- [x] `backend/scripts/verify_launch_ui.py`
- [x] `docs/BRAND_GUIDELINES.md`, `backend/app/static/branding/*`

## Data Impact

| Area | Change | Migration |
|------|--------|-----------|
| None | Read-only demo queries with fallbacks | — |

## API Impact

| Endpoint | Change |
|----------|--------|
| None | Web-only sprint |

## UI Impact

| Route | Change |
|-------|--------|
| `/home` | Marketing site |
| `/login` | Product login |
| `/app/*` | Role shells and modules |

## Tests

```bash
python3 -m unittest backend.tests.test_launch_ui -v
python3 backend/scripts/verify_launch_ui.py
```

## Verification

Launch UI unit tests PASS. Full `verify_launch_ui.py` requires seeded demo data and running health endpoints.

## Definition of Done

- [x] All role shells navigable after demo login
- [x] Marketing home with brand assets
- [x] CSS shared across public and app pages
- [x] `test_launch_ui.py` PASS
- [x] Sprint status DONE

## Commit Message

```
Launch UI Product Shell - Marketing Home and Role Dashboards
```

## Notes

- Demo password and accounts in `demo_pilot_lib.py`.
- Legacy landing remains at `/demo-landing` for internal pilot links.
- `verify_launch_ui.py` blockers (seeded_counts, health) addressed in SPRINT-003.
