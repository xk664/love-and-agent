package com.yuaiagent.service.chat.service;

import com.yuaiagent.common.response.PageResponse;
import com.yuaiagent.service.chat.dto.ChatMessage;
import com.yuaiagent.service.chat.dto.MessageListRequest;
import com.yuaiagent.service.chat.dto.MessageResponse;

import java.util.List;

/**
 * 消息服务接口
 */
public interface MessageService {

    /**
     * 保存用户消息
     *
     * @param chatId 会话ID
     * @param content 消息内容
     * @param metadata 元数据JSON（可选）
     * @return 消息响应
     */
    MessageResponse saveUserMessage(String chatId, String content, String metadata);

    /**
     * 保存 AI 消息
     *
     * @param chatId 会话ID
     * @param content 消息内容
     * @param metadata 元数据JSON（可选）
     * @return 消息响应
     */
    MessageResponse saveAssistantMessage(String chatId, String content, String metadata);

    /**
     * 获取消息历史（分页，时间倒序）
     *
     * @param userId 用户ID（用于校验会话归属）
     * @param chatId 会话ID
     * @param request 分页请求
     * @return 分页消息列表
     */
    PageResponse<MessageResponse> getMessageHistory(Long userId, String chatId, MessageListRequest request);

    /**
     * 获取跨会话记忆窗口（最近N条消息）
     * 查询同一用户所有会话的最近消息，不分 app_type
     *
     * @param userId 用户ID
     * @param limit  消息数量限制（默认20）
     * @return 对话上下文消息列表，按时间正序排列
     */
    List<ChatMessage> getRecentMessagesAcrossChats(Long userId, int limit);

}
