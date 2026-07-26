"""Sample logistics queue — additive schema for BizSampleQueueItem + events."""

-- Run against PostgreSQL (additive, idempotent)

CREATE TABLE IF NOT EXISTS biz_sample_queue_items (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL UNIQUE REFERENCES biz_orders(id),
    order_code VARCHAR(50) NOT NULL UNIQUE,
    collection_id VARCHAR(36) REFERENCES biz_collections(id),
    sample_code VARCHAR(50),
    stage VARCHAR(30) NOT NULL DEFAULT 'collected',
    collector_name VARCHAR(255),
    location VARCHAR(255),
    notes TEXT,
    collected_at TIMESTAMP,
    transport_at TIMESTAMP,
    received_at TIMESTAMP,
    sorting_at TIMESTAMP,
    laboratory_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_by VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_items_order_code ON biz_sample_queue_items(order_code);
CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_items_stage ON biz_sample_queue_items(stage);
CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_items_sample_code ON biz_sample_queue_items(sample_code);

CREATE TABLE IF NOT EXISTS biz_sample_queue_events (
    id VARCHAR(36) PRIMARY KEY,
    queue_item_id VARCHAR(36) NOT NULL REFERENCES biz_sample_queue_items(id),
    order_code VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    from_stage VARCHAR(30),
    to_stage VARCHAR(30),
    actor VARCHAR(255),
    location VARCHAR(255),
    note TEXT,
    created_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_events_queue_item_id ON biz_sample_queue_events(queue_item_id);
CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_events_order_code ON biz_sample_queue_events(order_code);
CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_events_created_at ON biz_sample_queue_events(created_at);
