-- Migration: Create sms_messages table
-- Feature: 27 - sms_persistence
-- Date: 2026-07-02
-- Covers: R2

CREATE TABLE IF NOT EXISTS sms_messages (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT UNSIGNED NOT NULL,
    direction ENUM('sent','received') NOT NULL,
    peer_number VARCHAR(20) NOT NULL,
    body TEXT NOT NULL,
    handler VARCHAR(32) NULL,
    status ENUM('pending','sending','sent','failed','timeout','delivered','received') NOT NULL DEFAULT 'pending',
    error_message TEXT NULL,
    modem_sms_id INT NULL,
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    INDEX idx_conv_id (conversation_id),
    INDEX idx_direction_status (direction, status),
    CONSTRAINT fk_sms_msg_conversation FOREIGN KEY (conversation_id) REFERENCES sms_conversations(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
