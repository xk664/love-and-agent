"""
数字朋友管理外部 API（需 JWT 认证）

端点:
- POST   /api/v1/friend/create              创建数字朋友
- GET    /api/v1/friend/list                数字朋友列表
- GET    /api/v1/friend/{friend_id}         数字朋友详情
- PUT    /api/v1/friend/{friend_id}         更新数字朋友
- DELETE /api/v1/friend/{friend_id}         删除数字朋友
- POST   /api/v1/friend/{friend_id}/source  添加素材（JSON文本）
- POST   /api/v1/friend/{friend_id}/source/upload  上传文件添加素材
- POST   /api/v1/friend/{friend_id}/distill 触发人格蒸馏（进入校准阶段）
- GET    /api/v1/friend/{friend_id}/status  获取蒸馏状态
- GET    /api/v1/friend/{friend_id}/calibration  获取校准问题
- POST   /api/v1/friend/{friend_id}/calibration  保存校准回答
- POST   /api/v1/friend/{friend_id}/finalize 完成校准，生成最终人格
"""

from fastapi import APIRouter, Depends, Query, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services import digital_friend_service

router = APIRouter(prefix="/api/v1/friend", tags=["数字朋友"])


# ===== 请求模型 =====

class CreateFriendRequest(BaseModel):
    """创建数字朋友请求"""
    name: str = Field(..., description="朋友昵称", min_length=1, max_length=64)
    description: str | None = Field(None, description="一句话描述", max_length=500)
    avatar_url: str | None = Field(None, description="头像URL")


class UpdateFriendRequest(BaseModel):
    """更新数字朋友请求"""
    name: str | None = Field(None, description="朋友昵称", max_length=64)
    description: str | None = Field(None, description="一句话描述", max_length=500)
    avatar_url: str | None = Field(None, description="头像URL")


class AddSourceRequest(BaseModel):
    """添加素材请求"""
    materials: list[dict] = Field(
        ...,
        description="素材列表，每项包含 type 和 content",
        min_length=1,
    )
    # 材料格式: [{"type": "chat_log", "content": "聊天记录内容..."}, {"type": "hobby", "content": "爱好内容..."}]
    # type 可选值: chat_log / moments / hobby / habit / description


class CalibrationAnswerRequest(BaseModel):
    """校准回答请求"""
    answers: list[dict] = Field(
        ...,
        description="回答列表，格式: [{question, answer}, ...]",
        min_length=1,
    )
    # 格式: [{"question": "他遇到压力时怎么排解？", "answer": "打游戏发泄"}, ...]


# ===== CRUD 接口 =====

@router.post("/create")
async def create_friend(
    request: CreateFriendRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建数字朋友"""
    result = await digital_friend_service.create_friend(
        db=db,
        user_id=user_id,
        name=request.name,
        description=request.description,
        avatar_url=request.avatar_url,
    )
    return {"code": 200, "message": "success", "data": result}


@router.get("/list")
async def list_friends(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """数字朋友列表（分页）"""
    result = await digital_friend_service.list_friends(db, user_id, page, page_size)
    return {"code": 200, "message": "success", "data": result}


@router.get("/{friend_id}")
async def get_friend(
    friend_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """数字朋友详情"""
    result = await digital_friend_service.get_friend(db, user_id, friend_id)
    return {"code": 200, "message": "success", "data": result}


@router.put("/{friend_id}")
async def update_friend(
    friend_id: int,
    request: UpdateFriendRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新数字朋友信息"""
    result = await digital_friend_service.update_friend(
        db=db,
        user_id=user_id,
        friend_id=friend_id,
        name=request.name,
        description=request.description,
        avatar_url=request.avatar_url,
    )
    return {"code": 200, "message": "success", "data": result}


@router.delete("/{friend_id}")
async def delete_friend(
    friend_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除数字朋友"""
    result = await digital_friend_service.delete_friend(db, user_id, friend_id)
    return {"code": 200, "message": "success", "data": result}


# ===== 素材与蒸馏 =====

@router.post("/{friend_id}/source")
async def add_source(
    friend_id: int,
    request: AddSourceRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """添加素材到数字朋友"""
    result = await digital_friend_service.save_source_materials(
        db=db,
        user_id=user_id,
        friend_id=friend_id,
        materials=request.materials,
    )
    return {"code": 200, "message": "success", "data": result}


@router.post("/{friend_id}/source/upload")
async def upload_source_file(
    friend_id: int,
    file: UploadFile = File(..., description="上传文件（.txt/.csv/.md）"),
    source_type: str = Form("chat_log", description="素材类型: chat_log/moments/hobby/habit/description"),
    title: str | None = Form(None, description="素材标题，不传则用文件名"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文件添加素材

    支持文件类型: .txt, .csv, .md
    自动读取文件内容，存为文本素材
    """
    import os

    # 1. 验证文件类型
    allowed_exts = {".txt", ".csv", ".md", ".markdown"}
    filename = file.filename or "unknown.txt"
    ext = os.path.splitext(filename.lower())[1]
    if ext not in allowed_exts:
        from app.core.exceptions import BusinessException
        raise BusinessException(400, f"不支持的文件类型: {ext}，仅支持 {', '.join(allowed_exts)}")

    # 2. 读取文件内容
    content_bytes = await file.read()
    if len(content_bytes) == 0:
        from app.core.exceptions import BusinessException
        raise BusinessException(400, "文件内容为空")

    # 3. 尝试多种编码解码
    text_content = None
    for encoding in ["utf-8", "gbk", "gb2312", "latin-1"]:
        try:
            text_content = content_bytes.decode(encoding)
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if text_content is None:
        from app.core.exceptions import BusinessException
        raise BusinessException(400, "无法解码文件内容，请确保文件编码为 UTF-8 或 GBK")

    # 4. 组装素材并调用保存方法
    materials = [{
        "type": source_type,
        "content": text_content,
        "title": title or filename,
    }]

    result = await digital_friend_service.save_source_materials(
        db=db,
        user_id=user_id,
        friend_id=friend_id,
        materials=materials,
    )
    return {"code": 200, "message": "success", "data": result}


@router.post("/{friend_id}/distill")
async def distill_friend(
    friend_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """触发人格蒸馏：LLM根据素材生成系统提示词"""
    result = await digital_friend_service.generate_system_prompt(
        db=db,
        user_id=user_id,
        friend_id=friend_id,
    )
    return {"code": 200, "message": "success", "data": result}


@router.get("/{friend_id}/status")
async def get_friend_status(
    friend_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取数字朋友蒸馏状态"""
    result = await digital_friend_service.get_friend_status(db, user_id, friend_id)
    return {"code": 200, "message": "success", "data": result}


# ===== 校准相关接口 =====

@router.get("/{friend_id}/calibration")
async def get_calibration(
    friend_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取校准问题"""
    result = await digital_friend_service.get_calibration_questions(db, user_id, friend_id)
    return {"code": 200, "message": "success", "data": result}


@router.post("/{friend_id}/calibration")
async def save_calibration(
    friend_id: int,
    request: CalibrationAnswerRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """保存校准回答"""
    result = await digital_friend_service.save_calibration_answers(
        db=db,
        user_id=user_id,
        friend_id=friend_id,
        answers=request.answers,
    )
    return {"code": 200, "message": "success", "data": result}


@router.post("/{friend_id}/finalize")
async def finalize(
    friend_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """完成校准，生成最终人格"""
    result = await digital_friend_service.finalize_calibration(
        db=db,
        user_id=user_id,
        friend_id=friend_id,
    )
    return {"code": 200, "message": "success", "data": result}
