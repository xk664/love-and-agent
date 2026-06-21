"""
Knowledge Base API - 知识库文档向量化接口
"""
import asyncio

import httpx
from fastapi import APIRouter

from app.ai.llm.dashscope_client import dashscope_client
from app.ai.rag.retriever import hybrid_retrieve
from app.ai.rag.text_splitter import split_text
from app.ai.rag.vector_store import vector_store
from app.core.config import settings
from app.core.logging import get_logger
from app.models.knowledge import (
    KnowledgeIndexRequest,
    KnowledgeIndexResponse,
    KnowledgeCallbackRequest,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResultItem,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/internal/knowledge", tags=["knowledge"])



@router.post("/index", response_model=KnowledgeIndexResponse)
async def index_document(request: KnowledgeIndexRequest):
    """
    文档向量化接口

    接收 Java 端发送的文档内容，异步执行向量化：
    1. 将文档内容分块
    2. 批量生成 embedding
    3. 存储到 PgVector
    4. 回调 Java 通知完成/失败
    """
    logger.info(
        f"Knowledge index request: document_id={request.document_id}, "
        f"user_id={request.user_id}, title={request.title}, "
        f"file_type={request.file_type}, content_length={len(request.content)}"
    )

    # 异步执行向量化，立即返回
    asyncio.create_task(_vectorize_document(request))

    return KnowledgeIndexResponse(
        code=200,
        message="向量化任务已提交",
        data={"document_id": request.document_id}
    )


async def _vectorize_document(request: KnowledgeIndexRequest):
    """
    后台向量化任务

    流程：分块 → 生成 embedding → 存 PgVector → 回调 Java
    """
    document_id = request.document_id
    collection = f"doc_{document_id}"

    try:
        # 1. 文本分块
        chunks = split_text(request.content)
        if not chunks:
            logger.warning(f"Document {document_id} has no content to vectorize")
            await _callback_java(document_id, status=2, message="文档内容为空，无法向量化")
            return

        logger.info(f"Document {document_id} split into {len(chunks)} chunks")

        # 2. 批量生成 embedding
        embeddings = dashscope_client.get_embeddings_batch(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings for document {document_id}")

        # 3. 逐条存入 PgVector
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            metadata = {
                "document_id": document_id,
                "user_id": request.user_id,
                "title": request.title,
                "file_type": request.file_type,
                "chunk_index": i,
            }
            await vector_store.add_embedding(
                content=chunk,
                embedding=embedding,
                metadata=metadata,
                collection=collection,
            )

        logger.info(f"Stored {len(chunks)} embeddings for document {document_id} in collection '{collection}'")

        # 4. 回调 Java 通知成功
        await _callback_java(document_id, status=1)

    except Exception as e:
        logger.error(f"Vectorization failed for document {document_id}: {str(e)}")
        # 回调 Java 通知失败
        await _callback_java(document_id, status=2, message=str(e))


async def _callback_java(document_id: int, status: int, message: str = None):
    """
    回调 Java 端通知向量化结果

    Args:
        document_id: 文档ID
        status: 状态（1-已向量化 2-处理失败）
        message: 可选消息（失败时的错误信息）
    """
    callback_url = settings.callback.knowledge_callback_url
    callback_token = settings.callback.CALLBACK_TOKEN

    if not callback_url:
        logger.warning("Callback URL not configured, skipping callback")
        return

    payload = KnowledgeCallbackRequest(
        document_id=document_id,
        status=status,
        message=message,
    ).model_dump(by_alias=True)

    headers = {"Content-Type": "application/json"}
    if callback_token:
        headers["X-Internal-Token"] = callback_token

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(callback_url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.info(f"Callback succeeded: document_id={document_id}, status={status}")
            else:
                logger.warning(
                    f"Callback failed: document_id={document_id}, "
                    f"status_code={response.status_code}, body={response.text}"
                )
    except Exception as e:
        logger.error(f"Callback error: document_id={document_id}, error={str(e)}")


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    """
    知识库检索接口

    执行流程：查询重写 → 向量+关键词混合检索 → RRF融合排序 → 返回 top_k
    """
    logger.info(
        f"Knowledge search: query='{request.query}', "
        f"user_id={request.user_id}, top_k={request.top_k}"
    )

    try:
        results = await hybrid_retrieve(
            query=request.query,
            user_id=request.user_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )

        items = [
            KnowledgeSearchResultItem(
                id=r["id"],
                content=r["content"],
                metadata=r["metadata"],
                similarity=r["similarity"],
            )
            for r in results
        ]

        logger.info(f"Knowledge search returned {len(items)} results")
        return KnowledgeSearchResponse(code=200, message="success", data=items)

    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        return KnowledgeSearchResponse(code=500, message=str(e), data=[])
