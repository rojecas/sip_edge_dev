-- Migration: Add password reset fields to users table
-- Feature: 12 - password_reset_sms
-- Date: 2026-06-16

ALTER TABLE users
  ADD COLUMN force_password_change BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN reset_pin VARCHAR(128) DEFAULT NULL,
  ADD COLUMN reset_pin_expires_at TIMESTAMP(0) DEFAULT NULL;
