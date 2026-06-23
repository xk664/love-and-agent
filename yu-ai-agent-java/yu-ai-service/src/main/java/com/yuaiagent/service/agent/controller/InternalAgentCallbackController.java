package com.yuaiagent.service.agent.controller;

import com.yuaiagent.common.exception.BusinessException;
import com.yuaiagent.common.response.Result;
import com.yuaiagent.service.agent.dto.AgentCallbackRequest;
import com.yuaiagent.service.agent.service.AgentTaskService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

/**
 * 智能体任务内部回调控制器
 * Python 任务执行完成后回调此接口更新任务状态
 */
@Slf4j
@Tag(name = "智能体任务内部回调", description = "Python 任务执行完成回调接口（仅内部调用）")
@RestController
@RequestMapping("/api/v1/internal/callback/agent")
@RequiredArgsConstructor
public class InternalAgentCallbackController {

    private final AgentTaskService agentTaskService;

    @Value("${internal.callback.token:}")
    private String internalToken;

    /**
     * 任务执行完成回调
     * Python 任务执行完成后调用此接口更新任务状态
     *
     * @param token   内部认证 Token（X-Internal-Token 请求头）
     * @param request 回调请求
     * @return 操作结果
     */
    @Operation(summary = "任务执行回调", description = "Python 任务执行完成后回调更新任务状态、result、steps")
    @PostMapping("/task")
    public Result<Void> handleTaskCallback(
            @RequestHeader(value = "X-Internal-Token", required = false) String token,
            @Valid @RequestBody AgentCallbackRequest request) {
        // 1. 校验内部 Token
        validateInternalToken(token);

        // 2. 参数校验
        if (!StringUtils.hasText(request.getTaskId())) {
            throw new BusinessException(400, "taskId 不能为空");
        }
        if (!StringUtils.hasText(request.getStatus())) {
            throw new BusinessException(400, "status 不能为空");
        }
        if (!"completed".equals(request.getStatus()) && !"failed".equals(request.getStatus())) {
            throw new BusinessException(400, "status 必须为 completed 或 failed");
        }

        log.info("收到智能体任务回调: taskId={}, status={}, resultLength={}",
                request.getTaskId(), request.getStatus(),
                request.getResult() != null ? request.getResult().length() : 0);

        // 3. 处理回调
        agentTaskService.handleCallback(request);

        return Result.success();
    }

    /**
     * 校验内部 Token
     */
    private void validateInternalToken(String token) {
        // 如果没有配置 Token，跳过校验（开发环境）
        if (!StringUtils.hasText(internalToken)) {
            return;
        }

        if (!StringUtils.hasText(token) || !internalToken.equals(token)) {
            throw new BusinessException(401, "无效的内部认证 Token");
        }
    }

}
