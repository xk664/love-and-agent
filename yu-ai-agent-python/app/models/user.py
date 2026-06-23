"""
User DTO Models
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ===== Request Models =====

class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=100, description="密码")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")


class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


# ===== Response Models =====

class RegisterResponse(BaseModel):
    """用户注册响应"""
    user_id: int
    username: str
    nickname: Optional[str] = None


class LoginResponse(BaseModel):
    """用户登录响应"""
    token: str
    user_id: int
    username: str


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class UserResponse(BaseModel):
    """统一用户响应（包装在 Result 中）"""
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None
