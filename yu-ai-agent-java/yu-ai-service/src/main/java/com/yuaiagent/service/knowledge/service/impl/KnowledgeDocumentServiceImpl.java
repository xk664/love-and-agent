package com.yuaiagent.service.knowledge.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yuaiagent.common.exception.BusinessException;
import com.yuaiagent.service.chat.config.PythonServiceConfig;
import com.yuaiagent.service.knowledge.dto.DocumentCallbackRequest;
import com.yuaiagent.service.knowledge.dto.DocumentListRequest;
import com.yuaiagent.service.knowledge.dto.DocumentResponse;
import com.yuaiagent.service.knowledge.dto.DocumentUploadResponse;
import com.yuaiagent.service.knowledge.mapper.KnowledgeDocumentMapper;
import com.yuaiagent.service.knowledge.model.KnowledgeDocument;
import com.yuaiagent.service.knowledge.pgvector.mapper.EmbeddingMapper;
import com.yuaiagent.service.knowledge.service.KnowledgeDocumentService;
import com.yuaiagent.service.knowledge.util.FileContentExtractor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 知识库文档服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class KnowledgeDocumentServiceImpl implements KnowledgeDocumentService {

    private final KnowledgeDocumentMapper knowledgeDocumentMapper;
    private final EmbeddingMapper embeddingMapper;
    private final FileContentExtractor fileContentExtractor;
    private final PythonServiceConfig pythonServiceConfig;
    private final OkHttpClient okHttpClient;
    private final ObjectMapper objectMapper;

    /**
     * 上传文档
     *
     * @param userId 用户ID
     * @param file   上传的文件
     * @return 文档上传响应
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public DocumentUploadResponse uploadDocument(Long userId, MultipartFile file) {
        // 1. 校验文件非空
        if (file == null || file.isEmpty()) {
            throw new BusinessException(400, "上传文件不能为空");
        }

        // 2. 获取文件名并识别类型
        String originalFilename = file.getOriginalFilename();
        String fileType;
        try {
            fileType = fileContentExtractor.resolveFileType(originalFilename);
        } catch (IllegalArgumentException e) {
            throw new BusinessException(400, e.getMessage());
        }

        // 3. 提取文本内容
        String content;
        try {
            content = fileContentExtractor.extractContent(file, fileType);
        } catch (IOException e) {
            log.error("文件内容提取失败: filename={}, error={}", originalFilename, e.getMessage(), e);
            throw new BusinessException(500, "文件内容提取失败: " + e.getMessage());
        }

        // 4. 从文件名提取标题（去掉扩展名）
        String title = fileContentExtractor.extractTitle(originalFilename);

        // 5. 构建文档实体
        KnowledgeDocument document = new KnowledgeDocument();
        document.setUserId(userId);
        document.setTitle(title);
        document.setContent(content);
        document.setFileType(fileType);
        document.setStatus(0); // 待处理

        // 6. 保存到数据库
        knowledgeDocumentMapper.insert(document);

        log.info("文档上传成功: id={}, userId={}, title={}, fileType={}, contentLength={}",
                document.getId(), userId, title, fileType, content != null ? content.length() : 0);

        // 7. 异步调用 Python 向量化接口
        callPythonIndexAsync(document);

        // 8. 返回响应
        return DocumentUploadResponse.fromEntity(document);
    }

    /**
     * 分页查询当前用户的文档列表
     *
     * @param userId  用户ID
     * @param request 分页查询请求参数
     * @return 分页结果
     */

    @Override
    public Page<DocumentResponse> getDocuments(Long userId, DocumentListRequest request) {
        // 1. 构建分页对象
        Page<KnowledgeDocument> page = new Page<>(request.getPage(), request.getPageSize());

        // 2. 构建查询条件：仅查询当前用户的文档，按创建时间倒序
        LambdaQueryWrapper<KnowledgeDocument> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(KnowledgeDocument::getUserId, userId)
               .orderByDesc(KnowledgeDocument::getCreateTime);

        // 3. 执行分页查询
        Page<KnowledgeDocument> documentPage = knowledgeDocumentMapper.selectPage(page, wrapper);

        // 4. 转换为响应DTO
        Page<DocumentResponse> responsePage = new Page<>(
                documentPage.getCurrent(),
                documentPage.getSize(),
                documentPage.getTotal()
        );

        responsePage.setRecords(
                documentPage.getRecords().stream()
                        .map(DocumentResponse::fromEntity)
                        .collect(Collectors.toList())
        );

        log.info("查询文档列表: userId={}, page={}, pageSize={}, total={}",
                userId, request.getPage(), request.getPageSize(), responsePage.getTotal());

        return responsePage;
    }

    /**
     * 删除文档（软删除 + 删除向量）
     *
     * @param userId     用户ID
     * @param documentId 文档ID
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteDocument(Long userId, Long documentId) {
        // 1. 查询文档
        KnowledgeDocument document = knowledgeDocumentMapper.selectById(documentId);

        if (document == null) {
            throw new BusinessException(404, "文档不存在");
        }

        // 2. 校验文档归属
        if (!document.getUserId().equals(userId)) {
            throw new BusinessException(403, "无权删除此文档");
        }

        // 3. 软删除文档（@TableLogic 字段需要使用 UpdateWrapper 显式设置）
        LambdaUpdateWrapper<KnowledgeDocument> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.eq(KnowledgeDocument::getId, documentId)
                     .set(KnowledgeDocument::getIsDeleted, 1)
                     .set(KnowledgeDocument::getVectorDeleted, 0);
        knowledgeDocumentMapper.update(null, updateWrapper);

        log.info("文档软删除成功: documentId={}, title={}", documentId, document.getTitle());

        // 4. 尝试删除向量
        try {
            String collection = "doc_" + documentId;
            int deletedCount = embeddingMapper.deleteByCollection(collection);
            // 更新向量清理标记
            LambdaUpdateWrapper<KnowledgeDocument> vectorUpdateWrapper = new LambdaUpdateWrapper<>();
            vectorUpdateWrapper.eq(KnowledgeDocument::getId, documentId)
                               .set(KnowledgeDocument::getVectorDeleted, 1);
            knowledgeDocumentMapper.update(null, vectorUpdateWrapper);
            log.info("向量删除成功: documentId={}, collection={}, deletedCount={}", documentId, collection, deletedCount);
        } catch (Exception e) {
            // 向量删除失败不影响软删除结果，由定时任务补偿
            log.warn("向量删除失败，将由定时任务补偿: documentId={}, error={}", documentId, e.getMessage());
        }
    }

    /**
     * 清理孤立向量（定时任务调用）
     * 扫描已软删除但向量未清理的文档，删除对应的向量
     *
     * @return 清理的文档数量
     */
    @Override
    public int cleanupOrphanVectors() {
        // 1. 查询已软删除但向量未清理的文档
        LambdaQueryWrapper<KnowledgeDocument> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(KnowledgeDocument::getIsDeleted, 1)
               .eq(KnowledgeDocument::getVectorDeleted, 0)
               .last("LIMIT 100"); // 每次最多处理100条

        List<KnowledgeDocument> documents = knowledgeDocumentMapper.selectList(wrapper);

        if (documents.isEmpty()) {
            log.debug("没有需要清理的孤立向量");
            return 0;
        }

        log.info("发现 {} 个文档需要清理向量", documents.size());

        // 2. 逐个删除向量
        int successCount = 0;
        for (KnowledgeDocument doc : documents) {
            try {
                String collection = "doc_" + doc.getId();
                int deletedCount = embeddingMapper.deleteByCollection(collection);

                // 3. 更新标记（使用 UpdateWrapper 避免 @TableLogic 字段干扰）
                LambdaUpdateWrapper<KnowledgeDocument> updateWrapper = new LambdaUpdateWrapper<>();
                updateWrapper.eq(KnowledgeDocument::getId, doc.getId())
                             .set(KnowledgeDocument::getVectorDeleted, 1);
                knowledgeDocumentMapper.update(null, updateWrapper);
                successCount++;

                log.info("定时清理向量成功: documentId={}, collection={}, deletedCount={}",
                        doc.getId(), collection, deletedCount);
            } catch (Exception e) {
                log.error("定时清理向量失败: documentId={}, error={}", doc.getId(), e.getMessage());
            }
        }

        log.info("向量清理任务完成: 总数={}, 成功={}", documents.size(), successCount);
        return successCount;
    }

    /**
     * 异步调用 Python 向量化接口
     * Python 端暂未实现，先打日志预留
     */
    private void callPythonIndexAsync(KnowledgeDocument document) {
        try {
            String url = pythonServiceConfig.getBaseUrl() + pythonServiceConfig.getEndpoints().getKnowledgeIndex();

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("document_id", document.getId());
            requestBody.put("user_id", document.getUserId());
            requestBody.put("title", document.getTitle());
            requestBody.put("content", document.getContent());
            requestBody.put("file_type", document.getFileType());

            String jsonBody = objectMapper.writeValueAsString(requestBody);

            Request httpRequest = new Request.Builder()
                    .url(url)
                    .addHeader("Content-Type", "application/json")
                    .post(RequestBody.create(jsonBody, MediaType.parse("application/json")))
                    .build();

            // 异步调用，不阻塞主流程
            okHttpClient.newCall(httpRequest).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    log.warn("调用 Python 向量化接口失败（Python 端可能尚未实现）: documentId={}, error={}",
                            document.getId(), e.getMessage());
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        log.info("Python 向量化接口调用成功: documentId={}", document.getId());
                    } else {
                        log.warn("Python 向量化接口返回错误: documentId={}, code={}", document.getId(), response.code());
                    }
                    response.close();
                }
            });

            log.info("已发起 Python 向量化请求: documentId={}, url={}", document.getId(), url);
        } catch (Exception e) {
            // 向量化调用失败不影响文档上传结果
            log.warn("发起 Python 向量化请求异常（Python 端可能尚未实现）: documentId={}, error={}",
                    document.getId(), e.getMessage());
        }
    }

    /**
     * 处理 Python 向量化回调
     * 更新文档状态（1-已向量化 2-处理失败）
     *
     * @param request 回调请求
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void handleCallback(DocumentCallbackRequest request) {
        // 1. 查询文档
        LambdaQueryWrapper<KnowledgeDocument> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(KnowledgeDocument::getId, request.getDocumentId());

        KnowledgeDocument document = knowledgeDocumentMapper.selectOne(wrapper);

        if (document == null) {
            throw new BusinessException(404, "文档不存在: id=" + request.getDocumentId());
        }

        // 2. 更新状态
        document.setStatus(request.getStatus());
        knowledgeDocumentMapper.updateById(document);

        if (request.getStatus() == 1) {
            log.info("文档向量化完成: documentId={}, title={}", document.getId(), document.getTitle());
        } else {
            log.warn("文档向量化失败: documentId={}, title={}, message={}",
                    document.getId(), document.getTitle(), request.getMessage());
        }
    }

}
