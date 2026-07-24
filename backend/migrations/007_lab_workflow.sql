-- Laboratory Workflow — additive processing fields on accession records

ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS processing_status VARCHAR(40) DEFAULT 'accessioned';
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS bench_id VARCHAR(100);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS instrument_id VARCHAR(100);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS technician VARCHAR(255);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS identifiers_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP;
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS rejection_reason VARCHAR(80);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP;
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP;
