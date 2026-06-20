package com.yuaiagent.service.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.Map;

/**
 * Python 服务对话响应
 */
@Data
public class PythonChatResponse {

    /**
     * 响应码
     */
    private Integer code;

    /**
     * 响应数据
     */
    private PythonChatData data;

    /**
     * 响应消息
     */
    private String message;

    /**
     * Python 响应数据
     */
    @Data
    public static class PythonChatData {

        /**
         * AI 回复内容
         */
        private String content;

        /**
         * 消息元数据
         */
        private Map<String, Object> metadata;

    }

}
