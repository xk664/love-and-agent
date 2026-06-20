package com.yuaiagent.service.chat.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 同步对话响应
 */
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class SyncChatResponse {

    /**
     * 会话ID
     */
    private String chatId;

    /**
     * 角色：assistant
     */
    private String role;

    /**
     * AI 回复内容
     */
    private String content;

    /**
     * 消息元数据
     */
    private MessageResponse.MessageMetadata metadata;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

}
