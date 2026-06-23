package com.yuaiagent.service.agent.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 智能体任务运行请求
 */
@Data
public class AgentRunRequest {

    /**
     * 用户消息（任务指令）
     */
    @NotBlank(message = "消息内容不能为空")
    private String message;

    /**
     * 会话ID（可选）
     * 不传则自动创建 manus 类型会话
     */
    private String chatId;

}
