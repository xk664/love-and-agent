"""
User Service - 用户业务逻辑
"""
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.core.logging import get_logger
from app.core.security import create_access_token
from app.models.db.user import User
from app.models.user import RegisterRequest, LoginRequest, RegisterResponse, LoginResponse, UserInfoResponse

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """Hash password using BCrypt"""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against BCrypt hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


async def register(db: AsyncSession, request: RegisterRequest) -> RegisterResponse:
    """
    用户注册

    1. 校验用户名唯一性
    2. BCrypt 加密密码
    3. 保存用户到数据库
    """
    # 1. 检查用户名是否已存在
    stmt = select(User).where(User.username == request.username, User.is_deleted == False)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise BusinessException(code=400, message="用户名已存在")

    # 2. 创建用户
    user = User(
        username=request.username,
        password=hash_password(request.password),
        nickname=request.nickname or request.username,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    logger.info(f"用户注册成功: user_id={user.id}, username={user.username}")

    return RegisterResponse(
        user_id=user.id,
        username=user.username,
        nickname=user.nickname,
    )


async def login(db: AsyncSession, request: LoginRequest) -> LoginResponse:
    """
    用户登录

    1. 查询用户
    2. 校验密码
    3. 生成 JWT Token
    """
    # 1. 查询用户
    stmt = select(User).where(User.username == request.username, User.is_deleted == False)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise BusinessException(code=401, message="用户名或密码错误")

    # 2. 校验密码
    if not verify_password(request.password, user.password):
        raise BusinessException(code=401, message="用户名或密码错误")

    # 3. 生成 JWT Token
    token = create_access_token(user_id=user.id)

    logger.info(f"用户登录成功: user_id={user.id}, username={user.username}")

    return LoginResponse(
        token=token,
        user_id=user.id,
        username=user.username,
    )


async def get_user_info(db: AsyncSession, user_id: int) -> UserInfoResponse:
    """
    获取用户信息

    Args:
        user_id: 用户ID
    """
    stmt = select(User).where(User.id == user_id, User.is_deleted == False)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise BusinessException(code=404, message="用户不存在")

    return UserInfoResponse(
        user_id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar=user.avatar,
    )
