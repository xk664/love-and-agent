"""
Internal Token Authentication Middleware
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings


# Bearer token scheme
security = HTTPBearer(auto_error=False)


def generate_internal_token() -> str:
    """Generate a secure internal token"""
    return secrets.token_urlsafe(32)


def create_token(expires_delta: Optional[timedelta] = None) -> str:
    """
    Create an internal authentication token.
    In production, use JWT or similar. This is a simple implementation.
    """
    token = generate_internal_token()
    return token


def verify_token(token: str) -> bool:
    """
    Verify internal token.
    For production, implement proper JWT verification.
    """
    expected_token = settings.auth.INTERNAL_TOKEN

    if not expected_token:
        # If no token configured, allow all (dev mode)
        if settings.app.DEBUG:
            return True
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal token not configured"
        )

    return secrets.compare_digest(token, expected_token)


async def get_current_token(credentials: Optional[HTTPAuthorizationCredentials] = None) -> str:
    """Get and verify current token from request"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    if not verify_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


class InternalTokenMiddleware:
    """
    Middleware for internal token authentication.
    Protects internal endpoints.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Skip auth for public endpoints
            if self._is_public_endpoint(request.url.path):
                return await self.app(scope, receive, send)

            # Get token from header
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                if verify_token(token):
                    return await self.app(scope, receive, send)

            # Check internal token header
            internal_token = request.headers.get("X-Internal-Token", "")
            if internal_token and verify_token(internal_token):
                return await self.app(scope, receive, send)

            # Token invalid or missing
            response = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            from starlette.responses import JSONResponse
            error_response = JSONResponse(
                status_code=response.status_code,
                content={"detail": response.detail},
                headers=response.headers
            )
            await error_response(scope, receive, send)
            return

        return await self.app(scope, receive, send)

    @staticmethod
    def _is_public_endpoint(path: str) -> bool:
        """Check if endpoint is public (no auth required)"""
        public_paths = [
            "/health",
            "/internal/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]
        return any(path.startswith(p) for p in public_paths)


def require_auth(credentials: HTTPAuthorizationCredentials = security):
    """
    Dependency for protected endpoints.
    Usage: @router.get("/protected", dependencies=[Depends(require_auth)])
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials
