package com.yuaiagent.service.chat.service.impl;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yuaiagent.common.exception.BusinessException;
import com.yuaiagent.service.chat.config.PythonServiceConfig;
import com.yuaiagent.service.chat.dto.*;
import com.yuaiagent.service.chat.mapper.ChatMapper;
import com.yuaiagent.service.chat.model.Chat;
import com.yuaiagent.service.chat.service.AiService;
import com.yuaiagent.service.chat.service.MessageService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * AI 服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AiServiceImpl implements AiService {

    private static final long SSE_TIMEOUT = 120_000L; // SSE 超时时间：120秒

    private final ChatMapper chatMapper;
    private final MessageService messageService;
    private final PythonServiceConfig pythonServiceConfig;
    private final OkHttpClient okHttpClient;
    private final ObjectMapper objectMapper;

    /**
     * 同步对话
     *
     * @param userId  用户ID
     * @param request 对话请求
     * @return 对话响应
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public SyncChatResponse syncChat(Long userId, SyncChatRequest request) {
        // 1. 校验会话是否存在且属于当前用户
        LambdaQueryWrapper<Chat> chatWrapper = new LambdaQueryWrapper<>();
        chatWrapper.eq(Chat::getChatId, request.getChatId())
                .eq(Chat::getUserId, userId);
        Chat chat = chatMapper.selectOne(chatWrapper);

        if (chat == null) {
            throw new BusinessException(404, "会话不存在");
        }

        // 2. 保存用户消息
        messageService.saveUserMessage(request.getChatId(), request.getMessage(), null);

        // 3. 获取跨会话记忆（最近20条消息）
        List<ChatMessage> history = messageService.getRecentMessagesAcrossChats(userId, 20);

        // 4. 构建 Python 服务请求
        PythonChatRequest pythonRequest = new PythonChatRequest();
        pythonRequest.setChatId(request.getChatId());
        pythonRequest.setMessage(request.getMessage());
        pythonRequest.setEmotionStatus(chat.getEmotionStatus());
        pythonRequest.setHistory(history);

        // 5. 调用 Python 服务
        PythonChatResponse pythonResponse = callPythonSyncChat(userId, pythonRequest);

        // 6. 保存 AI 消息
        String metadataJson = null;
        if (pythonResponse.getData() != null && pythonResponse.getData().getMetadata() != null) {
            try {
                metadataJson = objectMapper.writeValueAsString(pythonResponse.getData().getMetadata());
            } catch (Exception e) {
                log.warn("序列化 metadata 失败: {}", e.getMessage());
            }
        }

        messageService.saveAssistantMessage(request.getChatId(), pythonResponse.getData().getContent(), metadataJson);

        // 7. 构建响应
        SyncChatResponse response = new SyncChatResponse();
        response.setChatId(request.getChatId());
        response.setRole("assistant");
        response.setContent(pythonResponse.getData().getContent());
        response.setCreateTime(LocalDateTime.now());

        // 设置 metadata
        if (pythonResponse.getData().getMetadata() != null) {
            MessageResponse.MessageMetadata metadata = new MessageResponse.MessageMetadata();
            Map<String, Object> metadataMap = pythonResponse.getData().getMetadata();
            metadata.setEmotionStatus((String) metadataMap.get("emotion_status"));
            if (metadataMap.get("tokens_used") != null) {
                metadata.setTokensUsed((Integer) metadataMap.get("tokens_used"));
            }
            metadata.setModel((String) metadataMap.get("model"));
            metadata.setToolCalls(metadataMap.get("tool_calls"));
            metadata.setRagSources(metadataMap.get("rag_sources"));
            response.setMetadata(metadata);
        }

        log.info("同步对话成功: userId={}, chatId={}, contentLength={}", userId, request.getChatId(), response.getContent().length());

        return response;
    }

    /**
     * 流式对话（SSE）
     * Java 接收请求后转发到 Python SSE 端点，将 Python 返回的 SSE 事件流实时转发给前端
     *
     * @param userId  用户ID
     * @param request 对话请求
     * @return SSE 发射器
     */
    @Override
    public SseEmitter streamChat(Long userId, SyncChatRequest request) {
        // 1. 校验会话是否存在且属于当前用户
        LambdaQueryWrapper<Chat> chatWrapper = new LambdaQueryWrapper<>();
        chatWrapper.eq(Chat::getChatId, request.getChatId())
                .eq(Chat::getUserId, userId);
        Chat chat = chatMapper.selectOne(chatWrapper);

        if (chat == null) {
            throw new BusinessException(404, "会话不存在");
        }

        // 2. 保存用户消息
        messageService.saveUserMessage(request.getChatId(), request.getMessage(), null);

        // 3. 获取跨会话记忆（最近20条消息）
        List<ChatMessage> history = messageService.getRecentMessagesAcrossChats(userId, 20);

        // 4. 构建 Python 服务请求
        PythonChatRequest pythonRequest = new PythonChatRequest();
        pythonRequest.setChatId(request.getChatId());
        pythonRequest.setMessage(request.getMessage());
        pythonRequest.setEmotionStatus(chat.getEmotionStatus());
        pythonRequest.setHistory(history);

        // 5. 创建 SseEmitter
        SseEmitter emitter = new SseEmitter(SSE_TIMEOUT);

        // 6. 异步执行流式转发
        CompletableFuture.runAsync(() -> {
            StringBuilder contentBuilder = new StringBuilder();
            String metadataJson = null;

            try {
                // 调用 Python SSE 端点
                String url = pythonServiceConfig.getBaseUrl() + pythonServiceConfig.getEndpoints().getChatSse();
                String requestBody = objectMapper.writeValueAsString(pythonRequest);

                Request httpRequest = new Request.Builder()
                        .url(url)
                        .addHeader("X-User-Id", String.valueOf(userId))
                        .addHeader("Content-Type", "application/json")
                        .addHeader("Accept", "text/event-stream")
                        .post(RequestBody.create(requestBody, MediaType.parse("application/json")))
                        .build();

                try (Response response = okHttpClient.newCall(httpRequest).execute()) {
                    if (!response.isSuccessful() || response.body() == null) {
                        log.error("调用 Python SSE 服务失败: url={}, code={}", url, response.code());
                        emitter.send(SseEmitter.event()
                                .name("error")
                                .data(objectMapper.writeValueAsString(SSEEvent.error("AI 服务调用失败"))));
                        emitter.complete();
                        return;
                    }

                    // 逐行读取 SSE 流
                    try (BufferedReader reader = new BufferedReader(
                            new InputStreamReader(response.body().byteStream(), StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            if (line.isEmpty() || line.startsWith(":")) {
                                // 跳过空行和注释行
                                continue;
                            }

                            if (line.startsWith("data:")) {
                                String data = line.substring(5).trim();

                                // 检查结束标记
                                if ("[DONE]".equals(data)) {
                                    break;
                                }

                                // 解析 JSON 事件
                                try {
                                    Map<String, Object> eventMap = objectMapper.readValue(
                                            data, new TypeReference<Map<String, Object>>() {});

                                    String type = (String) eventMap.get("type");

                                    // 收集 answer 内容用于保存消息
                                    if ("answer".equals(type) && eventMap.get("content") != null) {
                                        contentBuilder.append(eventMap.get("content"));
                                    }

                                    // 收集 metadata 用于保存
                                    if ("metadata".equals(type) && eventMap.get("content") != null) {
                                        metadataJson = objectMapper.writeValueAsString(eventMap.get("content"));
                                    }

                                    // 转发事件给前端
                                    emitter.send(SseEmitter.event()
                                            .name("message")
                                            .data(data));

                                } catch (Exception e) {
                                    log.warn("解析 SSE 事件失败: line={}, error={}", line, e.getMessage());
                                }
                            }
                        }
                    }

                    // 流结束后保存 AI 消息
                    String content = contentBuilder.toString();
                    if (!content.isEmpty()) {
                        messageService.saveAssistantMessage(request.getChatId(), content, metadataJson);
                        log.info("SSE 对话保存成功: userId={}, chatId={}, contentLength={}", userId, request.getChatId(), content.length());
                    }

                    // 完成 SSE
                    emitter.complete();
                }

            } catch (IOException e) {
                log.error("SSE 流式对话异常: userId={}, chatId={}, error={}", userId, request.getChatId(), e.getMessage(), e);
                try {
                    emitter.send(SseEmitter.event()
                            .name("error")
                            .data(objectMapper.writeValueAsString(SSEEvent.error("AI 服务连接异常"))));
                } catch (Exception ignored) {
                }
                emitter.completeWithError(e);
            } catch (Exception e) {
                log.error("SSE 流式对话未知异常: userId={}, chatId={}, error={}", userId, request.getChatId(), e.getMessage(), e);
                try {
                    emitter.send(SseEmitter.event()
                            .name("error")
                            .data(objectMapper.writeValueAsString(SSEEvent.error("服务器内部错误"))));
                } catch (Exception ignored) {
                }
                emitter.completeWithError(e);
            }
        });

        // 7. 注册超时和错误回调
        emitter.onTimeout(() -> {
            log.warn("SSE 连接超时: userId={}, chatId={}", userId, request.getChatId());
            emitter.complete();
        });

        emitter.onError(e -> {
            log.warn("SSE 连接错误: userId={}, chatId={}, error={}", userId, request.getChatId(), e.getMessage());
        });

        log.info("SSE 流式对话开始: userId={}, chatId={}", userId, request.getChatId());

        return emitter;
    }

    /**
     * 调用 Python 服务同步对话
     */
    private PythonChatResponse callPythonSyncChat(Long userId, PythonChatRequest request) {
        String url = pythonServiceConfig.getBaseUrl() + pythonServiceConfig.getEndpoints().getChatSync();

        try {
            // 序列化请求体
            String requestBody = objectMapper.writeValueAsString(request);

            // 构建 HTTP 请求
            Request httpRequest = new Request.Builder()
                    .url(url)
                    .addHeader("X-User-Id", String.valueOf(userId))
                    .addHeader("Content-Type", "application/json")
                    .post(RequestBody.create(requestBody, MediaType.parse("application/json")))
                    .build();

            // 发送请求
            try (Response response = okHttpClient.newCall(httpRequest).execute()) {
                if (!response.isSuccessful()) {
                    log.error("调用 Python 服务失败: url={}, code={}, body={}", url, response.code(), response.body() != null ? response.body().string() : "null");
                    throw new BusinessException(500, "AI 服务调用失败");
                }

                // 解析响应
                String responseBody = response.body().string();
                PythonChatResponse pythonResponse = objectMapper.readValue(responseBody, PythonChatResponse.class);

                if (pythonResponse.getCode() != 200) {
                    log.error("Python 服务返回错误: url={}, code={}, message={}", url, pythonResponse.getCode(), pythonResponse.getMessage());
                    throw new BusinessException(500, "AI 服务返回错误: " + pythonResponse.getMessage());
                }

                return pythonResponse;
            }
        } catch (IOException e) {
            log.error("调用 Python 服务异常: url={}, error={}", url, e.getMessage(), e);
            throw new BusinessException(500, "AI 服务调用失败: " + e.getMessage());
        }
    }

}
