# DxCon Release 2.0 Roadmap

## Vision

Transform DxCon from pilot-ready to enterprise-scale multi-tenant SaaS with full commercial operations, advanced integrations, and mobile-first experiences.

## Planned Modules

### Clinical & Laboratory
- Full LIS bidirectional sync (HL7 FHIR, ASTM)
- Instrument middleware (Roche, Abbott, Sysmex)
- Advanced QC with Westgard rules
- Reference range auto-application from MDM

### Reporting & Compliance
- Server-side PDF generation (WeasyPrint/wkhtmltopdf)
- Legal digital certificate signing
- Amendment workflow with patient notification
- Regulatory audit packages (ISO 15189)

### Commercial
- Subscription billing and SaaS metering
- Corporate billing with PO workflows
- Insurance claims integration
- Commission engine for referring doctors
- Multi-currency support

### Patient & Doctor Experience
- Native mobile apps (Flutter — foundation started)
- Push notifications (FCM/APNs)
- Telehealth consultation placeholder
- AI interpretation (advisory, human-in-loop)

### Enterprise
- Full multi-tenant data isolation
- White-label branding per organization
- SSO (SAML, OIDC)
- Data warehouse and BI connectors
- Population health analytics

### Operations
- Kubernetes Helm charts
- Auto-scaling workers
- Real-time alerting (PagerDuty/Opsgenie)
- Disaster recovery automation
- Geographic redundancy

## Technical Prerequisites for 2.0

1. **Release 1.0 deployed** — All verify scripts passing in production
2. **PostgreSQL performance baseline** — Query optimization, indexes reviewed
3. **Notification providers** — At least SMTP + one SMS provider live
4. **Storage migration** — S3/MinIO for reports and attachments
5. **Security audit** — External penetration test completed
6. **Pilot feedback** — 30-day pilot with at least one laboratory

## Recommended Improvements (Release 1.x patches)

| Priority | Item | Effort |
|----------|------|--------|
| High | Wire SMTP for report-released notifications | 2 days |
| High | PDF server-side rendering | 3 days |
| Medium | Consolidate legacy portal routes | 5 days |
| Medium | Dashboard query optimization | 3 days |
| Low | Remove demo/legacy UI routes | 2 days |
| Low | SQLite test teardown fix | 1 day |

## Timeline Estimate

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 2.0 Alpha | 8 weeks | LIS + PDF + notifications |
| 2.0 Beta | 4 weeks | Billing + mobile hardening |
| 2.0 GA | 4 weeks | Enterprise SSO + white-label |

## Success Metrics

- Order-to-report TAT < 4 hours (routine panel)
- 99.9% API uptime
- < 500ms p95 dashboard load
- Zero critical security findings
- 3+ pilot customers live
