# DxCon Partner Guide — Enterprise v1.0

## Partner Ecosystem

DxCon partners integrate laboratories, clinics, HIS/LIS systems, and marketplace services through standardized APIs and the Partner Portal.

## Entry Points

| Resource | URL |
|----------|-----|
| Partner Portal | `/developer` · `/developer-portal` |
| Marketplace Platform | `/marketplace-platform` |
| Integration Hub | `/integration-hub` |
| Plugin SDK | [PLUGIN_SDK_GUIDE.md](PLUGIN_SDK_GUIDE.md) |

## Integration Workflow

1. Register API client in Developer Portal.
2. Review OpenAPI spec at `/api/v1/system/routes` or generated SDK in `backend/generated_api/`.
3. Test in Integration Hub sandbox: `/integration-hub/sandbox`.
4. Validate HL7/FHIR mappings via Standards Advanced hub.

## Marketplace

Partners list services on the Regional Marketplace. Overview at `/healthcare-ecosystem/dxcon-marketplace`.

## Federation

Cross-organization data exchange uses Federation Platform at `/federation-platform` with explicit consent records.

## Certification

Partner certification track (scaffold): `/healthcare-ecosystem/certification-center`.

## Support

Integration blockers: [SUPPORT_GUIDE.md](SUPPORT_GUIDE.md) → ticket channel with `INTEGRATION` category.

## API Guidelines

- Use `/api/v1/*` versioned endpoints only.
- Respect rate limits (see Security & Compliance hub).
- Never send production PHI to sandbox environments.
