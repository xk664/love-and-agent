package com.yuaiagent.service.chat.model;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 消息实体类
 */
@Data
@TableName("message")
public class Message {

    /**
     * 主键ID（自增）
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 会话ID（UUID格式）
     */
    private String chatId;

    /**
     * 角色：user | assistant | system
     */
    private String role;

    /**
     * 消息内容
     */
    private String content;

    /**
     * 消息元数据（JSON格式）
     * 包含：emotion_status, tokens_used, model, tool_calls, rag_sources
     */
    private String metadata;

    /**
     * 是否删除：0-未删除 1-已删除
     */
    @TableLogic
    private Integer isDeleted;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

}
