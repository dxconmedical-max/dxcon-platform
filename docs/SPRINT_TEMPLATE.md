# Sprint Template

Copy this file to `docs/sprints/SPRINT-NNN-<SHORT-NAME>.md` and fill every section before starting implementation.

---

## Sprint ID

`SPRINT-NNN`

## Title

Short descriptive name

## Status

`PLANNED` | `IN_PROGRESS` | `DONE` | `BLOCKED`

## Dates

- **Start:** YYYY-MM-DD
- **Target end:** YYYY-MM-DD

---

## Goal

One sentence: what this sprint achieves.

## Business Value

Why it matters to clinics, labs, patients, or commercial launch.

## Scope

- Bullet list of in-scope work items

## Out of Scope

- Explicit exclusions to prevent scope creep

## Deliverables

- [ ] Code / config paths
- [ ] Docs updated
- [ ] Verify script PASS
- [ ] Reports in `backend/generated_release/`

## Data Impact

| Area | Change | Migration |
|------|--------|-----------|
| Tables | None / list | `00N_*.sql` |

## API Impact

| Endpoint | Change |
|----------|--------|
| None | — |

## UI Impact

| Route | Change |
|-------|--------|
| None | — |

## Tests

- Unit: `python3 -m unittest discover -s backend/tests -k <pattern>`
- Verify: `python3 backend/scripts/verify_<name>.py`
- UAT (if applicable): role scripts

## Verification

```bash
python3 -m compileall backend/app backend/scripts backend/tests
python3 -m unittest discover -s backend/tests -v
python3 backend/scripts/verify_<name>.py
```

Expected: all PASS.

## Definition of Done

- [ ] All deliverables complete
- [ ] Verification commands PASS
- [ ] Sprint doc status set to `DONE`
- [ ] `PRODUCT_BACKLOG.md` story statuses updated
- [ ] No Critical/High bugs introduced
- [ ] Committed to `main` with message below

## Commit Message

```
<Sprint title> - <short outcome>
```

## Notes

Free-form: blockers, decisions, links to PRs or reports.
