package com.yuaiagent.service.knowledge.dto;

import lombok.Data;

/**
 * 文档向量化回调请求
 * Python 向量化完成后回调 Java 更新文档状态
 */
@Data
public class DocumentCallbackRequest {

    /**
     * 文档ID
     */
    private Long documentId;

    /**
     * 状态：1-已向量化 2-处理失败
     */
    private Integer status;

    /**
     * 可选消息（失败时的错误信息）
     */
    private String message;

}
