package com.yuaiagent.service.chat.service;

import com.yuaiagent.service.chat.dto.SyncChatRequest;
import com.yuaiagent.service.chat.dto.SyncChatResponse;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * AI 服务接口
 */
public interface AiService {

    /**
     * 同步对话
     *
     * @param userId  用户ID
     * @param request 对话请求
     * @return 对话响应
     */
    SyncChatResponse syncChat(Long userId, SyncChatRequest request);

    /**
     * 流式对话（SSE）
     * Java 接收请求后转发到 Python SSE 端点，将 Python 返回的 SSE 事件流实时转发给前端
     *
     * @param userId  用户ID
     * @param request 对话请求
     * @return SSE 发射器
     */
    SseEmitter streamChat(Long userId, SyncChatRequest request);

}
