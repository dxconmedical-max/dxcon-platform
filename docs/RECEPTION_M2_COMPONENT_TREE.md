# Reception Milestone 2 — Component Tree

**Status:** Architecture foundation (placeholders only)  
**Business logic:** Not implemented  

---

## 1. Route tree

```text
/app/reception                          RoleDashboardHome (+ M2 hub link)
└── /m2                                 ReceptionM2HubPage
    ├── /payment                        ReceptionM2PaymentPage
    ├── /receipt                        ReceptionM2ReceiptPage
    ├── /barcode                        ReceptionM2BarcodePage
    ├── /qr                             ReceptionM2QrPage
    ├── /lab-queue                      ReceptionM2LabQueuePage
    └── /sample-queue                   ReceptionM2SampleQueuePage
```

Legacy R1 (unchanged ownership for this foundation):

```text
/app/reception/workflow                 Milestone1Steps + OrderSteps (interim M2 UI)
/app/reception/search | register        M1 patient surfaces
```

---

## 2. Module component tree

```text
modules/reception-m2/
├── shared/
│   └── ReceptionM2Placeholder
├── payment/
│   ├── components/PaymentPanelPlaceholder
│   └── hooks/useReceptionPaymentArchitecture   (stub)
├── receipt/
│   ├── components/ReceiptPanelPlaceholder
│   └── hooks/useReceptionReceiptArchitecture   (stub)
├── barcode/
│   ├── components/BarcodePanelPlaceholder
│   └── hooks/useReceptionBarcodeArchitecture   (stub)
├── qr/
│   ├── components/QrPanelPlaceholder
│   └── hooks/useReceptionQrArchitecture        (stub)
├── lab-queue/
│   ├── components/LabQueuePanelPlaceholder
│   └── hooks/useReceptionLabQueueArchitecture  (stub)
└── sample-queue/
    ├── components/SampleQueuePanelPlaceholder
    └── hooks/useReceptionSampleQueueArchitecture (stub)
```

---

## 3. Page composition (foundation)

```text
AppShell
└── ReceptionM2Placeholder
└── *PanelPlaceholder
```

Future kickoff (not now):

```text
AppShell
└── DomainPage
    └── useReception*(token, orderRef)
        └── DomainPanel (real UI)
            └── service → @/lib/api/reception
```

---

## 4. Target extraction map (from OrderSteps)

When a milestone is kicked off, extract **call sites** — do not copy mappers:

| UI concern in OrderSteps | Target module |
|--------------------------|---------------|
| Collect payment / outstanding | `payment` |
| Printable receipt HTML | `receipt` |
| Barcode / sample labels | `barcode` |
| Patient QR display | `qr` |
| Lab handoff confirm | `lab-queue` |
| Collection queue hints | `sample-queue` |

---

## 5. Shared platform components (reuse)

| Component | Use |
|-----------|-----|
| `AppShell` | All M2 pages |
| `RoleDashboardHome` | Reception home |
| `@/components/ui/Button|Input|Card` | Future panels |
| Frozen auth hooks | Token / org when wiring hooks |

---

## 6. File index (created this foundation)

### Pages

- `apps/web/src/app/app/reception/m2/page.tsx`
- `apps/web/src/app/app/reception/m2/payment/page.tsx`
- `apps/web/src/app/app/reception/m2/receipt/page.tsx`
- `apps/web/src/app/app/reception/m2/barcode/page.tsx`
- `apps/web/src/app/app/reception/m2/qr/page.tsx`
- `apps/web/src/app/app/reception/m2/lab-queue/page.tsx`
- `apps/web/src/app/app/reception/m2/sample-queue/page.tsx`

### Module

- `apps/web/src/modules/reception-m2/**`

### Docs

- `docs/RECEPTION_M2_ARCHITECTURE.md`
- `docs/RECEPTION_M2_API.md`
- `docs/RECEPTION_M2_COMPONENT_TREE.md`

---

**STOP** — Component tree documented; no further implementation.
