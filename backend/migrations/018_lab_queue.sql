"""Laboratory intake queue — additive schema for BizLabQueueItem."""

-- Run against PostgreSQL (additive, idempotent)

CREATE TABLE IF NOT EXISTS biz_lab_queue_items (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL UNIQUE REFERENCES biz_orders(id),
    order_code VARCHAR(50) NOT NULL UNIQUE,
    stage VARCHAR(30) NOT NULL DEFAULT 'waiting',
    priority VARCHAR(20) NOT NULL DEFAULT 'routine',
    queue_reference VARCHAR(100),
    laboratory_name VARCHAR(255),
    notes TEXT,
    entered_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    verified_at TIMESTAMP,
    verified_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_biz_lab_queue_items_order_code ON biz_lab_queue_items(order_code);
CREATE INDEX IF NOT EXISTS ix_biz_lab_queue_items_stage ON biz_lab_queue_items(stage);
CREATE INDEX IF NOT EXISTS ix_biz_lab_queue_items_priority ON biz_lab_queue_items(priority);
