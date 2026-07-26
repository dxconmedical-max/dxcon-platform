# Reception M2 — Frontend Module

**Release:** 2.0 · Branch `release/v2.0.0`  
**Status:** Architecture foundation only  
**Payment / business logic:** **Not implemented in this module yet**

## Domains

| Domain | Path | Canonical API client |
|--------|------|----------------------|
| Payment | `./payment` | `@/lib/api/reception` → `collectReceptionPayment` |
| Receipt | `./receipt` | Derived from payment record + print surface (no duplicate POST) |
| Barcode | `./barcode` | `fetchReceptionBarcodes` |
| QR | `./qr` | Payment / VNPay / static / dynamic / sample / tracking + verify |
| Lab Queue | `./lab-queue` | Dashboard, priority, waiting→verified, live refresh |
| Sample Queue | `./sample-queue` | Collected→completed logistics, tracking, history |

## Rules

1. **Reuse Release 1** — AppShell, `useAuth` / `useRequireAuth`, `apiRequest`, reception workspace prefix.  
2. **No duplicated business logic** — services re-export `@/lib/api/reception`; do not copy mappers.  
3. **Auth freeze** — do not touch frozen auth files.  
4. **Legacy UI** — `OrderSteps.tsx` remains the interim R1 surface until M2 pages are implemented later.

See `docs/RECEPTION_M2_ARCHITECTURE.md`.
