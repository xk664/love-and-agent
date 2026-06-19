package com.yuaiagent.service.chat.controller;

import com.yuaiagent.common.config.JwtAuthInterceptor;
import com.yuaiagent.common.response.PageResponse;
import com.yuaiagent.common.response.Result;
import com.yuaiagent.service.chat.dto.ChatListRequest;
import com.yuaiagent.service.chat.dto.ChatResponse;
import com.yuaiagent.service.chat.dto.CreateChatRequest;
import com.yuaiagent.service.chat.service.ChatService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 会话控制器
 */
@Tag(name = "会话管理", description = "会话管理相关接口")
@RestController
@RequestMapping("/api/v1/chat")
@RequiredArgsConstructor
public class ChatController {

    private final ChatService chatService;

    /**
     * 创建会话
     *
     * @param request HTTP请求（用于获取当前用户ID）
     * @param createChatRequest 创建会话请求
     * @return 会话信息
     */
    @Operation(summary = "创建会话", description = "创建新的会话，love_app类型必须选择情感状态")
    @PostMapping("/create")
    public Result<ChatResponse> createChat(
            HttpServletRequest request,
            @Valid @RequestBody CreateChatRequest createChatRequest) {
        Long userId = getUserId(request);
        ChatResponse response = chatService.createChat(userId, createChatRequest);
        return Result.success(response);
    }

    /**
     * 获取会话列表
     *
     * @param request HTTP请求（用于获取当前用户ID）
     * @param page 页码
     * @param pageSize 每页数量
     * @param appType 应用类型筛选（可选）
     * @return 分页会话列表
     */
    @Operation(summary = "获取会话列表", description = "分页查询当前用户的会话列表，支持按应用类型筛选")
    @GetMapping("/list")
    public Result<PageResponse<ChatResponse>> listChats(
            HttpServletRequest request,
            @RequestParam(value = "page", defaultValue = "1") Integer page,
            @RequestParam(value = "page_size", defaultValue = "10") Integer pageSize,
            @RequestParam(value = "app_type", required = false) String appType) {
        Long userId = getUserId(request);

        // 构建查询请求
        ChatListRequest chatListRequest = new ChatListRequest();
        chatListRequest.setPage(page);
        chatListRequest.setPageSize(pageSize);
        chatListRequest.setAppType(appType);

        PageResponse<ChatResponse> response = chatService.listChats(userId, chatListRequest);
        return Result.success(response);
    }

    /**
     * 获取会话详情
     *
     * @param request HTTP请求（用于获取当前用户ID）
     * @param chatId 会话ID
     * @return 会话详情
     */
    @Operation(summary = "获取会话详情", description = "根据会话ID获取会话详细信息")
    @GetMapping("/{chatId}")
    public Result<ChatResponse> getChatDetail(
            HttpServletRequest request,
            @PathVariable String chatId) {
        Long userId = getUserId(request);
        ChatResponse response = chatService.getChatDetail(userId, chatId);
        return Result.success(response);
    }

    /**
     * 删除会话（软删除）
     * 级联软删除该会话下所有消息和关联的 agent_task
     *
     * @param request HTTP请求（用于获取当前用户ID）
     * @param chatId 会话ID
     * @return 删除结果
     */
    @Operation(summary = "删除会话", description = "删除会话并级联软删除该会话下所有消息和关联的 agent_task")
    @DeleteMapping("/{chatId}")
    public Result<Void> deleteChat(
            HttpServletRequest request,
            @PathVariable String chatId) {
        Long userId = getUserId(request);
        chatService.deleteChat(userId, chatId);
        return Result.success();
    }

    /**
     * 从 request attribute 获取用户ID
     */
    private Long getUserId(HttpServletRequest request) {
        return (Long) request.getAttribute(JwtAuthInterceptor.REQUEST_USER_ID);
    }

}
