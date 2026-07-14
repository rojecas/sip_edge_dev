ALTER TABLE sms_conversations 
MODIFY COLUMN status ENUM('active','completed','expired','cancelled','failed','archived') NOT NULL DEFAULT 'active';
