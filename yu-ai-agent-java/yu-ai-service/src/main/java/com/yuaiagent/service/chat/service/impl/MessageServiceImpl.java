package com.yuaiagent.service.chat.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yuaiagent.common.exception.BusinessException;
import com.yuaiagent.common.response.PageResponse;
import com.yuaiagent.service.chat.dto.ChatMessage;
import com.yuaiagent.service.chat.dto.MessageListRequest;
import com.yuaiagent.service.chat.dto.MessageResponse;
import com.yuaiagent.service.chat.mapper.ChatMapper;
import com.yuaiagent.service.chat.mapper.MessageMapper;
import com.yuaiagent.service.chat.model.Chat;
import com.yuaiagent.service.chat.model.Message;
import com.yuaiagent.service.chat.service.MessageService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 消息服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MessageServiceImpl implements MessageService {

    private final MessageMapper messageMapper;
    private final ChatMapper chatMapper;

    /**
     * 保存用户消息
     *
     * @param chatId   会话ID
     * @param content  消息内容
     * @param metadata 元数据JSON（可选）
     * @return 消息响应
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public MessageResponse saveUserMessage(String chatId, String content, String metadata) {
        return saveMessage(chatId, "user", content, metadata);
    }

    /**
     * 保存 AI 消息
     *
     * @param chatId   会话ID
     * @param content  消息内容
     * @param metadata 元数据JSON（可选）
     * @return 消息响应
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public MessageResponse saveAssistantMessage(String chatId, String content, String metadata) {
        return saveMessage(chatId, "assistant", content, metadata);
    }

    /**
     * 保存消息（通用方法）
     *
     * @param chatId   会话ID
     * @param role     角色
     * @param content  消息内容
     * @param metadata 元数据JSON
     * @return 消息响应
     */
    private MessageResponse saveMessage(String chatId, String role, String content, String metadata) {
        // 1. 校验会话是否存在
        LambdaQueryWrapper<Chat> chatWrapper = new LambdaQueryWrapper<>();
        chatWrapper.eq(Chat::getChatId, chatId);
        Chat chat = chatMapper.selectOne(chatWrapper);

        if (chat == null) {
            throw new BusinessException(404, "会话不存在");
        }

        // 2. 创建消息实体
        Message message = new Message();
        message.setChatId(chatId);
        message.setRole(role);
        message.setContent(content);
        message.setMetadata(metadata);

        // 3. 保存消息
        messageMapper.insert(message);

        // 4. 更新会话的最后消息时间
        chat.setLastMessageTime(LocalDateTime.now());
        chatMapper.updateById(chat);

        log.info("保存消息成功: chatId={}, role={}, messageId={}", chatId, role, message.getId());

        // 5. 返回响应
        return MessageResponse.fromEntity(message);
    }

    /**
     * 获取消息历史（分页，时间倒序）
     *
     * @param userId  用户ID（用于校验会话归属）
     * @param chatId  会话ID
     * @param request 分页请求
     * @return 分页消息列表
     */
    @Override
    public PageResponse<MessageResponse> getMessageHistory(Long userId, String chatId, MessageListRequest request) {
        // 1. 校验会话是否存在且属于当前用户
        LambdaQueryWrapper<Chat> chatWrapper = new LambdaQueryWrapper<>();
        chatWrapper.eq(Chat::getChatId, chatId)
                .eq(Chat::getUserId, userId);
        Chat chat = chatMapper.selectOne(chatWrapper);

        if (chat == null) {
            throw new BusinessException(404, "会话不存在");
        }

        // 2. 构建查询条件
        LambdaQueryWrapper<Message> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Message::getChatId, chatId);

        // 按创建时间倒序（最新消息在前）
        wrapper.orderByDesc(Message::getCreateTime);

        // 3. 分页查询
        Page<Message> page = new Page<>(request.getPage(), request.getPageSize());
        Page<Message> result = messageMapper.selectPage(page, wrapper);

        // 4. 转换为响应对象
        List<MessageResponse> list = result.getRecords().stream()
                .map(MessageResponse::fromEntity)
                .collect(Collectors.toList());

        log.debug("查询消息历史: userId={}, chatId={}, page={}, size={}, total={}",
                userId, chatId, request.getPage(), request.getPageSize(), result.getTotal());

        // 5. 返回分页响应
        return PageResponse.of(list, request.getPage(), request.getPageSize(), result.getTotal());
    }

    /**
     * 获取跨会话记忆窗口（最近N条消息）
     * 查询同一用户所有会话的最近消息，不分 app_type
     *
     * @param userId 用户ID
     * @param limit  消息数量限制（默认20）
     * @return 对话上下文消息列表，按时间正序排列
     */
    @Override
    public List<ChatMessage> getRecentMessagesAcrossChats(Long userId, int limit) {
        // 1. 查询用户的所有会话ID
        LambdaQueryWrapper<Chat> chatWrapper = new LambdaQueryWrapper<>();
        chatWrapper.eq(Chat::getUserId, userId)
                .select(Chat::getChatId);
        List<Chat> chats = chatMapper.selectList(chatWrapper);

        if (chats.isEmpty()) {
            return Collections.emptyList();
        }

        List<String> chatIds = chats.stream()
                .map(Chat::getChatId)
                .collect(Collectors.toList());

        // 2. 查询这些会话的最近消息（按时间倒序）
        LambdaQueryWrapper<Message> messageWrapper = new LambdaQueryWrapper<>();
        messageWrapper.in(Message::getChatId, chatIds)
                .in(Message::getRole, "user", "assistant")  // 只查询用户和AI消息
                .orderByDesc(Message::getCreateTime)
                .last("LIMIT " + limit);

        List<Message> messages = messageMapper.selectList(messageWrapper);

        // 3. 转换为 ChatMessage 并按时间正序排列
        List<ChatMessage> chatMessages = messages.stream()
                .map(msg -> new ChatMessage(msg.getRole(), msg.getContent()))
                .collect(Collectors.toList());

        // 反转列表，使其按时间正序（最早的消息在前）
        Collections.reverse(chatMessages);

        log.debug("获取跨会话记忆窗口: userId={}, limit={}, 实际返回={}", userId, limit, chatMessages.size());

        return chatMessages;
    }

}
