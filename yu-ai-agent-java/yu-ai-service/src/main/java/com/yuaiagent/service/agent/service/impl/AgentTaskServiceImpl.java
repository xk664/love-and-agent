package com.yuaiagent.service.agent.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yuaiagent.common.exception.BusinessException;
import com.yuaiagent.service.chat.config.PythonServiceConfig;
import com.yuaiagent.service.agent.dto.AgentCallbackRequest;
import com.yuaiagent.service.agent.dto.AgentRunRequest;
import com.yuaiagent.service.agent.dto.AgentTaskResponse;
import com.yuaiagent.service.agent.dto.AgentTaskStatusResponse;
import com.yuaiagent.service.agent.mapper.AgentTaskMapper;
import com.yuaiagent.service.chat.mapper.ChatMapper;
import com.yuaiagent.service.chat.model.AgentTask;
import com.yuaiagent.service.chat.model.Chat;
import com.yuaiagent.service.agent.service.AgentTaskService;
import com.yuaiagent.service.chat.service.MessageService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

/**
 * 智能体任务服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AgentTaskServiceImpl implements AgentTaskService {

    private final AgentTaskMapper agentTaskMapper;
    private final ChatMapper chatMapper;
    private final MessageService messageService;
    private final PythonServiceConfig pythonServiceConfig;
    private final OkHttpClient okHttpClient;
    private final ObjectMapper objectMapper;
    @Qualifier("agentTaskExecutor")
    private final Executor agentTaskExecutor;

    /**
     * 运行智能体任务
     *
     * 流程：
     * 1. 检查用户是否有运行中的任务
     * 2. 若无 chatId，自动创建 manus 类型会话
     * 3. 生成任务，状态为 pending
     * 4. 保存用户消息到 message 表
     * 5. 异步调用 Python 智能体服务
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public AgentTaskResponse runTask(Long userId, AgentRunRequest request) {
        // 1. 检查用户是否有运行中的任务（每用户同时只能 1 个）
        checkRunningTask(userId);

        // 2. 处理会话：若无 chatId 则自动创建 manus 类型会话
        String chatId = request.getChatId();
        if (!StringUtils.hasText(chatId)) {
            chatId = createManusChat(userId);
        } else {
            // 校验会话是否存在且属于当前用户
            validateChatOwnership(userId, chatId);
        }

        // 3. 创建任务
        String taskId = UUID.randomUUID().toString();
        AgentTask task = new AgentTask();
        task.setTaskId(taskId);
        task.setUserId(userId);
        task.setChatId(chatId);
        task.setMessage(request.getMessage());
        task.setStatus("pending");

        agentTaskMapper.insert(task);
        log.info("创建智能体任务: taskId={}, userId={}, chatId={}", taskId, userId, chatId);

        // 4. 保存用户消息到 message 表
        messageService.saveUserMessage(chatId, request.getMessage(), null);

        // 5. 异步调用 Python 智能体服务
        callPythonAgentAsync(userId, taskId, chatId, request.getMessage());

        // 6. 返回响应
        return AgentTaskResponse.fromEntity(task);
    }

    /**
     * 查询任务状态
     *
     * @param userId 用户ID
     * @param taskId 任务ID
     * @return 任务状态响应
     */
    @Override
    public AgentTaskStatusResponse getTaskStatus(Long userId, String taskId) {
        // 1. 查询任务
        LambdaQueryWrapper<AgentTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AgentTask::getTaskId, taskId)
                .eq(AgentTask::getUserId, userId);
        AgentTask task = agentTaskMapper.selectOne(wrapper);

        // 2. 判断任务是否存在
        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

        // 3. 返回状态响应
        return AgentTaskStatusResponse.fromEntity(task);
    }

    /**
     * 处理 Python 回调
     *
     * 流程：
     * 1. 根据 taskId 查询任务
     * 2. 更新任务状态、result、steps
     * 3. 如果是 completed，将 AI 结果存入 message 表
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void handleCallback(AgentCallbackRequest request) {
        // 1. 查询任务
        LambdaQueryWrapper<AgentTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AgentTask::getTaskId, request.getTaskId());
        AgentTask task = agentTaskMapper.selectOne(wrapper);

        if (task == null) {
            log.warn("回调任务不存在: taskId={}", request.getTaskId());
            throw new BusinessException(404, "任务不存在");
        }

        // 2. 校验状态：只有 pending/running 状态的任务才能被回调更新
        if (!"pending".equals(task.getStatus()) && !"running".equals(task.getStatus())) {
            log.warn("回调任务状态异常: taskId={}, currentStatus={}", request.getTaskId(), task.getStatus());
            throw new BusinessException(400, "任务状态不允许更新");
        }

        // 3. 更新任务状态
        task.setStatus(request.getStatus());
        task.setResult(request.getResult());

        // 4. 序列化 steps 为 JSON
        if (request.getSteps() != null && !request.getSteps().isEmpty()) {
            try {
                task.setSteps(objectMapper.writeValueAsString(request.getSteps()));
            } catch (Exception e) {
                log.warn("序列化 steps 失败: taskId={}, error={}", request.getTaskId(), e.getMessage());
            }
        }

        agentTaskMapper.updateById(task);
        log.info("任务回调更新成功: taskId={}, status={}", request.getTaskId(), request.getStatus());

        // 5. 如果是 completed，将 AI 结果存入 message 表
        if ("completed".equals(request.getStatus()) && StringUtils.hasText(request.getResult())) {
            messageService.saveAssistantMessage(task.getChatId(), request.getResult(), null);
            log.info("AI 结果已存入 message 表: chatId={}", task.getChatId());
        }
    }

    /**
     * 取消任务
     *
     * 流程：
     * 1. 根据 taskId + userId 查询任务
     * 2. 校验任务状态（只有 pending/running 可取消）
     * 3. 如果是 running，调用 Python 取消接口
     * 4. 更新任务状态为 cancelled，清空 steps
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public AgentTaskResponse cancelTask(Long userId, String taskId) {
        // 1. 查询任务
        LambdaQueryWrapper<AgentTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AgentTask::getTaskId, taskId)
                .eq(AgentTask::getUserId, userId);
        AgentTask task = agentTaskMapper.selectOne(wrapper);

        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

        // 2. 校验状态：只有 pending/running 可取消
        if (!"pending".equals(task.getStatus()) && !"running".equals(task.getStatus())) {
            throw new BusinessException(400, "当前状态不允许取消: " + task.getStatus());
        }

        // 3. 如果是 running，调用 Python 取消接口
        if ("running".equals(task.getStatus())) {
            callPythonCancelAsync(taskId);
        }

        // 4. 更新任务状态为 cancelled，清空 steps 和 result
        task.setStatus("cancelled");
        task.setSteps(null);
        task.setResult("用户取消任务");
        agentTaskMapper.updateById(task);

        log.info("任务已取消: taskId={}, userId={}", taskId, userId);

        // 5. 返回响应
        return AgentTaskResponse.fromEntity(task);
    }

    /**
     * 异步调用 Python 取消接口
     */
    private void callPythonCancelAsync(String taskId) {
        CompletableFuture.runAsync(() -> {
            try {
                Map<String, Object> requestBody = new HashMap<>();
                requestBody.put("task_id", taskId);

                String url = pythonServiceConfig.getBaseUrl() + pythonServiceConfig.getEndpoints().getAgentCancel();
                String jsonBody = objectMapper.writeValueAsString(requestBody);

                Request httpRequest = new Request.Builder()
                        .url(url)
                        .addHeader("Content-Type", "application/json")
                        .post(RequestBody.create(jsonBody, MediaType.parse("application/json")))
                        .build();

                try (Response response = okHttpClient.newCall(httpRequest).execute()) {
                    if (response.isSuccessful()) {
                        log.info("Python 取消任务成功: taskId={}", taskId);
                    } else {
                        log.warn("Python 取消任务失败: taskId={}, code={}", taskId, response.code());
                    }
                }
            } catch (Exception e) {
                log.warn("调用 Python 取消接口异常: taskId={}, error={}", taskId, e.getMessage());
            }
        }, agentTaskExecutor);
    }

    /**
     * 检查用户是否有运行中的任务
     */
    private void checkRunningTask(Long userId) {
        LambdaQueryWrapper<AgentTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AgentTask::getUserId, userId)
                .in(AgentTask::getStatus, "pending", "running");
        Long count = agentTaskMapper.selectCount(wrapper);

        if (count > 0) {
            throw new BusinessException(409, "您有任务正在运行中，请等待完成后再提交新任务");
        }
    }

    /**
     * 创建 manus 类型会话
     */
    private String createManusChat(Long userId) {
        Chat chat = new Chat();
        chat.setChatId(UUID.randomUUID().toString());
        chat.setUserId(userId);
        chat.setAppType("manus");
        chat.setTitle("智能体任务");

        chatMapper.insert(chat);
        log.info("自动创建 manus 会话: chatId={}, userId={}", chat.getChatId(), userId);

        return chat.getChatId();
    }

    /**
     * 校验会话是否属于当前用户
     */
    private void validateChatOwnership(Long userId, String chatId) {
        LambdaQueryWrapper<Chat> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Chat::getChatId, chatId)
                .eq(Chat::getUserId, userId);
        Chat chat = chatMapper.selectOne(wrapper);

        if (chat == null) {
            throw new BusinessException(404, "会话不存在");
        }
    }

    /**
     * 异步调用 Python 智能体服务
     */
    private void callPythonAgentAsync(Long userId, String taskId, String chatId, String message) {
        CompletableFuture.runAsync(() -> {
            try {
                // 更新任务状态为 running
                LambdaQueryWrapper<AgentTask> wrapper = new LambdaQueryWrapper<>();
                wrapper.eq(AgentTask::getTaskId, taskId);
                AgentTask task = agentTaskMapper.selectOne(wrapper);

                if (task != null) {
                    task.setStatus("running");
                    agentTaskMapper.updateById(task);
                }

                // 构建请求
                Map<String, Object> requestBody = new HashMap<>();
                requestBody.put("task_id", taskId);
                requestBody.put("chat_id", chatId);
                requestBody.put("message", message);

                String url = pythonServiceConfig.getBaseUrl() + pythonServiceConfig.getEndpoints().getAgentRun();
                String jsonBody = objectMapper.writeValueAsString(requestBody);

                Request httpRequest = new Request.Builder()
                        .url(url)
                        .addHeader("X-User-Id", String.valueOf(userId))
                        .addHeader("Content-Type", "application/json")
                        .post(RequestBody.create(jsonBody, MediaType.parse("application/json")))
                        .build();

                // 发送请求
                try (Response response = okHttpClient.newCall(httpRequest).execute()) {
                    if (response.isSuccessful()) {
                        log.info("Python 智能体任务完成: taskId={}", taskId);
                        // Python 端会通过回调更新任务状态
                    } else {
                        log.error("Python 智能体任务失败: taskId={}, code={}", taskId, response.code());
                        updateTaskStatus(taskId, "failed", "Python 服务调用失败: HTTP " + response.code());
                    }
                }
            } catch (Exception e) {
                log.error("调用 Python 智能体服务异常: taskId={}, error={}", taskId, e.getMessage(), e);
                updateTaskStatus(taskId, "failed", "服务调用异常: " + e.getMessage());
            }
        }, agentTaskExecutor);
    }

    /**
     * 更新任务状态
     */
    private void updateTaskStatus(String taskId, String status, String result) {
        try {
            LambdaQueryWrapper<AgentTask> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(AgentTask::getTaskId, taskId);
            AgentTask task = agentTaskMapper.selectOne(wrapper);

            if (task != null) {
                task.setStatus(status);
                task.setResult(result);
                agentTaskMapper.updateById(task);
            }
        } catch (Exception e) {
            log.error("更新任务状态失败: taskId={}, error={}", taskId, e.getMessage());
        }
    }

}
