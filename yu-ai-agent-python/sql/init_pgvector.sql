-- ============================================================
-- PgVector 向量数据库初始化脚本
-- 数据库: PostgreSQL + pgvector 扩展
-- ============================================================

-- 创建数据库（如果不存在）
-- 注意：需要在 postgres 默认数据库下执行此语句
-- CREATE DATABASE love_and_agent;

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 向量嵌入表
-- ============================================================
DROP TABLE IF EXISTS embeddings;
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536) NOT NULL,
    collection VARCHAR(255) DEFAULT 'default',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引：按 collection 查询加速
CREATE INDEX idx_embeddings_collection ON embeddings (collection);

-- 索引：向量相似度搜索加速（HNSW 算法，余弦距离）
CREATE INDEX idx_embeddings_vector ON embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================
-- 表和列注释
-- ============================================================
COMMENT ON TABLE embeddings IS '知识库文档向量嵌入表';
COMMENT ON COLUMN embeddings.content IS '文本内容（文档分块后的文本）';
COMMENT ON COLUMN embeddings.metadata IS '元数据 JSON（document_id, user_id, title, file_type, chunk_index）';
COMMENT ON COLUMN embeddings.embedding IS '向量嵌入（1536 维，text-embedding-v2 模型输出）';
COMMENT ON COLUMN embeddings.collection IS '集合名称，格式 doc_{document_id}，用于按文档隔离';
