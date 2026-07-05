-- Sprint 006 — Reception Operational Workspace (additive, PostgreSQL)

ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(30) DEFAULT 'WAITING';

CREATE INDEX IF NOT EXISTS idx_reception_queue_workflow ON reception_queue_entries (workflow_status);
CREATE INDEX IF NOT EXISTS idx_reception_queue_order ON reception_queue_entries (order_id);
