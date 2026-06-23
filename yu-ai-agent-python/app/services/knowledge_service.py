"""
知识库服务
处理文档上传、文本提取、异步向量化、列表、删除

迁移自 Java KnowledgeDocumentServiceImpl + InternalKnowledgeCallbackController
"""

import asyncio
import logging
import os
from datetime import datetime

from sqlalchemy import select, func, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.models.db.knowledge_document import KnowledgeDocument
from app.services import file_extractor, knowledge_vector_store
from app.ai.rag.text_splitter import split_text
from app.ai.llm.dashscope_client import dashscope_client

logger = logging.getLogger(__name__)

# 允许的文件类型
ALLOWED_EXTENSIONS = {".md", ".markdown", ".txt", ".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# status 状态值
STATUS_PENDING = 0    # 待处理
STATUS_VECTORIZED = 1  # 已向量化
STATUS_FAILED = 2      # 处理失败


async def upload_document(
    db: AsyncSession,
    user_id: int,
    filename: str,
    file_content: bytes,
) -> dict:
    """
    上传文档：提取文本 → 保存 MySQL → 异步向量化

    迁移自 Java KnowledgeDocumentServiceImpl.uploadDocument()
    区别：Python 内部异步向量化，不再 HTTP 回调 Java
    """
    # 1. 验证文件类型
    lower_name = filename.lower()
    ext = os.path.splitext(lower_name)[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise BusinessException(400, f"不支持的文件类型: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}")

    # 2. 验证文件大小
    if len(file_content) > MAX_FILE_SIZE:
        raise BusinessException(400, "文件大小超过限制（最大 50MB）")

    # 3. 提取文本
    try:
        text_content = file_extractor.extract_text(filename, file_content)
    except ValueError as e:
        raise BusinessException(400, str(e))

    if not text_content:
        raise BusinessException(400, "文件内容为空")

    # 4. 保存文档记录到 MySQL
    doc = KnowledgeDocument(
        user_id=user_id,
        title=filename,
        content=text_content,
        file_type=ext.lstrip("."),
        status=STATUS_PENDING,
    )
    db.add(doc)
    await db.flush()
    doc_id = doc.id
    logger.info(f"Document saved: id={doc_id}, user={user_id}, file={filename}")

    # 5. 异步向量化（不阻塞请求）
    asyncio.create_task(_vectorize_document(doc_id, user_id, text_content, filename))

    return _to_response(doc)


async def _vectorize_document(
    document_id: int,
    user_id: int,
    text_content: str,
    filename: str,
):
    """
    异步向量化文档（后台任务）

    替代 Java 的 HTTP 回调链：
    - Java: Python 向量化完 → HTTP 回调 Java → Java 更新 status
    - Python: 直接更新 MySQL status
    """
    db = None
    try:
        from app.core.database import async_session
        db = async_session()

        # 1. 文本分块
        chunks = split_text(text_content)
        if not chunks:
            await _update_status(db, document_id, STATUS_FAILED)
            logger.warning(f"No chunks generated for document {document_id}")
            return

        # 2. 生成向量
        embeddings = dashscope_client.get_embeddings_batch(chunks)

        # 3. 存储到 PgVector
        metadata = {
            "document_id": document_id,
            "user_id": user_id,
            "file_name": filename,
        }
        await knowledge_vector_store.add_chunks(document_id, chunks, embeddings, metadata)

        # 4. 更新状态 → 已向量化
        await _update_status(db, document_id, STATUS_VECTORIZED)
        logger.info(f"Vectorization completed: document={document_id}, chunks={len(chunks)}")

    except Exception as e:
        logger.error(f"Vectorization failed: document={document_id}, error={e}")
        try:
            if db:
                await _update_status(db, document_id, STATUS_FAILED)
        except Exception:
            pass
    finally:
        if db:
            await db.close()


async def _update_status(db: AsyncSession, document_id: int, status: int):
    """更新文档处理状态"""
    await db.execute(
        sa_update(KnowledgeDocument)
        .where(KnowledgeDocument.id == document_id)
        .values(status=status, update_time=datetime.now())
    )
    await db.commit()


async def get_document_list(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    查询文档列表（分页，时间倒序）

    迁移自 Java KnowledgeDocumentServiceImpl.getDocumentList()
    """
    # 总数
    count_stmt = (
        select(func.count())
        .select_from(KnowledgeDocument)
        .where(
            KnowledgeDocument.user_id == user_id,
            KnowledgeDocument.is_deleted == 0,
        )
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    # 分页查询
    stmt = (
        select(KnowledgeDocument)
        .where(
            KnowledgeDocument.user_id == user_id,
            KnowledgeDocument.is_deleted == 0,
        )
        .order_by(KnowledgeDocument.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()

    return {
        "list": [_to_response(d) for d in docs],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


async def delete_document(db: AsyncSession, user_id: int, document_id: int) -> dict:
    """
    删除文档：软删除 MySQL + 删除 PgVector 向量

    迁移自 Java KnowledgeDocumentServiceImpl.deleteDocument()
    区别：Python 内部直接删除 PgVector，不再 HTTP 调用
    """
    # 1. 查询文档
    stmt = select(KnowledgeDocument).where(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.user_id == user_id,
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise BusinessException(400, "文档不存在")
    if doc.is_deleted:
        raise BusinessException(400, "文档已删除")

    # 2. 删除 PgVector 向量（失败不影响主流程）
    try:
        count = await knowledge_vector_store.delete_by_document(document_id)
        logger.info(f"Deleted {count} vectors for document {document_id}")
    except Exception as e:
        logger.warning(f"Vector deletion failed (non-critical): {e}")

    # 3. 软删除 MySQL 记录
    doc.is_deleted = True
    doc.update_time = datetime.now()
    await db.commit()

    logger.info(f"Document deleted: id={document_id}, user={user_id}")
    return {"success": True}


async def cleanup_orphaned_vectors() -> int:
    """
    清理孤立向量（定时任务调用）

    替代 Java VectorCleanupScheduler
    """
    try:
        count = await knowledge_vector_store.cleanup_orphaned()
        return count
    except Exception as e:
        logger.error(f"Orphaned vector cleanup failed: {e}")
        return 0


def _to_response(doc: KnowledgeDocument) -> dict:
    """文档 ORM → 响应字典"""
    return {
        "id": doc.id,
        "user_id": doc.user_id,
        "title": doc.title,
        "file_type": doc.file_type,
        "status": doc.status,
        "is_deleted": doc.is_deleted,
        "create_time": doc.create_time.strftime("%Y-%m-%d %H:%M:%S") if doc.create_time else "",
    }
