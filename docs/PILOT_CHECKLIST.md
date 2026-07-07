# Pilot Checklist (16 Manual Items)

This checklist is **manual** and must be verified before customer-facing pilot go-live.

Internal pilot can proceed with some items in **WARNING** state with mitigation.

## Items

1. **domain** — Domain configured
2. **ssl** — TLS/SSL certificate active
3. **smtp** — SMTP configured (or `EMAIL_DRY_RUN=true` for internal pilot)
4. **pilot_users** — Pilot users provisioned (SUPER_ADMIN, RECEPTION, LAB, DOCTOR, PATIENT)
5. **organization_setup** — Organization created/configured
6. **master_data** — Master data seeded/imported
7. **price_list** — Price list verified
8. **clinic** — Clinic partner configured
9. **lab** — Laboratory partner configured
10. **doctors** — Doctor users created and assigned
11. **collectors** — Collector users created
12. **test_patient** — Test patient created
13. **test_order** — Test order created
14. **test_report** — Test report approved + released
15. **backup** — Backup schedule enabled + restore rehearsal completed
16. **support_contact** — Support contact and escalation path confirmed

## Generated Status

Run:

```bash
python backend/scripts/verify_pilot_blockers.py
```

Outputs:
- `backend/generated_release/PILOT_CHECKLIST_STATUS.json`

