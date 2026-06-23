package com.yuaiagent.service.agent.service;

import com.yuaiagent.service.agent.dto.AgentCallbackRequest;
import com.yuaiagent.service.agent.dto.AgentRunRequest;
import com.yuaiagent.service.agent.dto.AgentTaskResponse;
import com.yuaiagent.service.agent.dto.AgentTaskStatusResponse;

/**
 * 智能体任务服务接口
 */
public interface AgentTaskService {

    /**
     * 运行智能体任务
     *
     * @param userId  用户ID
     * @param request 任务请求
     * @return 任务响应
     */
    AgentTaskResponse runTask(Long userId, AgentRunRequest request);

    /**
     * 查询任务状态
     *
     * @param userId 用户ID
     * @param taskId 任务ID
     * @return 任务状态响应
     */
    AgentTaskStatusResponse getTaskStatus(Long userId, String taskId);

    /**
     * 处理 Python 回调
     * 更新任务状态、result、steps，并将 AI 结果存入 message 表
     *
     * @param request 回调请求
     */
    void handleCallback(AgentCallbackRequest request);

    /**
     * 取消任务
     * 支持 pending 和 running 状态的任务取消
     *
     * @param userId 用户ID
     * @param taskId 任务ID
     * @return 任务响应
     */
    AgentTaskResponse cancelTask(Long userId, String taskId);

}
