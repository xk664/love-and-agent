package com.yuaiagent.service.chat.dto;

import com.yuaiagent.service.chat.model.Chat;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 会话响应
 */
@Data
public class ChatResponse {

    /**
     * 主键ID
     */
    private Long id;

    /**
     * 会话ID（UUID格式）
     */
    private String chatId;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 应用类型：love_app | manus
     */
    private String appType;

    /**
     * 情感状态（中文：单身/恋爱/已婚）
     */
    private String emotionStatus;

    /**
     * 会话标题
     */
    private String title;

    /**
     * 最后一条消息时间
     */
    private LocalDateTime lastMessageTime;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;

    /**
     * 将实体转换为响应对象
     */
    public static ChatResponse fromEntity(Chat chat) {
        ChatResponse response = new ChatResponse();
        response.setId(chat.getId());
        response.setChatId(chat.getChatId());
        response.setUserId(chat.getUserId());
        response.setAppType(chat.getAppType());
        response.setEmotionStatus(convertToChinese(chat.getEmotionStatus()));
        response.setTitle(chat.getTitle());
        response.setLastMessageTime(chat.getLastMessageTime());
        response.setCreateTime(chat.getCreateTime());
        response.setUpdateTime(chat.getUpdateTime());
        return response;
    }

    /**
     * 情感状态英文转中文
     */
    private static String convertToChinese(String emotionStatus) {
        if (emotionStatus == null) {
            return null;
        }
        return switch (emotionStatus) {
            case "single" -> "单身";
            case "relationship" -> "恋爱";
            case "married" -> "已婚";
            default -> emotionStatus;
        };
    }

}
