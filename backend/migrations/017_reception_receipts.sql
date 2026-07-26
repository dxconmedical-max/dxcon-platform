"""Reception receipts — additive schema for BizReceipt documents."""

-- Run against PostgreSQL (additive, idempotent)

CREATE TABLE IF NOT EXISTS biz_receipts (
    id VARCHAR(36) PRIMARY KEY,
    receipt_code VARCHAR(50) UNIQUE NOT NULL,
    payment_id VARCHAR(36) NOT NULL UNIQUE REFERENCES biz_payments(id),
    order_id VARCHAR(36) NOT NULL REFERENCES biz_orders(id),
    invoice_id VARCHAR(36) REFERENCES biz_invoices(id),
    status VARCHAR(30) NOT NULL DEFAULT 'issued',
    print_count INTEGER DEFAULT 0,
    preferred_format VARCHAR(30) DEFAULT 'standard',
    html_snapshot TEXT,
    thermal_payload TEXT,
    pdf_path VARCHAR(500),
    issued_at TIMESTAMP NOT NULL,
    issued_by VARCHAR(255),
    last_printed_at TIMESTAMP,
    last_printed_by VARCHAR(255),
    cancelled_at TIMESTAMP,
    cancelled_by VARCHAR(255),
    cancel_reason TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_biz_receipts_order_id ON biz_receipts(order_id);
CREATE INDEX IF NOT EXISTS ix_biz_receipts_status ON biz_receipts(status);
