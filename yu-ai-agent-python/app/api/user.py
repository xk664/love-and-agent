"""
User API - 用户注册、登录、信息管理
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import RegisterRequest, LoginRequest, RegisterResponse, LoginResponse, UserInfoResponse
from app.services import user_service

router = APIRouter(prefix="/api/v1/user", tags=["用户"])


@router.post("/register", response_model=None)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    用户注册

    - 参数校验（用户名、密码非空）
    - 用户名唯一性校验
    - BCrypt 加密密码
    """
    result = await user_service.register(db, request)
    return {"code": 200, "message": "success", "data": result.model_dump()}


@router.post("/login", response_model=None)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录

    - 校验用户名密码
    - 生成 JWT Token（有效期 24 小时）
    """
    result = await user_service.login(db, request)
    return {"code": 200, "message": "success", "data": result.model_dump()}


@router.get("/info", response_model=None)
async def get_user_info(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户信息（需 JWT 认证）
    """
    result = await user_service.get_user_info(db, user_id)
    return {"code": 200, "message": "success", "data": result.model_dump()}
