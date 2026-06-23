"""
PgVector 向量存储服务
操作 embeddings 表（使用已有的 VectorStoreManager 表结构）
"""

import json
import logging

import asyncpg

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_dsn() -> str:
    """构建 PostgreSQL 连接字符串"""
    cfg = settings.pgvector
    pwd = f":{cfg.PGVECTOR_PASSWORD}" if cfg.PGVECTOR_PASSWORD else ""
    return f"postgresql://{cfg.PGVECTOR_USER}{pwd}@{cfg.PGVECTOR_HOST}:{cfg.PGVECTOR_PORT}/{cfg.PGVECTOR_DATABASE}"


async def _get_conn() -> asyncpg.Connection:
    """获取数据库连接（5秒超时）"""
    return await asyncpg.connect(_get_dsn(), timeout=5)


async def add_chunks(
    document_id: int,
    chunks: list[str],
    embeddings: list[list[float]],
    metadata: dict | None = None,
):
    """
    批量插入向量块到 embeddings 表

    document_id 和 chunk_index 存储在 metadata JSON 中
    """
    if not chunks:
        return

    conn = await _get_conn()
    try:
        records = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
            meta = dict(metadata or {})
            meta["document_id"] = document_id
            meta["chunk_index"] = i
            records.append((
                chunk,
                json.dumps(meta),
                embedding_str,
                "knowledge",
            ))

        logger.info(f"Inserting {len(records)} chunks for document {document_id} into {_get_dsn()}")

        await conn.executemany(
            """
            INSERT INTO embeddings (content, metadata, embedding, collection)
            VALUES ($1, $2::jsonb, $3::vector, $4)
            """,
            records,
        )
        logger.info(f"Inserted {len(records)} chunks for document {document_id}")

        # 验证插入
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM embeddings WHERE metadata->>'document_id' = $1",
            str(document_id),
        )
        logger.info(f"Verified: {count} chunks exist for document {document_id}")
    finally:
        await conn.close()


async def delete_by_document(document_id: int) -> int:
    """删除指定文档的所有向量块"""
    conn = await _get_conn()
    try:
        result = await conn.execute(
            "DELETE FROM embeddings WHERE collection = 'knowledge' AND metadata->>'document_id' = $1",
            str(document_id),
        )
        count = int(result.split()[-1])
        if count > 0:
            logger.info(f"Deleted {count} chunks for document {document_id}")
        return count
    except Exception as e:
        logger.warning(f"PgVector delete failed for document {document_id}: {e}")
        return 0
    finally:
        await conn.close()


async def cleanup_orphaned() -> int:
    """
    清理孤立向量（metadata 中的 document_id 不在 knowledge_document 表中的记录）
    """
    conn = await _get_conn()
    try:
        result = await conn.execute("""
            DELETE FROM embeddings
            WHERE collection = 'knowledge'
              AND (metadata->>'document_id')::bigint NOT IN (
                  SELECT id FROM knowledge_document WHERE is_deleted = false
              )
        """)
        count = int(result.split()[-1])
        if count > 0:
            logger.info(f"Cleaned up {count} orphaned vectors")
        return count
    finally:
        await conn.close()
