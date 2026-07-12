-- Release 8.0 Sprint 7 — Patient Commerce (additive)

ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS featured BOOLEAN DEFAULT FALSE;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS category VARCHAR(50);

ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS turnaround_hours INTEGER;
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS featured BOOLEAN DEFAULT FALSE;
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS category VARCHAR(50);

CREATE TABLE IF NOT EXISTS mp_slot_holds (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    provider_id VARCHAR(36) NOT NULL REFERENCES mp_providers(id),
    availability_id VARCHAR(36) REFERENCES mp_availability(id),
    patient_user_id VARCHAR(36),
    hold_token VARCHAR(64) NOT NULL UNIQUE,
    slot_start TIMESTAMP NOT NULL,
    slot_end TIMESTAMP NOT NULL,
    status VARCHAR(30) DEFAULT 'HELD',
    expires_at TIMESTAMP NOT NULL,
    booking_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mp_slot_holds_token ON mp_slot_holds(hold_token);
CREATE INDEX IF NOT EXISTS idx_mp_slot_holds_expires ON mp_slot_holds(expires_at);

CREATE TABLE IF NOT EXISTS mp_patient_addresses (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    patient_user_id VARCHAR(36) NOT NULL,
    label VARCHAR(50) DEFAULT 'Home',
    address_line TEXT NOT NULL,
    building VARCHAR(100),
    apartment VARCHAR(50),
    city VARCHAR(100),
    district VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    contact_instructions TEXT,
    collector_notes TEXT,
    preferred_window_start VARCHAR(10),
    preferred_window_end VARCHAR(10),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mp_patient_addresses_user ON mp_patient_addresses(patient_user_id);

CREATE TABLE IF NOT EXISTS mp_holidays (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    provider_id VARCHAR(36) REFERENCES mp_providers(id),
    holiday_date DATE NOT NULL,
    name VARCHAR(255),
    is_closed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_mp_holiday_org_provider_date
    ON mp_holidays(organization_id, COALESCE(provider_id, ''), holiday_date);

CREATE TABLE IF NOT EXISTS mp_package_items (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    package_listing_id VARCHAR(36) NOT NULL REFERENCES mp_listings(id),
    service_id VARCHAR(36) NOT NULL REFERENCES mp_services(id),
    quantity INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0
);
