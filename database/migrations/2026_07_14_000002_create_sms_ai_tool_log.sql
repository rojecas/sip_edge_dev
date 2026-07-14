CREATE TABLE IF NOT EXISTS sms_ai_tool_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_id BIGINT UNSIGNED NOT NULL,
    incoming_msg_id BIGINT UNSIGNED NOT NULL,
    tool_name VARCHAR(64) NOT NULL,
    tool_args JSON NOT NULL,
    tool_result JSON NOT NULL,
    duration_ms INT NOT NULL,
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    CONSTRAINT fk_ai_tool_log_conversation FOREIGN KEY (conversation_id) REFERENCES sms_conversations(id),
    CONSTRAINT fk_ai_tool_log_message FOREIGN KEY (incoming_msg_id) REFERENCES sms_messages(id),
    INDEX idx_ai_tool_log_conv (conversation_id),
    INDEX idx_ai_tool_log_msg (incoming_msg_id),
    INDEX idx_ai_tool_log_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
