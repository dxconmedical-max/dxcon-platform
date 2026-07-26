# Reception Milestone 2 — Architecture

**Role:** Principal Architect  
**Release:** 2.0 · Branch `release/v2.0.0`  
**Status:** Foundation only — **no payment / business logic implemented**  
**Backend changes:** None  
**Production deploy:** None  

---

## 1. Goals

Define a modular frontend architecture for Reception M2 domains:

| Domain | Roadmap milestone |
|--------|-------------------|
| Payment | R2 M1 |
| Receipt | R2 M2 |
| Barcode | R2 M3 |
| QR | R2 M4 |
| Lab Queue | R2 M5 |
| Sample Queue | R2 M6 (bridge to Collector) |

This pass creates **structure + contracts + docs**. Implementation of collection/print/handoff UI logic is deferred to milestone kickoffs.

---

## 2. Reuse Release 1 architecture

| Layer | Reuse |
|-------|--------|
| Shell / auth | `AppShell`, frozen `useAuth` / session — **do not modify auth freeze files** |
| HTTP | `@/services/api` → `apiRequest` |
| Reception client | `@/lib/api/reception` (canonical — **single source of business HTTP + mappers**) |
| UI primitives | `@/components/ui/*`, reception `_components/ui` as needed |
| Routing | Next.js App Router under `apps/web/src/app/app/reception/` |
| Roles | Existing Reception workspace guards via AppShell |

**Interim R1 surface:** `workflow/OrderSteps.tsx` already contains payment/documents/handoff UI. M2 pages must **not** fork that logic. Future kickoffs extract into `modules/reception-m2/*` by moving call sites to the facades — not by copying mappers.

---

## 3. Module layout

```text
apps/web/src/modules/reception-m2/
  index.ts
  README.md
  shared/ReceptionM2Placeholder.tsx
  payment/     types · service · hooks · components
  receipt/     types · service · hooks · components
  barcode/     types · service · hooks · components
  qr/          types · service · hooks · components
  lab-queue/   types · service · hooks · components
  sample-queue/ types · service · hooks · components
```

### Pages (App Router)

| Route | Purpose |
|-------|---------|
| `/app/reception/m2` | Architecture hub |
| `/app/reception/m2/payment` | Payment placeholder |
| `/app/reception/m2/receipt` | Receipt placeholder |
| `/app/reception/m2/barcode` | Barcode placeholder |
| `/app/reception/m2/qr` | QR placeholder |
| `/app/reception/m2/lab-queue` | Lab queue placeholder |
| `/app/reception/m2/sample-queue` | Sample queue placeholder |

---

## 4. Layer responsibilities

| Layer | Responsibility | Rule |
|-------|----------------|------|
| **pages** | Route + AppShell + compose placeholders | No domain HTTP |
| **components** | Presentational panels (placeholders now) | No duplicated mappers |
| **hooks** | Future state orchestration | Stubs return `architecture_only` |
| **services** | Thin re-exports of `@/lib/api/reception` | **No second client** |
| **types** | Re-export + view-model aliases | No divergent DTOs |

---

## 5. No duplicated business logic

1. All payment / barcode / handoff HTTP stays in `@/lib/api/reception`.  
2. `modules/reception-m2/*/service.ts` only re-exports (plus pure view mappers for receipt/sample-queue).  
3. Do not reimplement `mapPaymentRecord`, `mapBarcodes`, `mapLabHandoff` in the module.  
4. Do not add backend routes in this foundation.  
5. Sample queue has **no new API** — maps lab-handoff `collection` / `queue_entry`.

---

## 6. Dependency flow

```text
Page → (future) Hook → Module service → @/lib/api/reception → apiRequest → API
                ↘ Placeholder component (foundation)
```

Auth token / org context continues to come from frozen auth store when hooks are implemented.

---

## 7. Explicit non-actions (this foundation)

- No `collectReceptionPayment` UI wiring on M2 pages  
- No print/receipt window logic in the new module  
- No barcode/QR canvas rendering  
- No lab handoff POST from M2 pages  
- No backend / migration / deploy  

---

## 8. Related documents

- `docs/RECEPTION_M2_API.md`
- `docs/RECEPTION_M2_COMPONENT_TREE.md`
- `docs/RELEASE_2_ROADMAP.md`
- `docs/RECEPTION_MILESTONE_1_CONTRACT.md`
- `docs/RELEASE_1_FREEZE.md`
- `docs/AUTH_FREEZE.md`

**STOP** — Architecture foundation complete.
