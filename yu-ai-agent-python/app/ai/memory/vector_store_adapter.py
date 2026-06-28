"""
向量存储适配器
将 VectorStoreManager 适配为长期记忆的接口
"""

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.database import async_session
from app.ai.rag.vector_store import vector_store

logger = get_logger(__name__)


class MemoryVectorStoreAdapter:
    """
    向量存储适配器
    将 VectorStoreManager 的接口适配为长期记忆所需的方法
    支持用户隔离：在SQL查询时按user_id过滤
    """

    def __init__(self, user_id: int, collection: str = "memory"):
        """
        初始化适配器

        Args:
            user_id: 用户ID
            collection: 向量集合名称
        """
        self.user_id = user_id
        self.collection = collection
        self._store = vector_store

    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> List[int]:
        """
        添加文本到向量存储

        Args:
            texts: 文本列表
            metadatas: 元数据列表

        Returns:
            向量ID列表
        """
        if not texts:
            logger.debug("add_texts: texts为空，跳过")
            return []

        # 准备元数据
        if metadatas is None:
            metadatas = [{}] * len(texts)

        # 为每个metadata添加user_id
        for meta in metadatas:
            meta["user_id"] = self.user_id

        # 生成嵌入向量
        logger.info(f"add_texts: 开始生成嵌入向量, texts数量={len(texts)}")
        embeddings = await self._get_embeddings(texts)
        logger.info(f"add_texts: 嵌入向量生成完成, embeddings数量={len(embeddings)}")

        if not embeddings:
            logger.warning("add_texts: 嵌入向量为空，跳过存储")
            return []

        # 存储到PgVector
        ids = []
        for i, (text_content, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
            try:
                embedding_id = await self._store.add_embedding(
                    content=text_content,
                    embedding=embedding,
                    metadata=metadata,
                    collection=self.collection
                )
                ids.append(embedding_id)
                logger.debug(f"add_texts: 添加向量 {i+1}/{len(texts)}, id={embedding_id}")
            except Exception as e:
                logger.error(f"add_texts: 添加向量失败 [{i+1}/{len(texts)}]: {e}")

        logger.info(f"add_texts: 完成, 成功添加 {len(ids)}/{len(texts)} 个向量到集合 '{self.collection}'")
        return ids

    async def similarity_search(
        self,
        query: str,
        k: int = 3,
        filter: Optional[dict] = None,
    ) -> List[dict]:
        """
        语义相似度搜索（支持用户隔离）

        Args:
            query: 查询文本
            k: 返回数量
            filter: 过滤条件，支持 {"user_id": int}

        Returns:
            相似文档列表
        """
        # 生成查询向量
        query_embedding = await self._get_embeddings([query])
        if not query_embedding:
            return []

        # 使用用户隔离的搜索
        try:
            results = await self._search_with_user_filter(
                query_embedding=query_embedding[0],
                k=k
            )

            return [
                {
                    "content": r["content"],
                    "metadata": r.get("metadata", {}),
                    "score": r.get("similarity", 0)
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"语义搜索失败: {e}")
            return []

    async def _search_with_user_filter(
        self,
        query_embedding: List[float],
        k: int = 3,
        similarity_threshold: float = 0.5
    ) -> List[dict]:
        """
        按用户ID过滤的向量搜索

        Args:
            query_embedding: 查询向量
            k: 返回数量
            similarity_threshold: 相似度阈值

        Returns:
            搜索结果列表
        """
        async with async_session() as session:
            query = text("""
                SELECT
                    id,
                    content,
                    metadata,
                    1 - (embedding <=> :query_embedding) AS similarity
                FROM embeddings
                WHERE collection = :collection
                  AND metadata->>'user_id' = :user_id
                  AND 1 - (embedding <=> :query_embedding) >= :threshold
                ORDER BY embedding <=> :query_embedding
                LIMIT :k
            """)

            result = await session.execute(
                query,
                {
                    "query_embedding": str(query_embedding),
                    "collection": self.collection,
                    "user_id": str(self.user_id),
                    "threshold": similarity_threshold,
                    "k": k
                }
            )

            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "content": row[1],
                    "metadata": row[2],
                    "similarity": float(row[3])
                }
                for row in rows
            ]

    async def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        获取文本的嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        try:
            from app.ai.llm.dashscope_client import dashscope_client
            logger.info(f"_get_embeddings: 调用 dashscope_client.get_embeddings_batch, texts数量={len(texts)}")
            embeddings = dashscope_client.get_embeddings_batch(texts)
            logger.info(f"_get_embeddings: 成功获取 {len(embeddings)} 个嵌入向量")
            return embeddings
        except Exception as e:
            logger.error(f"_get_embeddings: 获取嵌入向量失败: {e}")
            return []


def get_memory_vector_store(user_id: int) -> MemoryVectorStoreAdapter:
    """
    获取用户的记忆向量存储实例

    Args:
        user_id: 用户ID

    Returns:
        MemoryVectorStoreAdapter实例
    """
    return MemoryVectorStoreAdapter(user_id=user_id, collection="memory")
