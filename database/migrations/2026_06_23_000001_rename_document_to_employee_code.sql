-- Migration: Rename document to employee_code in users table
-- Feature: Bug 22 - user_phone_not_exposed
-- Date: 2026-06-23
-- Usage: mysql -u root -p sip_edge < this_file

ALTER TABLE users CHANGE COLUMN document employee_code VARCHAR(32) NOT NULL DEFAULT '';
