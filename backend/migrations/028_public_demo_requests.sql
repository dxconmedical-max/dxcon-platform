-- Public "Book a demo" requests (landing page contact form) — additive, idempotent. PostgreSQL.

CREATE TABLE IF NOT EXISTS public_demo_requests (
    id VARCHAR(36) PRIMARY KEY,
    reference VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    organization VARCHAR(160),
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    message VARCHAR(1000),
    lang VARCHAR(5) DEFAULT 'vi',
    consent_contact BOOLEAN NOT NULL DEFAULT FALSE,
    ip_address VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'NEW',
    handled_by VARCHAR(120),
    handled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_public_demo_requests_status ON public_demo_requests (status);
CREATE INDEX IF NOT EXISTS ix_public_demo_requests_ip ON public_demo_requests (ip_address);
CREATE INDEX IF NOT EXISTS ix_public_demo_requests_created ON public_demo_requests (created_at);
