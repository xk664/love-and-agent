"""
Knowledge Retriever - 查询重写 + 混合检索
"""
from typing import List, Optional

from app.ai.llm.dashscope_client import dashscope_client
from app.ai.rag.vector_store import vector_store
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

REWRITE_SYSTEM_PROMPT = """你是一个搜索查询优化器。你的任务是将用户查询改写为更适合语义搜索的形式。
要求：
1. 保留核心意图，不要改变原意
2. 扩展同义词和相关概念
3. 输出 2-3 个不同表述，每行一个
4. 不要编号，不要加任何前缀"""


async def rewrite_query(query: str) -> List[str]:
    """
    用 LLM 改写查询，生成多个语义等价表述，提高检索召回率

    Args:
        query: 原始用户查询

    Returns:
        改写后的查询列表（包含原始 query）
    """
    try:
        prompt = f"原始查询：{query}"
        result = dashscope_client.generate_text(
            prompt=prompt,
            system_prompt=REWRITE_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=200,
        )

        # 解析：按行分割，过滤空行
        rewritten = [line.strip() for line in result.strip().split("\n") if line.strip()]

        # 去重（忽略大小写）
        seen = set()
        unique = []
        for q in [query] + rewritten:
            lower = q.lower()
            if lower not in seen:
                seen.add(lower)
                unique.append(q)

        logger.info(f"Query rewrite: '{query}' -> {unique}")
        return unique

    except Exception as e:
        logger.warning(f"Query rewrite failed, using original query: {e}")
        return [query]


async def hybrid_retrieve(
    query: str,
    user_id: int,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
) -> List[dict]:
    """
    完整检索流程：查询重写 → 多路混合检索 → 去重融合

    Args:
        query: 用户原始查询
        user_id: 用户 ID，限定检索范围
        top_k: 返回结果数量
        similarity_threshold: 向量相似度阈值

    Returns:
        检索结果列表，每项包含 id, content, metadata, similarity
    """
    top_k = top_k or settings.rag.RAG_TOP_K
    similarity_threshold = similarity_threshold or settings.rag.RAG_SIMILARITY_THRESHOLD

    # Step 1: 查询重写
    queries = await rewrite_query(query)

    # Step 2: 为每个改写 query 生成 embedding
    query_embeddings = []
    for q in queries:
        try:
            embedding = dashscope_client.get_embedding(q)
            query_embeddings.append((q, embedding))
        except Exception as e:
            logger.warning(f"Embedding failed for query '{q}': {e}")

    if not query_embeddings:
        logger.error("All query embeddings failed")
        return []

    # Step 3: 对每个 query 做混合检索
    all_results = {}
    for q, embedding in query_embeddings:
        try:
            results = await vector_store.hybrid_search(
                query=q,
                query_embedding=embedding,
                user_id=user_id,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )
            for item in results:
                chunk_id = item["id"]
                # 去重：同一 chunk 取最高分
                if chunk_id not in all_results or item["similarity"] > all_results[chunk_id]["similarity"]:
                    all_results[chunk_id] = item
        except Exception as e:
            logger.warning(f"Hybrid search failed for query '{q}': {e}")

    # Step 4: 按 similarity 降序，取 top_k
    final = sorted(all_results.values(), key=lambda x: x["similarity"], reverse=True)[:top_k]

    logger.info(f"Hybrid retrieve: query='{query}', user_id={user_id}, results={len(final)}")
    return final
