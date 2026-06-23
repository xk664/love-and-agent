"""
知识库管理外部 API（需 JWT 认证）

端点:
- POST   /api/v1/knowledge/document          上传文档
- GET    /api/v1/knowledge/document/list      文档列表
- DELETE /api/v1/knowledge/document/{id}      删除文档
"""

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services import knowledge_service

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识库管理"])


@router.post("/document")
async def upload_document(
    file: UploadFile = File(..., description="上传文件（.md/.txt/.pdf）"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """上传文档：提取文本 → 保存 MySQL → 异步向量化"""
    content = await file.read()
    result = await knowledge_service.upload_document(
        db=db,
        user_id=user_id,
        filename=file.filename or "unknown",
        file_content=content,
    )
    return {"code": 200, "message": "success", "data": result}


@router.get("/document/list")
async def get_document_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """查询文档列表（分页）"""
    result = await knowledge_service.get_document_list(db, user_id, page, page_size)
    return {"code": 200, "message": "success", "data": result}


@router.delete("/document/{document_id}")
async def delete_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除文档（软删除 + 删除向量）"""
    result = await knowledge_service.delete_document(db, user_id, document_id)
    return {"code": 200, "message": "success", "data": result}
