# Release 2 Go-Live Checklist — Reception M2 RC (`2.0.0-rc1`)

**Auth:** FROZEN — do not change web auth runtime.  
**Report:** `docs/RELEASE_2_RC_REPORT.md`  
**Deploy:** `docs/RELEASE_2_DEPLOYMENT_CHECKLIST.md`

---

## Pre-cutover

- [ ] RM approved RC report gates (typecheck / M2 lint / auth / build / engine tests)
- [ ] Reception M2 changes committed or merged to `release/v2.0.0` (named files; release isolation)
- [ ] Migrations `017`–`019` reviewed for target Postgres
- [ ] Staging API + web smoke green
- [ ] Auth freeze guard still PASS on promote branch
- [ ] Rollback owner and prior deploy IDs recorded

---

## Production URLs

| Surface | URL |
|---------|-----|
| Web | https://dxcon.com.vn |
| API | https://api.dxcon.com.vn |
| Health | `GET /api/v1/system/health` |
| Ready | `GET /api/v1/system/ready` |

---

## Functional smoke (synthetic data)

### Payment
- [ ] Open unpaid order → collect cash (full)
- [ ] Collect partial payment (if enabled) → outstanding updates
- [ ] Payment history lists rows

### Receipt
- [ ] Receipt auto-issued after payment
- [ ] Preview standard + thermal
- [ ] Print / reprint increments print count
- [ ] PDF downloadable
- [ ] Cancel blocks further print

### Barcode
- [ ] Paid order loads order / sample labels
- [ ] Collection label after collection job
- [ ] Browser print preview opens
- [ ] Thermal format shows 80mm / thermal text

### QR
- [ ] Payment + VNPay QR render for payable order
- [ ] Static patient/order QR valid
- [ ] Dynamic QR verifies; tampered payload fails
- [ ] Sample QR after paid; tracking QR present

### Lab queue
- [ ] Enqueue paid+barcoded order → **waiting**
- [ ] Advance waiting → processing → completed → verified
- [ ] Priority change before verified
- [ ] Live refresh updates version / board

### Sample queue
- [ ] Enqueue with collection → **collected**
- [ ] Advance through transport → received → sorting → laboratory → completed
- [ ] Track + history show audit events
- [ ] Location update recorded

### Regression
- [ ] Reception M1 create-order path still works
- [ ] Login / session restore (auth freeze) still works
- [ ] Lab handoff still idempotent

---

## Post go-live

- [ ] Error rate / 5xx watch 30–60 minutes
- [ ] Confirm no auth-freeze file diffs in deploy artifact
- [ ] File RC smoke evidence in release folder / ticket
- [ ] Tag `v2.0.0-rc1` only if process requires (do not move `v1.0.0`)

---

## Abort criteria

Stop promote / roll back if:

- Auth freeze guard fails
- Payment collect or receipt issue broken in production
- Ready probe fails after migration
- Unexpected schema migrate error on `017`–`019`
