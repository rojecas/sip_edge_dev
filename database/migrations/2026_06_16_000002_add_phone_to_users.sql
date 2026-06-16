-- Migration: Add phone column to users table
-- Requires: superuser privilege on MariaDB
-- Usage: mysql -u root -p sip_edge < this_file

ALTER TABLE users
  ADD COLUMN phone VARCHAR(32) DEFAULT NULL
  AFTER is_active;
