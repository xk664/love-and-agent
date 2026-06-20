package com.yuaiagent.service.chat.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 同步对话请求
 */
@Data
public class SyncChatRequest {

    /**
     * 会话ID（UUID格式）
     */
    @NotBlank(message = "会话ID不能为空")
    private String chatId;

    /**
     * 用户消息
     */
    @NotBlank(message = "消息内容不能为空")
    private String message;

}
