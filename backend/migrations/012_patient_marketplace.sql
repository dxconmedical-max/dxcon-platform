-- Epic 5 Patient Marketplace (non-destructive)

CREATE TABLE IF NOT EXISTS mp_providers (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    partner_id VARCHAR(36),
    provider_code VARCHAR(80) UNIQUE NOT NULL,
    provider_name VARCHAR(255) NOT NULL,
    provider_type VARCHAR(50) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    description TEXT,
    address TEXT,
    latitude FLOAT,
    longitude FLOAT,
    working_hours_json TEXT DEFAULT '{}',
    service_areas_json TEXT DEFAULT '[]',
    certifications_json TEXT DEFAULT '[]',
    specialties_json TEXT DEFAULT '[]',
    rating_avg FLOAT DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    turnaround_hours INTEGER,
    collection_methods_json TEXT DEFAULT '[]',
    payment_methods_json TEXT DEFAULT '[]',
    cancellation_policy TEXT,
    public_status VARCHAR(30) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mp_providers_org ON mp_providers(organization_id);

CREATE TABLE IF NOT EXISTS mp_services (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    service_code VARCHAR(80) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    description TEXT,
    preparation_instructions TEXT,
    sample_requirements TEXT,
    duration_minutes INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, service_code)
);

CREATE TABLE IF NOT EXISTS mp_listings (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    provider_id VARCHAR(36) NOT NULL REFERENCES mp_providers(id),
    service_id VARCHAR(36) NOT NULL REFERENCES mp_services(id),
    listing_code VARCHAR(80) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    base_price NUMERIC(12,2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'VND',
    home_collection_available BOOLEAN DEFAULT FALSE,
    service_radius_km FLOAT,
    price_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    partner_consent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mp_listings_org ON mp_listings(organization_id);
CREATE INDEX IF NOT EXISTS idx_mp_listings_status ON mp_listings(status);

CREATE TABLE IF NOT EXISTS mp_promotions (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    promotion_code VARCHAR(50) NOT NULL,
    promotion_type VARCHAR(30) DEFAULT 'PLATFORM',
    discount_percent NUMERIC(5,2),
    discount_amount NUMERIC(12,2),
    min_order_amount NUMERIC(12,2) DEFAULT 0,
    usage_limit INTEGER,
    per_patient_limit INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    starts_at TIMESTAMP,
    ends_at TIMESTAMP,
    stacking_policy VARCHAR(20) DEFAULT 'NONE',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, promotion_code)
);

CREATE TABLE IF NOT EXISTS mp_pricing_snapshots (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    listing_id VARCHAR(36) REFERENCES mp_listings(id),
    components_json TEXT NOT NULL,
    rule_versions_json TEXT DEFAULT '{}',
    total_amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'VND',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mp_bookings (
    id VARCHAR(36) PRIMARY KEY,
    booking_code VARCHAR(50) UNIQUE NOT NULL,
    patient_id VARCHAR(36),
    patient_user_id VARCHAR(36),
    organization_id VARCHAR(36) NOT NULL,
    provider_id VARCHAR(36) NOT NULL REFERENCES mp_providers(id),
    listing_id VARCHAR(36) NOT NULL REFERENCES mp_listings(id),
    service_type VARCHAR(50),
    appointment_type VARCHAR(50),
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    pickup_address TEXT,
    clinic_address TEXT,
    contact_phone VARCHAR(30),
    preparation_acknowledged BOOLEAN DEFAULT FALSE,
    consent_status VARCHAR(30) DEFAULT 'PENDING',
    pricing_snapshot_id VARCHAR(36) REFERENCES mp_pricing_snapshots(id),
    booking_status VARCHAR(30) DEFAULT 'DRAFT',
    order_id VARCHAR(36),
    collection_job_id VARCHAR(36),
    idempotency_key VARCHAR(80) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mp_bookings_org ON mp_bookings(organization_id);

CREATE TABLE IF NOT EXISTS mp_availability (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    provider_id VARCHAR(36) NOT NULL REFERENCES mp_providers(id),
    slot_start TIMESTAMP NOT NULL,
    slot_end TIMESTAMP NOT NULL,
    capacity INTEGER DEFAULT 1,
    reserved INTEGER DEFAULT 0,
    is_blocked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, slot_start)
);

CREATE TABLE IF NOT EXISTS mp_payments (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    booking_id VARCHAR(36) NOT NULL REFERENCES mp_bookings(id),
    payment_reference VARCHAR(80) UNIQUE NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'VND',
    payment_method VARCHAR(30) DEFAULT 'QR_BANK_TRANSFER',
    status VARCHAR(30) DEFAULT 'CREATED',
    qr_payload TEXT,
    provider_code VARCHAR(50),
    expires_at TIMESTAMP,
    webhook_idempotency_key VARCHAR(80) UNIQUE,
    reconciliation_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mp_payments_org ON mp_payments(organization_id);

CREATE TABLE IF NOT EXISTS mp_reviews (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    booking_id VARCHAR(36) UNIQUE REFERENCES mp_bookings(id),
    provider_id VARCHAR(36) REFERENCES mp_providers(id),
    patient_user_id VARCHAR(36),
    rating INTEGER NOT NULL,
    review_text TEXT,
    moderation_status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mp_audit_events (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    actor_id VARCHAR(36),
    resource_type VARCHAR(50),
    resource_id VARCHAR(36),
    outcome VARCHAR(30),
    details_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mp_audit_org ON mp_audit_events(organization_id);
