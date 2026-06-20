package com.yuaiagent.service.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Python 服务对话请求
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PythonChatRequest {

    /**
     * 会话ID
     */
    @JsonProperty("chat_id")
    private String chatId;

    /**
     * 用户消息
     */
    private String message;

    /**
     * 情感状态（英文值：single|relationship|married）
     */
    @JsonProperty("emotion_status")
    private String emotionStatus;

    /**
     * 跨会话记忆（最近20条消息）
     */
    private List<ChatMessage> history;

}
