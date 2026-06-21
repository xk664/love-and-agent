package com.yuaiagent.service.knowledge.pgvector.model;

import lombok.Data;

/**
 * PgVector Embedding 实体类
 * 对应 PostgreSQL 中的 embeddings 表
 */
@Data
public class Embedding {

    /**
     * 主键ID
     */
    private Integer id;

    /**
     * 文本内容
     */
    private String content;

    /**
     * 元数据（JSON格式）
     */
    private String metadata;

    /**
     * 向量（不映射到Java对象，由数据库处理）
     */
    // private float[] embedding;

    /**
     * 集合名称，格式：doc_{documentId}
     */
    private String collection;
}
