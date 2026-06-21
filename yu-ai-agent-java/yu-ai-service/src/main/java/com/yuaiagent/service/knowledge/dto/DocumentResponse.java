package com.yuaiagent.service.knowledge.dto;

import com.yuaiagent.service.knowledge.model.KnowledgeDocument;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 文档详情响应
 */
@Data
public class DocumentResponse {

    /**
     * 文档ID
     */
    private Long id;

    /**
     * 文档标题
     */
    private String title;

    /**
     * 文件类型
     */
    private String fileType;

    /**
     * 状态：0-待处理 1-已向量化 2-处理失败
     */
    private Integer status;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;

    /**
     * 从实体转换为响应对象
     */
    public static DocumentResponse fromEntity(KnowledgeDocument document) {
        DocumentResponse response = new DocumentResponse();
        response.setId(document.getId());
        response.setTitle(document.getTitle());
        response.setFileType(document.getFileType());
        response.setStatus(document.getStatus());
        response.setCreateTime(document.getCreateTime());
        response.setUpdateTime(document.getUpdateTime());
        return response;
    }

}
