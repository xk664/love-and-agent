package com.yuaiagent.service.agent.dto;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yuaiagent.service.chat.model.AgentTask;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 智能体任务状态查询响应
 */
@Data
public class AgentTaskStatusResponse {

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
     * 任务状态：pending | running | completed | failed | cancelled
     */
    private String status;

    /**
     * 任务结果（completed 时有值）
     */
    private String result;

    /**
     * 执行步骤（completed 时有值）
     */
    private List<Map<String, Object>> steps;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;

    private static final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * 从实体转换
     */
    public static AgentTaskStatusResponse fromEntity(AgentTask task) {
        AgentTaskStatusResponse response = new AgentTaskStatusResponse();
        response.setTaskId(task.getTaskId());
        response.setChatId(task.getChatId());
        response.setMessage(task.getMessage());
        response.setStatus(task.getStatus());
        response.setResult(task.getResult());
        response.setCreateTime(task.getCreateTime());
        response.setUpdateTime(task.getUpdateTime());

        // 解析 steps JSON
        if (task.getSteps() != null && !task.getSteps().isEmpty()) {
            try {
                List<Map<String, Object>> stepsList = objectMapper.readValue(
                        task.getSteps(), new TypeReference<List<Map<String, Object>>>() {});
                response.setSteps(stepsList);
            } catch (Exception e) {
                // JSON 解析失败，steps 为空
            }
        }

        return response;
    }

}
