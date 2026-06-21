package com.yuaiagent.service.knowledge.controller;

import com.yuaiagent.common.exception.BusinessException;
import com.yuaiagent.common.response.Result;
import com.yuaiagent.service.knowledge.dto.DocumentCallbackRequest;
import com.yuaiagent.service.knowledge.service.KnowledgeDocumentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

/**
 * 知识库内部回调控制器
 * Python 向量化完成后回调此接口更新文档状态
 */
@Slf4j
@Tag(name = "知识库内部回调", description = "Python 向量化完成回调接口（仅内部调用）")
@RestController
@RequestMapping("/api/v1/internal/callback/knowledge")
@RequiredArgsConstructor
public class InternalKnowledgeCallbackController {

    private final KnowledgeDocumentService knowledgeDocumentService;

    @Value("${internal.callback.token:}")
    private String internalToken;

    /**
     * 文档向量化完成回调
     * Python 向量化完成后调用此接口更新文档状态
     *
     * @param token   内部认证 Token（X-Internal-Token 请求头）
     * @param request 回调请求
     * @return 操作结果
     */
    @Operation(summary = "文档向量化回调", description = "Python 向量化完成后回调更新文档状态")
    @PostMapping("/document")
    public Result<Void> handleDocumentCallback(
            @RequestHeader(value = "X-Internal-Token", required = false) String token,
            @Valid @RequestBody DocumentCallbackRequest request) {
        // 1. 校验内部 Token
        validateInternalToken(token);

        // 2. 参数校验
        if (request.getDocumentId() == null) {
            throw new BusinessException(400, "documentId 不能为空");
        }
        if (request.getStatus() == null || (request.getStatus() != 1 && request.getStatus() != 2)) {
            throw new BusinessException(400, "status 必须为 1（已向量化）或 2（处理失败）");
        }

        log.info("收到文档向量化回调: documentId={}, status={}, message={}",
                request.getDocumentId(), request.getStatus(), request.getMessage());

        // 3. 处理回调
        knowledgeDocumentService.handleCallback(request);

        return Result.success();
    }

    /**
     * 校验内部 Token
     */
    private void validateInternalToken(String token) {
        // 如果没有配置 Token，跳过校验（开发环境）
        if (!StringUtils.hasText(internalToken)) {
            return;
        }

        if (!StringUtils.hasText(token) || !internalToken.equals(token)) {
            throw new BusinessException(401, "无效的内部认证 Token");
        }
    }

}
