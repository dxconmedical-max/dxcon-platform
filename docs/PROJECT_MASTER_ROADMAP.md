# DxCon Project Master Roadmap

**Role:** Principal Architect  
**Updated:** 2026-07-26  
**Active planning branch:** `release/v2.0.0`  
**Release 1:** Officially frozen (`docs/RELEASE_1_FREEZE.md`)

---

## Release 1 — FROZEN

| Field | Value |
|-------|--------|
| Version | `1.0.0` |
| Status | **Frozen** — hotfix only |
| Branch / tag | `release/v1.0.0` / `v1.0.0` |

### Delivered (baseline)

- Auth platform (frozen)
- Reception M1 — patient, catalog, pricing, order
- Reception extended contracts on line (payment/docs/handoff APIs as present)
- Sample Collection, Laboratory Workflow, Clinical Report PDF
- Role dashboards, RC1 security hardening
- Flutter Mobile Phase 1 foundation

### Post-freeze rule

No feature work on Release 1. Hotfixes only — see `docs/RELEASE_1_FREEZE.md` and `docs/RELEASE_FREEZE_REPORT.md`.

---

## Release 2 — INITIALIZED

| Field | Value |
|-------|--------|
| Version target | `2.0.0` |
| Status | **Initialized** — roadmap only |
| Branch | `release/v2.0.0` |

### Tracks

Reception M2 · Laboratory · Collector · Doctor · Patient Portal · Mobile

### Milestones (ordered)

| # | Milestone |
|---|-----------|
| 1 | Reception Payment |
| 2 | Receipt |
| 3 | Barcode |
| 4 | QR |
| 5 | Lab Queue |
| 6 | Sample Queue |
| 7 | Laboratory workflow |
| 8 | Collector workflow |
| 9 | Doctor workflow |
| 10 | Patient Portal |
| 11 | Flutter Mobile |

Detail: `docs/RELEASE_2_ROADMAP.md`  
Structure: `docs/release-2/`

### Constraints

- No Release 1 line edits except hotfix  
- Auth freeze remains in force  
- No business logic until milestone kickoff  

---

## Release 3 — FUTURE

| Field | Value |
|-------|--------|
| Version target | `3.0.0` (provisional) |
| Status | **Not started** |

### Candidate themes (planning only)

- Enterprise multi-tenant hardening / white-label
- LIS instrument middleware (HL7 FHIR / ASTM depth)
- Advanced QC (Westgard), MDM-driven reference ranges
- Subscription / insurance / corporate billing depth
- SSO (SAML/OIDC), warehouse/BI connectors
- Geographic DR, Kubernetes ops maturity
- AI clinical assistant with human-in-the-loop only (no auto-release)

Release 3 does not begin until Release 2 freeze and explicit architecture kickoff.

---

## Technical Debt

| ID | Item | Notes |
|----|------|--------|
| TD-001 | Manual SQL migrations; Alembic not adopted | Carry from R1 |
| TD-002 | In-memory rate limiter / queue defaults | Multi-instance risk |
| TD-003 | CSP `unsafe-inline` / `unsafe-eval` | Auth-aware harden later |
| TD-004 | CI primarily on `main`; release-branch PR gaps | Process |
| TD-005 | Workers/schedulers incomplete in prod compose | Ops |
| TD-006 | Redis / SMTP / durable object storage gaps | Ops |
| TD-007 | Postgres E2E preferred over SQLite for GA proofs | Quality |
| TD-008 | Residual Reception post-create order GET observation (KI-R1-001) | Hotfix if reproducible |

---

## Known Risks

| ID | Risk | Mitigation |
|----|------|------------|
| KR-001 | Feature work accidentally lands on `release/v1.0.0` | Freeze lock + hotfix-only policy |
| KR-002 | Auth freeze broken by portal/mobile work | Keep using frozen hooks; no bootstrap redesign |
| KR-003 | Parallel milestones without isolation | One exclusive release commit set per milestone |
| KR-004 | Payment mocks leaking to production | Extension rules; no mock success in prod |
| KR-005 | Lab auto-release / weakened clinical gates | Prohibited; medical validation preserved |
| KR-006 | Live deploy SHA drift vs tags | Ops align to tagged tips |
| KR-007 | Remote tag/branch protection delays R1 publish | PR + admin tag process |

---

## Future Architecture

### Platform shape

```text
[ Web Next.js ]     [ Flutter Mobile ]
        \                 /
         \               /
          v             v
        [ API / Auth-frozen session+JWT ]
                    |
     +--------------+--------------+
     |              |              |
 [ Reception ]  [ Lab/Collector ] [ Portal ]
     |              |              |
 [ Orders/Pay ] [ Specimens ]  [ Results ]
                    |
              [ PDF / Reports ]
                    |
         [ Postgres + Object Storage ]
```

### Architecture principles (forward)

1. **Frozen auth** as the only session bootstrap path until a dedicated auth epic  
2. **Additive contracts** preferred; breaking changes require architecture review  
3. **Clinical gates** never bypassed for speed  
4. **Tenant isolation** mandatory for multi-org  
5. **Release isolation** — exclusive files not mixed across unfinished milestones  
6. **Hotfix vs feature** — R1 hotfixes never carry R2 features  

### Near-term architecture work (docs/design only until scheduled)

- Payment ledger and receipt idempotency design  
- Barcode/QR payload standard shared by Reception and Lab  
- Queue models for lab intake vs sample collection  
- Patient Portal read models over released results  
- Mobile offline cache boundaries  

---

## Document map

| Doc | Role |
|-----|------|
| `docs/RELEASE_1_FREEZE.md` | R1 freeze lock |
| `docs/RELEASE_2_ROADMAP.md` | R2 milestones 1–11 |
| `docs/release-2/README.md` | R2 milestone folder index |
| `docs/PROJECT_MASTER_ROADMAP.md` | This master plan |
| `docs/AUTH_FREEZE.md` | Auth freeze policy |

---

**STOP** — Roadmap initialization only. No business logic implemented.
