-- Staff profiles for report approvers (name, job title, license) — additive, idempotent.
-- PostgreSQL only.

CREATE TABLE IF NOT EXISTS staff_profiles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id),
    user_id VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id),
    full_name VARCHAR(255) NOT NULL,
    job_title VARCHAR(255),
    license_number VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_staff_profiles_user_id ON staff_profiles (user_id);
