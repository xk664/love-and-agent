package com.yuaiagent.service.chat.controller;

import com.yuaiagent.common.config.JwtAuthInterceptor;
import com.yuaiagent.common.response.PageResponse;
import com.yuaiagent.common.response.Result;
import com.yuaiagent.service.chat.dto.MessageListRequest;
import com.yuaiagent.service.chat.dto.MessageResponse;
import com.yuaiagent.service.chat.service.MessageService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 消息控制器
 */
@Tag(name = "消息管理", description = "消息管理相关接口")
@RestController
@RequestMapping("/api/v1/chat/{chatId}/messages")
@RequiredArgsConstructor
public class MessageController {

    private final MessageService messageService;

    /**
     * 获取消息历史
     *
     * @param request  HTTP请求（用于获取当前用户ID）
     * @param chatId   会话ID
     * @param page     页码
     * @param pageSize 每页数量
     * @return 分页消息列表
     */
    @Operation(summary = "获取消息历史", description = "分页查询会话的消息历史，按时间倒序返回（最新消息在前）")
    @GetMapping
    public Result<PageResponse<MessageResponse>> getMessageHistory(
            HttpServletRequest request,
            @PathVariable String chatId,
            @RequestParam(value = "page", defaultValue = "1") Integer page,
            @RequestParam(value = "page_size", defaultValue = "20") Integer pageSize) {
        Long userId = getUserId(request);

        // 构建查询请求
        MessageListRequest messageListRequest = new MessageListRequest();
        messageListRequest.setPage(page);
        messageListRequest.setPageSize(pageSize);

        PageResponse<MessageResponse> response = messageService.getMessageHistory(userId, chatId, messageListRequest);
        return Result.success(response);
    }

    /**
     * 从 request attribute 获取用户ID
     */
    private Long getUserId(HttpServletRequest request) {
        return (Long) request.getAttribute(JwtAuthInterceptor.REQUEST_USER_ID);
    }

}
