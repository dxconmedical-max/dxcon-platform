# Result Report Format

DxCon clinical report PDF/HTML (reporting engine).

## Sections

- DxCon branding and laboratory details
- Patient identifiers (authorized views only)
- Order and specimen metadata
- Results table: analyte, value, unit, reference range, abnormal indicators
- Clinical interpretation (doctor note)
- Approver/signatory and approval timestamp
- Report version and amendment notice
- Verification code/QR (opaque token reference)
- Disclaimer and page numbering

## Immutability

Released PDF hash stored on `clinical_reports.report_hash`. Amendments generate new version.
