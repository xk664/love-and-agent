package com.yuaiagent.service.chat.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * SSE 事件 DTO
 * 用于 Java 端转发 Python SSE 事件给前端
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class SSEEvent {

    /**
     * 事件类型：thinking, answer, tool_call, tool_result, metadata, error
     */
    private String type;

    /**
     * 事件内容（thinking/answer 使用）
     */
    private Object content;

    /**
     * 工具名称（tool_call/tool_result 使用）
     */
    private String tool;

    /**
     * 工具参数（tool_call 使用）
     */
    private Object args;

    /**
     * 工具结果（tool_result 使用）
     */
    private Object result;

    /**
     * 错误信息（error 使用）
     */
    private String message;

    /**
     * 创建 thinking 事件
     */
    public static SSEEvent thinking(String content) {
        return new SSEEvent("thinking", content, null, null, null, null);
    }

    /**
     * 创建 answer 事件
     */
    public static SSEEvent answer(String content) {
        return new SSEEvent("answer", content, null, null, null, null);
    }

    /**
     * 创建 metadata 事件
     */
    public static SSEEvent metadata(Object content) {
        return new SSEEvent("metadata", content, null, null, null, null);
    }

    /**
     * 创建 error 事件
     */
    public static SSEEvent error(String message) {
        return new SSEEvent("error", null, null, null, null, message);
    }

}
