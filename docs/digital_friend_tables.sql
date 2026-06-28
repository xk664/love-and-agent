-- 数字朋友功能数据库表

-- 如果表存在则删除
DROP TABLE IF EXISTS `digital_friend`;

-- 数字朋友主表
CREATE TABLE `digital_friend` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL COMMENT '创建者用户ID',
    `name` VARCHAR(64) NOT NULL COMMENT '朋友昵称',
    `avatar_url` VARCHAR(512) COMMENT '头像URL',
    `description` TEXT COMMENT '用户对朋友的一句话描述',
    `source_materials` LONGTEXT COMMENT '用户上传的原始素材（JSON格式）',
    `calibration_questions` TEXT COMMENT '校准问题列表（JSON格式）',
    `calibration_answers` TEXT COMMENT '校准回答列表（JSON格式）',
    `system_prompt` LONGTEXT COMMENT 'LLM根据素材+校准回答生成的完整系统提示词',
    `status` VARCHAR(20) DEFAULT 'draft' COMMENT '状态: draft/processing/calibrating/ready/failed',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数字朋友表';

-- chat 表新增 friend_id 字段（关联数字朋友）
ALTER TABLE `chat` ADD COLUMN `friend_id` BIGINT DEFAULT NULL COMMENT '关联的数字朋友ID' AFTER `emotion_status`;
