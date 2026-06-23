package com.yuaiagent.service.agent.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 智能体任务回调请求
 * Python 任务执行完成后回调 Java 更新任务状态
 */
@Data
public class AgentCallbackRequest {

    /**
     * 任务ID（UUID）
     */
    @JsonProperty("task_id")
    private String taskId;

    /**
     * 状态：completed | failed
     */
    private String status;

    /**
     * 任务结果（completed 时为 AI 回答，failed 时为错误信息）
     */
    private String result;

    /**
     * 执行步骤详情（JSON 格式）
     * completed 时有值，格式如：
     * [
     *   {"step": 1, "action": "rag_retrieve", "detail": "检索到 3 条相关内容"},
     *   {"step": 2, "action": "llm_call", "detail": "调用 LLM 生成回答"}
     * ]
     */
    private List<Map<String, Object>> steps;

}
