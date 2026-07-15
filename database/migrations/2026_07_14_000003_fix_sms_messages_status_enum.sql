-- Migration: Add sending to sms_messages.status ENUM
-- Fix: sms_service.update_message_status() uses sending but it was missing from ENUM
-- This caused (1265, Data truncated for column status) and duplicate SMS via send queue
-- Date: 2026-07-14

ALTER TABLE sms_messages MODIFY COLUMN status ENUM('pending','sending','sent','failed','timeout','delivered','received') NOT NULL DEFAULT 'pending';
