# Mobile Release Roadmap — Release 9.0

Recommended product sequence (reuse `apps/mobile`, progressive enablement):

| Phase | Product | Focus |
|---|---|---|
| M1 | DxCon Patient | Auth, bookings, results (released only), payments status |
| M2 | DxCon Collector | Jobs, patient verify, barcode, custody events |
| M3 | DxCon Lab | Accession queue, cold-chain alerts (read), result intake status |
| M4 | DxCon Admin | Org ops subset; never ship admin PHI offline loosely |

## Shared foundations (prepare before M1 GA)

1. Authentication + refresh  
2. Secure token storage  
3. API client (correlation ID, org header)  
4. Role/permission model  
5. Navigation (go_router shells)  
6. Environment configuration (dev/staging/prod)  
7. Push-notification abstraction  
8. Camera / QR abstraction  
9. Offline queue + sync engine  
10. Local encrypted storage  
11. Deep-link contract  
12. Design tokens  
13. Error handling  
14. Analytics / crash reporting abstraction  

## Out of scope this release

Full feature implementation of M1–M4. Release 9.0 delivers **documentation + staging API readiness** only.
