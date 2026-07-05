"""Business engine additive schema — Sprint 1."""

-- Run against PostgreSQL (additive, idempotent)

CREATE TABLE IF NOT EXISTS biz_orders (
    id VARCHAR(36) PRIMARY KEY,
    order_code VARCHAR(50) UNIQUE NOT NULL,
    patient_code VARCHAR(50) NOT NULL REFERENCES patients(patient_code),
    patient_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    subtotal DOUBLE PRECISION DEFAULT 0,
    discount DOUBLE PRECISION DEFAULT 0,
    total_amount DOUBLE PRECISION DEFAULT 0,
    note TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS biz_order_items (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL REFERENCES biz_orders(id),
    test_catalog_id VARCHAR(36),
    test_code VARCHAR(50) NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    unit_price DOUBLE PRECISION DEFAULT 0,
    quantity INTEGER DEFAULT 1,
    line_total DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS biz_invoices (
    id VARCHAR(36) PRIMARY KEY,
    invoice_no VARCHAR(50) UNIQUE NOT NULL,
    order_id VARCHAR(36) NOT NULL REFERENCES biz_orders(id),
    amount DOUBLE PRECISION DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'unpaid',
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS biz_payments (
    id VARCHAR(36) PRIMARY KEY,
    invoice_id VARCHAR(36) NOT NULL REFERENCES biz_invoices(id),
    order_id VARCHAR(36) NOT NULL REFERENCES biz_orders(id),
    payment_method VARCHAR(50) NOT NULL,
    receipt_number VARCHAR(50) UNIQUE NOT NULL,
    amount DOUBLE PRECISION DEFAULT 0,
    paid_at TIMESTAMP NOT NULL,
    created_by VARCHAR(255),
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS biz_collections (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL REFERENCES biz_orders(id),
    collector_name VARCHAR(255),
    pickup_address TEXT,
    scheduled_at TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'assigned',
    sample_code VARCHAR(50) UNIQUE,
    barcode_value VARCHAR(100) UNIQUE,
    accession_number VARCHAR(50) UNIQUE,
    received_by VARCHAR(255),
    received_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS biz_results (
    id VARCHAR(36) PRIMARY KEY,
    result_code VARCHAR(50) UNIQUE NOT NULL,
    order_id VARCHAR(36) NOT NULL UNIQUE REFERENCES biz_orders(id),
    status VARCHAR(50) NOT NULL DEFAULT 'testing',
    doctor_note TEXT,
    approved_at TIMESTAMP,
    approved_by VARCHAR(255),
    released_at TIMESTAMP,
    html_content TEXT,
    patient_visible BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS biz_result_items (
    id VARCHAR(36) PRIMARY KEY,
    result_id VARCHAR(36) NOT NULL REFERENCES biz_results(id),
    test_code VARCHAR(50),
    test_name VARCHAR(255) NOT NULL,
    result_value VARCHAR(255),
    unit VARCHAR(50),
    reference_range VARCHAR(255),
    flag VARCHAR(20) DEFAULT 'NORMAL',
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS biz_workflow_audits (
    id VARCHAR(36) PRIMARY KEY,
    actor VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    note TEXT,
    created_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_biz_orders_patient_code ON biz_orders(patient_code);
CREATE INDEX IF NOT EXISTS idx_biz_orders_status ON biz_orders(status);
CREATE INDEX IF NOT EXISTS idx_biz_workflow_audits_entity ON biz_workflow_audits(entity_type, entity_id);
