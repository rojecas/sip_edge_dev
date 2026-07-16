ALTER TABLE sms_conversations 
MODIFY COLUMN workflow_type ENUM('emergency','password_reset','ai_query','unknown','rejected') NOT NULL;
