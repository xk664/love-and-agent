package com.yuaiagent.service.knowledge.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yuaiagent.common.config.JwtAuthInterceptor;
import com.yuaiagent.common.response.Result;
import com.yuaiagent.service.knowledge.dto.DocumentListRequest;
import com.yuaiagent.service.knowledge.dto.DocumentResponse;
import com.yuaiagent.service.knowledge.dto.DocumentUploadResponse;
import com.yuaiagent.service.knowledge.service.KnowledgeDocumentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

/**
 * 知识库管理控制器
 */
@Tag(name = "知识库管理", description = "知识库文档管理相关接口")
@RestController
@RequestMapping("/api/v1/knowledge")
@RequiredArgsConstructor
public class KnowledgeController {

    private final KnowledgeDocumentService knowledgeDocumentService;

    /**
     * 上传文档
     * 支持 .md / .pdf / .txt 格式
     * 文档内容存储在数据库中，标题自动从文件名提取
     *
     * @param request HTTP请求（用于获取当前用户ID）
     * @param file    上传的文件
     * @return 文档信息
     */
    @Operation(summary = "上传文档", description = "上传知识库文档，支持 .md / .pdf / .txt 格式，标题自动从文件名提取")
    @PostMapping("/document")
    public Result<DocumentUploadResponse> uploadDocument(
            HttpServletRequest request,
            @RequestParam("file") MultipartFile file) {
        Long userId = getUserId(request);
        DocumentUploadResponse response = knowledgeDocumentService.uploadDocument(userId, file);
        return Result.success(response);
    }

    /**
     * 获取文档列表
     * 分页查询当前用户的文档列表，按创建时间倒序
     *
     * @param request   HTTP请求（用于获取当前用户ID）
     * @param listRequest 分页查询参数
     * @return 文档列表分页结果
     */
    @Operation(summary = "获取文档列表", description = "分页查询当前用户的文档列表，按创建时间倒序")
    @GetMapping("/documents")
    public Result<Page<DocumentResponse>> getDocuments(
            HttpServletRequest request,
            DocumentListRequest listRequest) {
        Long userId = getUserId(request);
        Page<DocumentResponse> response = knowledgeDocumentService.getDocuments(userId, listRequest);
        return Result.success(response);
    }

    /**
     * 删除文档
     * 软删除文档并清理对应的向量
     *
     * @param request    HTTP请求（用于获取当前用户ID）
     * @param documentId 文档ID
     * @return 操作结果
     */
    @Operation(summary = "删除文档", description = "删除知识库文档（软删除），同时清理对应的向量")
    @DeleteMapping("/document/{id}")
    public Result<Void> deleteDocument(
            HttpServletRequest request,
            @PathVariable("id") Long documentId) {
        Long userId = getUserId(request);
        knowledgeDocumentService.deleteDocument(userId, documentId);
        return Result.success();
    }

    /**
     * 从 request attribute 获取用户ID
     */
    private Long getUserId(HttpServletRequest request) {
        return (Long) request.getAttribute(JwtAuthInterceptor.REQUEST_USER_ID);
    }

}
