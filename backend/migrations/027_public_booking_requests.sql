-- Public booking requests (website /book form) — additive, idempotent. PostgreSQL.

CREATE TABLE IF NOT EXISTS public_booking_requests (
    id VARCHAR(36) PRIMARY KEY,
    reference VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(120),
    address VARCHAR(300) NOT NULL,
    district VARCHAR(100),
    preferred_date VARCHAR(10),
    preferred_slot VARCHAR(20) DEFAULT 'ANYTIME',
    note VARCHAR(500),
    consent_contact BOOLEAN NOT NULL DEFAULT FALSE,
    consent_version VARCHAR(20),
    consent_at TIMESTAMP,
    ip_address VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'NEW',
    handled_by VARCHAR(120),
    handled_at TIMESTAMP,
    internal_note VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_public_booking_requests_status ON public_booking_requests (status);
CREATE INDEX IF NOT EXISTS ix_public_booking_requests_ip ON public_booking_requests (ip_address);
CREATE INDEX IF NOT EXISTS ix_public_booking_requests_created ON public_booking_requests (created_at);
