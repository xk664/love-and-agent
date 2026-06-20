package com.yuaiagent.service.chat.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.yuaiagent.service.chat.model.Message;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 消息响应
 */
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class MessageResponse {

    /**
     * 主键ID
     */
    private Long id;

    /**
     * 会话ID（UUID格式）
     */
    private String chatId;

    /**
     * 角色：user | assistant | system
     */
    private String role;

    /**
     * 消息内容
     */
    private String content;

    /**
     * 消息元数据
     */
    private MessageMetadata metadata;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 消息元数据内部类
     */
    @Data
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class MessageMetadata {

        /**
         * 情感状态（中文：单身/恋爱/已婚）
         */
        private String emotionStatus;

        /**
         * 使用的 token 数量
         */
        private Integer tokensUsed;

        /**
         * 使用的模型
         */
        private String model;

        /**
         * 工具调用列表
         */
        private Object toolCalls;

        /**
         * RAG 来源列表
         */
        private Object ragSources;
    }

    /**
     * 将实体转换为响应对象
     */
    public static MessageResponse fromEntity(Message message) {
        MessageResponse response = new MessageResponse();
        response.setId(message.getId());
        response.setChatId(message.getChatId());
        response.setRole(message.getRole());
        response.setContent(message.getContent());
        response.setCreateTime(message.getCreateTime());

        // 解析 metadata JSON
        if (message.getMetadata() != null && !message.getMetadata().isEmpty()) {
            try {
                com.fasterxml.jackson.databind.ObjectMapper objectMapper = new com.fasterxml.jackson.databind.ObjectMapper();
                Map<String, Object> metadataMap = objectMapper.readValue(message.getMetadata(), Map.class);

                MessageMetadata metadata = new MessageMetadata();
                metadata.setEmotionStatus((String) metadataMap.get("emotion_status"));

                if (metadataMap.get("tokens_used") != null) {
                    metadata.setTokensUsed((Integer) metadataMap.get("tokens_used"));
                }

                metadata.setModel((String) metadataMap.get("model"));
                metadata.setToolCalls(metadataMap.get("tool_calls"));
                metadata.setRagSources(metadataMap.get("rag_sources"));

                response.setMetadata(metadata);
            } catch (Exception e) {
                // JSON 解析失败，忽略 metadata
            }
        }

        return response;
    }

}
