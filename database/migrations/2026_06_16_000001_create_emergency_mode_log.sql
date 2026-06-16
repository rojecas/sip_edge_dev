-- Migration: Create emergency_mode_log table
-- Feature: 9 - emergency_mode
-- Date: 2026-06-16

CREATE TABLE IF NOT EXISTS emergency_mode_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    request_id BIGINT UNSIGNED NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    analyst_id BIGINT UNSIGNED NULL,
    supervisor_id BIGINT UNSIGNED NULL,
    motivo TEXT NULL,
    started_at DATETIME NULL,
    duration_seconds INT UNSIGNED NULL,
    expires_at DATETIME NULL,
    cmd_source VARCHAR(10) NOT NULL,
    cmd_raw VARCHAR(255) NULL,
    sender_phone VARCHAR(32) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_eml_status_expires (status, expires_at),
    INDEX idx_eml_analyst (analyst_id),
    INDEX idx_eml_supervisor (supervisor_id),
    INDEX idx_eml_request (request_id),
    CONSTRAINT fk_emergency_request FOREIGN KEY (request_id) REFERENCES emergency_mode_log(id),
    CONSTRAINT fk_emergency_analyst FOREIGN KEY (analyst_id) REFERENCES users(id),
    CONSTRAINT fk_emergency_supervisor FOREIGN KEY (supervisor_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add phone column to users if not exists (needed for SMS-based emergency mode)
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(32) NULL DEFAULT NULL;
