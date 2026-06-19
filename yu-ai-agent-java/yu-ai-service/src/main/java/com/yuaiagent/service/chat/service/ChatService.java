package com.yuaiagent.service.chat.service;

import com.yuaiagent.common.response.PageResponse;
import com.yuaiagent.service.chat.dto.ChatListRequest;
import com.yuaiagent.service.chat.dto.ChatResponse;
import com.yuaiagent.service.chat.dto.CreateChatRequest;

/**
 * 会话服务接口
 */
public interface ChatService {

    /**
     * 创建会话
     *
     * @param userId   用户ID
     * @param request  创建会话请求
     * @return 会话响应
     */
    ChatResponse createChat(Long userId, CreateChatRequest request);

    /**
     * 获取会话列表
     *
     * @param userId  用户ID
     * @param request 查询请求
     * @return 分页会话列表
     */
    PageResponse<ChatResponse> listChats(Long userId, ChatListRequest request);

    /**
     * 获取会话详情
     *
     * @param userId 用户ID
     * @param chatId 会话ID
     * @return 会话详情
     */
    ChatResponse getChatDetail(Long userId, String chatId);

    /**
     * 删除会话（软删除）
     * 级联软删除该会话下所有消息和关联的 agent_task
     *
     * @param userId 用户ID
     * @param chatId 会话ID
     */
    void deleteChat(Long userId, String chatId);

}
