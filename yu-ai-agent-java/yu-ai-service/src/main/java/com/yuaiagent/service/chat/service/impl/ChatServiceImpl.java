package com.yuaiagent.service.chat.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yuaiagent.common.exception.BusinessException;
import com.yuaiagent.common.response.PageResponse;
import com.yuaiagent.service.chat.dto.ChatListRequest;
import com.yuaiagent.service.chat.dto.ChatResponse;
import com.yuaiagent.service.chat.dto.CreateChatRequest;
import com.yuaiagent.service.chat.mapper.AgentTaskMapper;
import com.yuaiagent.service.chat.mapper.ChatMapper;
import com.yuaiagent.service.chat.mapper.MessageMapper;
import com.yuaiagent.service.chat.model.AgentTask;
import com.yuaiagent.service.chat.model.Chat;
import com.yuaiagent.service.chat.model.Message;
import com.yuaiagent.service.chat.service.ChatService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 会话服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ChatServiceImpl implements ChatService {

    private final ChatMapper chatMapper;
    private final MessageMapper messageMapper;
    private final AgentTaskMapper agentTaskMapper;

    /**
     * 创建会话
     *
     * @param userId  用户ID
     * @param request 创建会话请求
     * @return 会话响应
     */
    @Override
    public ChatResponse createChat(Long userId, CreateChatRequest request) {
        // 1. 校验情感状态（love_app 必填，manus 忽略）
        validateEmotionStatus(request);

        // 2. 创建会话实体
        Chat chat = new Chat();
        chat.setChatId(UUID.randomUUID().toString());
        chat.setUserId(userId);
        chat.setAppType(request.getAppType());
        chat.setEmotionStatus(request.getEmotionStatus());
        chat.setTitle(request.getTitle());

        // 3. 保存会话
        chatMapper.insert(chat);

        log.info("创建会话成功: chatId={}, userId={}, appType={}", chat.getChatId(), userId, request.getAppType());

        // 4. 返回响应（情感状态转中文）
        return ChatResponse.fromEntity(chat);
    }

    /**
     * 获取会话列表
     *
     * @param userId  用户ID
     * @param request 查询请求
     * @return 分页会话列表
     */
    @Override
    public PageResponse<ChatResponse> listChats(Long userId, ChatListRequest request) {
        // 1. 构建查询条件
        LambdaQueryWrapper<Chat> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Chat::getUserId, userId);

        // 按 app_type 筛选（可选）
        if (StringUtils.hasText(request.getAppType())) {
            wrapper.eq(Chat::getAppType, request.getAppType());
        }

        // 按 last_message_time 倒序排序
        wrapper.orderByDesc(Chat::getLastMessageTime);

        // 2. 分页查询
        Page<Chat> page = new Page<>(request.getPage(), request.getPageSize());
        Page<Chat> result = chatMapper.selectPage(page, wrapper);

        // 3. 转换为响应对象
        List<ChatResponse> list = result.getRecords().stream()
                .map(ChatResponse::fromEntity)
                .collect(Collectors.toList());

        log.debug("查询会话列表: userId={}, page={}, size={}, total={}", userId, request.getPage(), request.getPageSize(), result.getTotal());

        // 4. 返回分页响应
        return PageResponse.of(list, request.getPage(), request.getPageSize(), result.getTotal());
    }

    /**
     * 获取会话详情
     *
     * @param userId 用户ID
     * @param chatId 会话ID
     * @return 会话详情
     */
    @Override
    public ChatResponse getChatDetail(Long userId, String chatId) {
        // 1. 查询会话
        LambdaQueryWrapper<Chat> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Chat::getChatId, chatId)
                .eq(Chat::getUserId, userId);

        Chat chat = chatMapper.selectOne(wrapper);

        // 2. 判断会话是否存在
        if (chat == null) {
            throw new BusinessException(404, "会话不存在");
        }

        log.debug("查询会话详情: chatId={}, userId={}", chatId, userId);

        // 3. 返回响应
        return ChatResponse.fromEntity(chat);
    }

    /**
     * 校验情感状态
     */
    private void validateEmotionStatus(CreateChatRequest request) {
        if ("love_app".equals(request.getAppType())) {
            // love_app 类型必须填写情感状态
            if (request.getEmotionStatus() == null || request.getEmotionStatus().isEmpty()) {
                throw new BusinessException(400, "恋爱大师应用必须选择情感状态");
            }
        } else if ("manus".equals(request.getAppType())) {
            // manus 类型忽略情感状态
            request.setEmotionStatus(null);
        }
    }

    /**
     * 删除会话（软删除）
     * 级联软删除该会话下所有消息和关联的 agent_task
     *
     * @param userId 用户ID
     * @param chatId 会话ID
     */
    @Override
    public void deleteChat(Long userId, String chatId) {
        // 1. 查询会话是否存在
        LambdaQueryWrapper<Chat> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Chat::getChatId, chatId)
                .eq(Chat::getUserId, userId);

        Chat chat = chatMapper.selectOne(wrapper);

        // 2. 判断会话是否存在
        if (chat == null) {
            throw new BusinessException(404, "会话不存在");
        }

        // 3. 级联软删除该会话下所有消息
        LambdaQueryWrapper<Message> messageWrapper = new LambdaQueryWrapper<>();
        messageWrapper.eq(Message::getChatId, chatId);
        messageMapper.delete(messageWrapper);

        // 4. 级联软删除该会话关联的 agent_task
        LambdaQueryWrapper<AgentTask> agentTaskWrapper = new LambdaQueryWrapper<>();
        agentTaskWrapper.eq(AgentTask::getChatId, chatId);
        agentTaskMapper.delete(agentTaskWrapper);

        // 5. 软删除会话
        chatMapper.deleteById(chat.getId());

        log.info("删除会话成功: chatId={}, userId={}, 删除了 {} 条消息和关联的 agent_task",
                chatId, userId, chatId);
    }

}
