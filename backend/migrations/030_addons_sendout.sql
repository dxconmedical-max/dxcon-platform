-- Add-on tests on already collected samples + send-out (outsourced / overseas) tracking — additive, idempotent. PostgreSQL.

-- Per-test flags kept in their own table so the core test catalog is never altered.
CREATE TABLE IF NOT EXISTS test_flags (
    test_catalog_id VARCHAR(36) PRIMARY KEY,
    is_sendout BOOLEAN NOT NULL DEFAULT FALSE,
    sendout_destination VARCHAR(120),
    sendout_eta_days INTEGER,
    addon_window_hours INTEGER,
    updated_by VARCHAR(120),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- A follow-up order created from the sample of an earlier order.
CREATE TABLE IF NOT EXISTS order_addons (
    id VARCHAR(36) PRIMARY KEY,
    original_order_code VARCHAR(50) NOT NULL,
    addon_order_code VARCHAR(50) NOT NULL UNIQUE,
    tests_json TEXT NOT NULL,
    created_by VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_order_addons_original ON order_addons (original_order_code);

-- Reception's notes on send-out tests: when the sample was sent, where, and an updated ETA.
CREATE TABLE IF NOT EXISTS sendout_tracks (
    id VARCHAR(36) PRIMARY KEY,
    order_code VARCHAR(50) NOT NULL,
    test_code VARCHAR(50) NOT NULL,
    sent_at VARCHAR(10),
    destination VARCHAR(120),
    eta_date VARCHAR(10),
    note VARCHAR(300),
    dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    updated_by VARCHAR(120),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_sendout_tracks_order_test UNIQUE (order_code, test_code)
);
