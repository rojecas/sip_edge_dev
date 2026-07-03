-- Migration: Create sms_conversations table
-- Feature: 27 - sms_persistence
-- Date: 2026-07-02
-- Covers: R1

CREATE TABLE IF NOT EXISTS sms_conversations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    peer_number VARCHAR(20) NOT NULL,
    workflow_type ENUM('emergency','password_reset','ai_query','unknown') NOT NULL,
    status ENUM('active','completed','expired','cancelled','failed') NOT NULL DEFAULT 'active',
    started_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    last_activity DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    expires_at DATETIME(3) NULL,
    metadata JSON NULL,
    INDEX idx_peer_status (peer_number, status),
    INDEX idx_expires (status, expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
