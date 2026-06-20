package com.yuaiagent.service.chat.controller;

import com.yuaiagent.common.config.JwtAuthInterceptor;
import com.yuaiagent.common.response.Result;
import com.yuaiagent.service.chat.dto.SyncChatRequest;
import com.yuaiagent.service.chat.dto.SyncChatResponse;
import com.yuaiagent.service.chat.service.AiService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * AI 对话控制器
 */
@Tag(name = "AI 对话服务", description = "AI 对话服务相关接口（Java 转发调用 Python）")
@RestController
@RequestMapping("/api/v1/ai/love/chat")
@RequiredArgsConstructor
public class AiController {

    private final AiService aiService;

    /**
     * 同步对话
     *
     * @param request         HTTP请求（用于获取当前用户ID）
     * @param syncChatRequest 对话请求
     * @return 对话响应
     */
    @Operation(summary = "同步对话", description = "同步对话，Java 接收后转发调用 Python 服务")
    @PostMapping("/sync")
    public Result<SyncChatResponse> syncChat(
            HttpServletRequest request,
            @Valid @RequestBody SyncChatRequest syncChatRequest) {
        Long userId = getUserId(request);
        SyncChatResponse response = aiService.syncChat(userId, syncChatRequest);
        return Result.success(response);
    }

    /**
     * 流式对话（SSE）
     *
     * @param request         HTTP请求（用于获取当前用户ID）
     * @param syncChatRequest 对话请求
     * @return SSE 事件流
     */
    @Operation(summary = "流式对话", description = "流式对话（SSE），Java 接收后转发调用 Python SSE 服务")
    @PostMapping(value = "/sse", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamChat(
            HttpServletRequest request,
            @Valid @RequestBody SyncChatRequest syncChatRequest) {
        Long userId = getUserId(request);
        return aiService.streamChat(userId, syncChatRequest);
    }

    /**
     * 从 request attribute 获取用户ID
     */
    private Long getUserId(HttpServletRequest request) {
        return (Long) request.getAttribute(JwtAuthInterceptor.REQUEST_USER_ID);
    }

}
