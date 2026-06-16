-- Migration: Create anomaly_log table
-- Feature: 8 - ai_agent
-- Date: 2026-06-16

CREATE TABLE anomaly_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    record_id BIGINT UNSIGNED NOT NULL,
    layer VARCHAR(20) NOT NULL,
    z_score DECIMAL(10,4) NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    threshold DECIMAL(10,4) NOT NULL,
    llm_report TEXT NULL,
    sent_sms BOOLEAN NOT NULL DEFAULT FALSE,
    anomaly_context JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_al_record (record_id),
    INDEX idx_al_layer (layer),
    INDEX idx_al_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
