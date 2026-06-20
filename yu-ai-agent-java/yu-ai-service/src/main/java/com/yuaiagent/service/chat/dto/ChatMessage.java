package com.yuaiagent.service.chat.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 对话上下文消息
 * 用于组装发送给 AI 的对话历史
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChatMessage {

    /**
     * 角色：user | assistant | system
     */
    private String role;

    /**
     * 消息内容
     */
    private String content;

}
