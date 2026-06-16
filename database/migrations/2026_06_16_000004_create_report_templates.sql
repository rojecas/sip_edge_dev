-- Migration: Create report_templates table
-- Feature: 8 - ai_agent
-- Date: 2026-06-16

CREATE TABLE report_templates (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    schedule JSON NOT NULL,
    recipients JSON NOT NULL,
    metrics JSON NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rt_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
