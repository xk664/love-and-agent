"""
JWT Authentication
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings

# JWT configuration
JWT_SECRET = getattr(settings.auth, "JWT_SECRET", settings.auth.INTERNAL_TOKEN or "yu-ai-agent-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User ID to encode in token
        expires_delta: Token expiration time delta

    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRE_HOURS)

    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """
    Decode JWT access token and extract user_id.

    Args:
        token: JWT token string

    Returns:
        User ID

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> int:
    """
    FastAPI dependency: extract user_id from JWT token.

    前端只需在 Header 中传 Authorization: <token>，无需 Bearer 前缀。

    Usage:
        @router.get("/protected")
        async def protected(user_id: int = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
    # 兼容 "Bearer xxx" 和直接传 "xxx" 两种格式
    token = authorization.removeprefix("Bearer ").strip()
    return decode_access_token(token)
