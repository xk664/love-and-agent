package com.yuaiagent.service.agent.controller;

import com.yuaiagent.common.config.JwtAuthInterceptor;
import com.yuaiagent.common.response.Result;
import com.yuaiagent.service.agent.dto.AgentRunRequest;
import com.yuaiagent.service.agent.dto.AgentTaskResponse;
import com.yuaiagent.service.agent.dto.AgentTaskStatusResponse;
import com.yuaiagent.service.agent.service.AgentTaskService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 智能体任务控制器
 */
@Tag(name = "智能体任务", description = "智能体任务管理相关接口")
@RestController
@RequestMapping("/api/v1/agent")
@RequiredArgsConstructor
public class AgentTaskController {

    private final AgentTaskService agentTaskService;

    /**
     * 运行智能体任务
     *
     * @param request       HTTP请求（用于获取当前用户ID）
     * @param agentRunRequest 任务请求
     * @return 任务信息
     */
    @Operation(summary = "运行智能体任务", description = "提交智能体任务，每用户同时只能运行1个任务")
    @PostMapping("/run")
    public Result<AgentTaskResponse> runTask(
            HttpServletRequest request,
            @Valid @RequestBody AgentRunRequest agentRunRequest) {
        Long userId = getUserId(request);
        AgentTaskResponse response = agentTaskService.runTask(userId, agentRunRequest);
        return Result.success(response);
    }

    /**
     * 查询任务状态
     *
     * @param request HTTP请求（用于获取当前用户ID）
     * @param taskId  任务ID
     * @return 任务状态信息
     */
    @Operation(summary = "查询任务状态", description = "根据任务ID查询智能体任务状态，前端每3秒轮询一次")
    @GetMapping("/status/{taskId}")
    public Result<AgentTaskStatusResponse> getTaskStatus(
            HttpServletRequest request,
            @PathVariable String taskId) {
        Long userId = getUserId(request);
        AgentTaskStatusResponse response = agentTaskService.getTaskStatus(userId, taskId);
        return Result.success(response);
    }

    /**
     * 取消任务
     *
     * @param request HTTP请求（用于获取当前用户ID）
     * @param taskId  任务ID
     * @return 任务状态信息
     */
    @Operation(summary = "取消任务", description = "取消智能体任务，支持 pending 和 running 状态的任务")
    @PostMapping("/cancel/{taskId}")
    public Result<AgentTaskResponse> cancelTask(
            HttpServletRequest request,
            @PathVariable String taskId) {
        Long userId = getUserId(request);
        AgentTaskResponse response = agentTaskService.cancelTask(userId, taskId);
        return Result.success(response);
    }

    /**
     * 从 request attribute 获取用户ID
     */
    private Long getUserId(HttpServletRequest request) {
        return (Long) request.getAttribute(JwtAuthInterceptor.REQUEST_USER_ID);
    }

}
