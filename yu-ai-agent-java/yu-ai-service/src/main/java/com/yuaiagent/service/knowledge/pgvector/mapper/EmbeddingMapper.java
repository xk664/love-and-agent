package com.yuaiagent.service.knowledge.pgvector.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * PgVector Embedding Mapper 接口
 * 用于操作 PostgreSQL 中的 embeddings 表
 */
@Mapper
public interface EmbeddingMapper {

    /**
     * 删除指定 collection 的所有向量
     *
     * @param collection 集合名称，格式：doc_{documentId}
     * @return 删除的记录数
     */
    int deleteByCollection(@Param("collection") String collection);

    /**
     * 统计指定 collection 的向量数量
     *
     * @param collection 集合名称
     * @return 向量数量
     */
    int countByCollection(@Param("collection") String collection);
}
