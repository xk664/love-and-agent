-- 三层记忆架构数据库表设计
-- 在原有 database.sql 基础上添加

-- 删除已存在的表（如果存在）
DROP TABLE IF EXISTS `user_memory`;
DROP TABLE IF EXISTS `session_summary`;

-- 用户长期记忆表（Kryo序列化存储）
CREATE TABLE `user_memory` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `memory_type` VARCHAR(32) NOT NULL COMMENT '记忆类型: profile/preference/key_fact/episodic',
    `content_json` JSON COMMENT 'JSON格式的记忆内容',
    `content_text` TEXT COMMENT '文本格式的内容（便于查询和调试）',
    `embedding_id` VARCHAR(64) COMMENT 'PgVector中的向量ID',
    `importance_score` FLOAT DEFAULT 0.5 COMMENT '重要性评分(0-1)',
    `access_count` INT DEFAULT 0 COMMENT '访问次数（用于遗忘曲线）',
    `last_accessed` DATETIME COMMENT '最后访问时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_user_type` (`user_id`, `memory_type`),
    INDEX `idx_importance` (`importance_score` DESC),
    INDEX `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户长期记忆表';

-- 会话摘要表
CREATE TABLE `session_summary` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` VARCHAR(36) NOT NULL COMMENT '会话ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `summary` TEXT NOT NULL COMMENT '会话摘要',
    `key_topics` JSON COMMENT '关键话题标签',
    `emotion_trend` VARCHAR(20) COMMENT '情感趋势',
    `message_count` INT COMMENT '消息数量',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_chat_id` (`chat_id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_user_time` (`user_id`, `create_time` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话摘要表';

-- 用户画像示例数据结构（存在 user_memory.content_json 中）
-- {
--     "personal_info": {
--         "age_range": "20-25",
--         "occupation": "学生/上班族",
--         "location": "杭州"
--     },
--     "relationship_status": "异地恋3年",
--     "personality_traits": ["内向", "敏感"],
--     "concerns": ["安全感", "沟通问题"],
--     "preferences": ["具体建议", "温暖鼓励"],
--     "key_events": ["见家长", "讨论未来规划"]
-- }

-- 关键事实示例数据结构（存在 user_memory.content_json 中）
-- {
--     "fact": "用户男友妈妈嫌她学历低",
--     "type": "relationship"
-- }

-- 用户偏好示例数据结构（存在 user_memory.content_json 中）
-- {
--     "preference": "用户喜欢具体的行动建议，不喜欢大道理",
--     "category": "communication"
-- }

-- 情景记忆示例数据结构（存在 user_memory.content_json 中）
-- {
--     "chat_id": "会话ID",
--     "summary": "讨论了异地恋的未来规划",
--     "key_events": ["决定继续坚持", "计划明年同居"]
-- }
