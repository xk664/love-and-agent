package com.yuaiagent.service.agent.dto;

import com.yuaiagent.service.chat.model.AgentTask;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 智能体任务响应
 */
@Data
public class AgentTaskResponse {

    /**
     * 任务ID（UUID）
     */
    private String taskId;

    /**
     * 关联会话ID
     */
    private String chatId;

    /**
     * 任务描述
     */
    private String message;

    /**
     * 任务状态
     */
    private String status;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 从实体转换
     */
    public static AgentTaskResponse fromEntity(AgentTask task) {
        AgentTaskResponse response = new AgentTaskResponse();
        response.setTaskId(task.getTaskId());
        response.setChatId(task.getChatId());
        response.setMessage(task.getMessage());
        response.setStatus(task.getStatus());
        response.setCreateTime(task.getCreateTime());
        return response;
    }

}
