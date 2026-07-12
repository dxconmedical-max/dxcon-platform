-- Release 7.0 Sprint 4 — IoT Logistics and Cold Chain (additive, non-destructive)

-- Extend existing IoT device registry with platform metadata
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS vendor VARCHAR(100);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS model VARCHAR(100);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS firmware_version VARCHAR(50);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS connectivity_type VARCHAR(30);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS battery_level INTEGER;
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS assigned_vehicle_id VARCHAR(36);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS assigned_container_id VARCHAR(36);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS calibration_due_at TIMESTAMP;
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS certificate_reference VARCHAR(255);

CREATE TABLE IF NOT EXISTS iot_device_credentials (
    id VARCHAR(36) PRIMARY KEY,
    device_id VARCHAR(36) NOT NULL REFERENCES iot_devices(id),
    credential_hash VARCHAR(255) NOT NULL,
    credential_ref VARCHAR(255),
    rotated_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_iot_device_credentials_device ON iot_device_credentials(device_id);

CREATE TABLE IF NOT EXISTS iot_device_assignments (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    device_id VARCHAR(36) NOT NULL REFERENCES iot_devices(id),
    vehicle_id VARCHAR(36),
    container_id VARCHAR(36),
    trip_id VARCHAR(36),
    assigned_by VARCHAR(255),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'ACTIVE'
);

CREATE INDEX IF NOT EXISTS idx_iot_assignments_org ON iot_device_assignments(organization_id);
CREATE INDEX IF NOT EXISTS idx_iot_assignments_device ON iot_device_assignments(device_id);

CREATE TABLE IF NOT EXISTS iot_canonical_readings (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    device_id VARCHAR(36) NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE,
    sequence_number BIGINT,
    recorded_at TIMESTAMP NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature_c DOUBLE PRECISION,
    humidity_percent DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    speed_kph DOUBLE PRECISION,
    heading DOUBLE PRECISION,
    altitude_m DOUBLE PRECISION,
    battery_percent DOUBLE PRECISION,
    signal_strength DOUBLE PRECISION,
    door_open BOOLEAN,
    trip_id VARCHAR(36),
    transport_container_id VARCHAR(36),
    metadata_json TEXT,
    simulated BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_iot_readings_device ON iot_canonical_readings(device_id);
CREATE INDEX IF NOT EXISTS idx_iot_readings_org ON iot_canonical_readings(organization_id);
CREATE INDEX IF NOT EXISTS idx_iot_readings_recorded ON iot_canonical_readings(recorded_at);

CREATE TABLE IF NOT EXISTS iot_threshold_policies (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    policy_code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    specimen_type VARCHAR(50),
    test_requirement VARCHAR(100),
    container_type VARCHAR(50),
    route_id VARCHAR(36),
    min_temperature_c DOUBLE PRECISION,
    max_temperature_c DOUBLE PRECISION,
    min_humidity_percent DOUBLE PRECISION,
    max_humidity_percent DOUBLE PRECISION,
    grace_duration_seconds INTEGER DEFAULT 300,
    sampling_interval_seconds INTEGER DEFAULT 60,
    max_transport_duration_seconds INTEGER,
    max_door_open_seconds INTEGER,
    requires_calibration BOOLEAN DEFAULT TRUE,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_iot_policies_org ON iot_threshold_policies(organization_id);

CREATE TABLE IF NOT EXISTS iot_cold_chain_excursions (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    device_id VARCHAR(36),
    trip_id VARCHAR(36),
    transport_container_id VARCHAR(36),
    policy_id VARCHAR(36) REFERENCES iot_threshold_policies(id),
    excursion_type VARCHAR(50) NOT NULL,
    state VARCHAR(50) DEFAULT 'DETECTED',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP,
    override_reason TEXT,
    specimen_hold BOOLEAN DEFAULT FALSE,
    correlation_id VARCHAR(64),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_iot_excursions_org ON iot_cold_chain_excursions(organization_id);
CREATE INDEX IF NOT EXISTS idx_iot_excursions_state ON iot_cold_chain_excursions(state);

CREATE TABLE IF NOT EXISTS iot_platform_alerts (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'WARNING',
    status VARCHAR(30) DEFAULT 'OPEN',
    device_id VARCHAR(36),
    trip_id VARCHAR(36),
    dedupe_key VARCHAR(128),
    message TEXT,
    channel VARCHAR(30) DEFAULT 'in_app',
    correlation_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_iot_alerts_dedupe ON iot_platform_alerts(dedupe_key) WHERE dedupe_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS iot_telemetry_dead_letters (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36),
    device_id VARCHAR(36),
    adapter_type VARCHAR(30),
    error_code VARCHAR(50),
    error_message TEXT,
    payload_ref VARCHAR(255),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS logistics_transport_trips (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    trip_code VARCHAR(50) NOT NULL UNIQUE,
    route_plan_id VARCHAR(36),
    driver_profile_id VARCHAR(36),
    vehicle_id VARCHAR(36),
    container_id VARCHAR(36),
    status VARCHAR(30) DEFAULT 'PLANNED',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    latest_latitude DOUBLE PRECISION,
    latest_longitude DOUBLE PRECISION,
    latest_location_at TIMESTAMP,
    distance_km DOUBLE PRECISION DEFAULT 0,
    eta_provider VARCHAR(30) DEFAULT 'test',
    correlation_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logistics_trips_org ON logistics_transport_trips(organization_id);
CREATE INDEX IF NOT EXISTS idx_logistics_trips_status ON logistics_transport_trips(status);
