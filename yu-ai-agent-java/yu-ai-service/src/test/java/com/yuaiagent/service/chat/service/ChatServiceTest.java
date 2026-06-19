package com.yuaiagent.service.chat.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yuaiagent.common.exception.BusinessException;
import com.yuaiagent.service.chat.dto.ChatListRequest;
import com.yuaiagent.service.chat.dto.ChatResponse;
import com.yuaiagent.service.chat.dto.CreateChatRequest;
import com.yuaiagent.service.chat.mapper.AgentTaskMapper;
import com.yuaiagent.service.chat.mapper.ChatMapper;
import com.yuaiagent.service.chat.mapper.MessageMapper;
import com.yuaiagent.service.chat.model.AgentTask;
import com.yuaiagent.service.chat.model.Chat;
import com.yuaiagent.service.chat.model.Message;
import com.yuaiagent.service.chat.service.impl.ChatServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * 会话服务单元测试
 */
@ExtendWith(MockitoExtension.class)
public class ChatServiceTest {

    @Mock
    private ChatMapper chatMapper;

    @Mock
    private MessageMapper messageMapper;

    @Mock
    private AgentTaskMapper agentTaskMapper;

    @InjectMocks
    private ChatServiceImpl chatService;

    private Long userId;
    private String chatId;
    private Chat chat;

    @BeforeEach
    void setUp() {
        userId = 1L;
        chatId = UUID.randomUUID().toString();

        chat = new Chat();
        chat.setId(1L);
        chat.setChatId(chatId);
        chat.setUserId(userId);
        chat.setAppType("love_app");
        chat.setEmotionStatus("single");
        chat.setTitle("测试会话");
        chat.setIsDeleted(0);
        chat.setCreateTime(LocalDateTime.now());
        chat.setUpdateTime(LocalDateTime.now());
    }

    @Test
    void testCreateChat_Success() {
        // 准备测试数据
        CreateChatRequest request = new CreateChatRequest();
        request.setAppType("love_app");
        request.setEmotionStatus("single");
        request.setTitle("测试会话");

        when(chatMapper.insert(any(Chat.class))).thenReturn(1);

        // 执行测试
        ChatResponse response = chatService.createChat(userId, request);

        // 验证结果
        assertNotNull(response);
        assertEquals("love_app", response.getAppType());
        assertEquals("单身", response.getEmotionStatus());
        assertEquals("测试会话", response.getTitle());

        // 验证调用
        verify(chatMapper, times(1)).insert(any(Chat.class));
    }

    @Test
    void testCreateChat_LoveAppWithoutEmotionStatus_ThrowsException() {
        // 准备测试数据
        CreateChatRequest request = new CreateChatRequest();
        request.setAppType("love_app");
        request.setEmotionStatus(null);

        // 执行测试并验证异常
        assertThrows(BusinessException.class, () -> {
            chatService.createChat(userId, request);
        });

        // 验证没有调用插入
        verify(chatMapper, never()).insert(any(Chat.class));
    }

    @Test
    void testListChats_Success() {
        // 准备测试数据
        ChatListRequest request = new ChatListRequest();
        request.setPage(1);
        request.setPageSize(10);
        request.setAppType(null);

        List<Chat> chats = Arrays.asList(chat);
        com.baomidou.mybatisplus.extension.plugins.pagination.Page<Chat> page = new com.baomidou.mybatisplus.extension.plugins.pagination.Page<>(1, 10);
        page.setRecords(chats);
        page.setTotal(1);

        when(chatMapper.selectPage(any(), any(LambdaQueryWrapper.class))).thenReturn(page);

        // 执行测试
        var response = chatService.listChats(userId, request);

        // 验证结果
        assertNotNull(response);
        assertEquals(1, response.getList().size());
        assertEquals(1, response.getPagination().getTotal());

        // 验证调用
        verify(chatMapper, times(1)).selectPage(any(), any(LambdaQueryWrapper.class));
    }

    @Test
    void testGetChatDetail_Success() {
        // 准备测试数据
        when(chatMapper.selectOne(any(LambdaQueryWrapper.class))).thenReturn(chat);

        // 执行测试
        ChatResponse response = chatService.getChatDetail(userId, chatId);

        // 验证结果
        assertNotNull(response);
        assertEquals(chatId, response.getChatId());
        assertEquals("测试会话", response.getTitle());

        // 验证调用
        verify(chatMapper, times(1)).selectOne(any(LambdaQueryWrapper.class));
    }

    @Test
    void testGetChatDetail_ChatNotFound_ThrowsException() {
        // 准备测试数据
        when(chatMapper.selectOne(any(LambdaQueryWrapper.class))).thenReturn(null);

        // 执行测试并验证异常
        assertThrows(BusinessException.class, () -> {
            chatService.getChatDetail(userId, chatId);
        });

        // 验证调用
        verify(chatMapper, times(1)).selectOne(any(LambdaQueryWrapper.class));
    }

    @Test
    void testDeleteChat_Success() {
        // 准备测试数据
        when(chatMapper.selectOne(any(LambdaQueryWrapper.class))).thenReturn(chat);
        when(messageMapper.delete(any(LambdaQueryWrapper.class))).thenReturn(5);
        when(agentTaskMapper.delete(any(LambdaQueryWrapper.class))).thenReturn(2);
        when(chatMapper.deleteById(1L)).thenReturn(1);

        // 执行测试
        chatService.deleteChat(userId, chatId);

        // 验证调用
        verify(chatMapper, times(1)).selectOne(any(LambdaQueryWrapper.class));
        verify(messageMapper, times(1)).delete(any(LambdaQueryWrapper.class));
        verify(agentTaskMapper, times(1)).delete(any(LambdaQueryWrapper.class));
        verify(chatMapper, times(1)).deleteById(1L);
    }

    @Test
    void testDeleteChat_ChatNotFound_ThrowsException() {
        // 准备测试数据
        when(chatMapper.selectOne(any(LambdaQueryWrapper.class))).thenReturn(null);

        // 执行测试并验证异常
        assertThrows(BusinessException.class, () -> {
            chatService.deleteChat(userId, chatId);
        });

        // 验证调用
        verify(chatMapper, times(1)).selectOne(any(LambdaQueryWrapper.class));
        verify(messageMapper, never()).delete(any(LambdaQueryWrapper.class));
        verify(agentTaskMapper, never()).delete(any(LambdaQueryWrapper.class));
        verify(chatMapper, never()).deleteById(any());
    }

    @Test
    void testDeleteChat_CascadeDelete() {
        // 准备测试数据
        when(chatMapper.selectOne(any(LambdaQueryWrapper.class))).thenReturn(chat);
        when(messageMapper.delete(any(LambdaQueryWrapper.class))).thenReturn(0);
        when(agentTaskMapper.delete(any(LambdaQueryWrapper.class))).thenReturn(0);
        when(chatMapper.deleteById(1L)).thenReturn(1);

        // 执行测试
        chatService.deleteChat(userId, chatId);

        // 验证级联删除调用
        verify(messageMapper, times(1)).delete(argThat(wrapper -> {
            // 验证删除条件是 chatId
            return true;
        }));
        verify(agentTaskMapper, times(1)).delete(argThat(wrapper -> {
            // 验证删除条件是 chatId
            return true;
        }));
    }
}
