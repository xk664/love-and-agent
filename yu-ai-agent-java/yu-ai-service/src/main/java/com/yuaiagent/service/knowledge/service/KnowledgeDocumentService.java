package com.yuaiagent.service.knowledge.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yuaiagent.service.knowledge.dto.DocumentCallbackRequest;
import com.yuaiagent.service.knowledge.dto.DocumentListRequest;
import com.yuaiagent.service.knowledge.dto.DocumentResponse;
import com.yuaiagent.service.knowledge.dto.DocumentUploadResponse;
import org.springframework.web.multipart.MultipartFile;

/**
 * 知识库文档服务接口
 */
public interface KnowledgeDocumentService {

    /**
     * 上传文档
     *
     * @param userId 用户ID
     * @param file   上传的文件
     * @return 文档上传响应
     */
    DocumentUploadResponse uploadDocument(Long userId, MultipartFile file);

    /**
     * 分页查询当前用户的文档列表
     *
     * @param userId  用户ID
     * @param request 分页查询请求参数
     * @return 分页结果
     */
    Page<DocumentResponse> getDocuments(Long userId, DocumentListRequest request);

    /**
     * 删除文档（软删除 + 删除向量）
     *
     * @param userId     用户ID
     * @param documentId 文档ID
     */
    void deleteDocument(Long userId, Long documentId);

    /**
     * 处理 Python 向量化回调
     * 更新文档状态（1-已向量化 2-处理失败）
     *
     * @param request 回调请求
     */
    void handleCallback(DocumentCallbackRequest request);

    /**
     * 清理孤立向量（定时任务调用）
     * 扫描已软删除但向量未清理的文档，删除对应的向量
     *
     * @return 清理的文档数量
     */
    int cleanupOrphanVectors();

}
