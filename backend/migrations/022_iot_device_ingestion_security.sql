-- IoT device ingestion security (P0-D) — additive, idempotent.
-- PostgreSQL only.
--
-- Adds:
-- - iot_devices.ingest_secret_hash / ingest_secret_set_at
-- - iot_device_ingest_events (DB-backed idempotency + anti-replay)

-- ===== iot_devices (credential fields) =====
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS ingest_secret_hash VARCHAR(255);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS ingest_secret_set_at TIMESTAMP WITHOUT TIME ZONE;

-- ===== iot_device_ingest_events =====
CREATE TABLE IF NOT EXISTS iot_device_ingest_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id),
    device_id VARCHAR(36) NOT NULL REFERENCES iot_devices(id),
    event_id VARCHAR(128),
    nonce VARCHAR(128),
    payload_hash VARCHAR(64),
    processed BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_iot_device_ingest_events_device_id ON iot_device_ingest_events (device_id);
CREATE INDEX IF NOT EXISTS ix_iot_device_ingest_events_nonce ON iot_device_ingest_events (nonce);

-- Idempotency is scoped to authenticated device identity.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_iot_device_event_id'
  ) THEN
    ALTER TABLE iot_device_ingest_events
      ADD CONSTRAINT uq_iot_device_event_id UNIQUE (device_id, event_id);
  END IF;
END $$;

-- Nonce anti-replay is also scoped to authenticated device identity.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_iot_device_nonce'
  ) THEN
    ALTER TABLE iot_device_ingest_events
      ADD CONSTRAINT uq_iot_device_nonce UNIQUE (device_id, nonce);
  END IF;
END $$;
