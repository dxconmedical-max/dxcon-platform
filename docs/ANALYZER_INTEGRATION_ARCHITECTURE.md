# Analyzer Integration Architecture

Release 7.0 Sprint 5 — vendor-neutral instrument integration layer.

## Components

- **Analyzer registry** — extends `lab_analyzers` with protocol, connection, and organization scope.
- **Adapter framework** — `SimulatorAdapter`, `ASTMAdapter` (foundation); vendor parsing isolated in adapters.
- **Message inbox** — `integration_messages` with hash deduplication and redacted summaries.
- **Test code mapping** — approved mappings with version and effective date.
- **Result ingestion** — preliminary results only; `auto_released=False` always unless explicit approved workflow exists.
- **Quarantine** — unmapped, duplicate, unit mismatch, unknown barcode.

## Data flow

```
Instrument → Adapter → Message → Validate → Map → Preliminary Result → Technician Review
                      ↘ Quarantine (on failure)
```

## Not implemented (hardware)

ASTM/HL7 TCP, serial gateways, and vendor-specific protocols require on-prem gateway deployment.
