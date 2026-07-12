# Result Ingestion Safety

- Original analyzer values stored in `analyzer_preliminary_results.original_value`.
- Normalized values stored separately; originals are never overwritten.
- Duplicate detection via message hash and result fingerprint.
- Unit mismatch and unmapped tests → quarantine.
- **Analyzer results never auto-release** as final patient results (`auto_released=False`).
