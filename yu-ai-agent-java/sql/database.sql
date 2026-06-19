-- ============================================================
-- Yu AI Agent 数据库初始化脚本
-- 数据库版本: MySQL 8.0+
-- ============================================================

-- 如果数据库存在则删除（开发环境使用）
DROP DATABASE IF EXISTS `yu_ai_agent`;

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `yu_ai_agent` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `yu_ai_agent`;

-- ============================================================
-- 用户表
-- ============================================================
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `password` VARCHAR(255) NOT NULL COMMENT '密码（BCrypt加密）',
    `nickname` VARCHAR(50) COMMENT '昵称',
    `avatar` VARCHAR(255) COMMENT '头像URL',
    `status` TINYINT DEFAULT 1 COMMENT '0-禁用 1-启用',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 对话表
-- ============================================================
DROP TABLE IF EXISTS `chat`;
CREATE TABLE `chat` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` VARCHAR(36) NOT NULL COMMENT 'UUID 格式',
    `user_id` BIGINT NOT NULL,
    `app_type` VARCHAR(20) NOT NULL COMMENT 'love_app | manus',
    `emotion_status` VARCHAR(20) COMMENT 'single | relationship | married（会话创建时设定，不可更改）',
    `title` VARCHAR(255),
    `last_message_time` DATETIME COMMENT '最后一条消息时间，用于会话列表排序',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_chat_id` (`chat_id`),
    INDEX `idx_user_app_type` (`user_id`, `app_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话表';

-- ============================================================
-- 消息表
-- ============================================================
DROP TABLE IF EXISTS `message`;
CREATE TABLE `message` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `chat_id` VARCHAR(36) NOT NULL COMMENT 'UUID 格式',
    `role` VARCHAR(20) NOT NULL COMMENT 'user | assistant | system',
    `content` TEXT NOT NULL,
    `metadata` JSON COMMENT '消息元数据，结构见下方 JSON 字段定义',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_chat_id` (`chat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';

-- ============================================================
-- 智能体任务表
-- ============================================================
DROP TABLE IF EXISTS `agent_task`;
CREATE TABLE `agent_task` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `task_id` VARCHAR(36) NOT NULL COMMENT 'UUID 格式',
    `user_id` BIGINT NOT NULL,
    `chat_id` VARCHAR(36) COMMENT '关联会话ID，Manus 类型通过此字段与 message 表关联',
    `message` TEXT NOT NULL COMMENT '任务描述（用户输入的任务指令）',
    `status` VARCHAR(20) DEFAULT 'pending' COMMENT 'pending | running | completed | failed | cancelled',
    `result` TEXT COMMENT '任务最终结果',
    `steps` JSON COMMENT '执行步骤详情，Python 完成时一次性回写，取消任务时清空',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_task_id` (`task_id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_chat_id` (`chat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能体任务表';
