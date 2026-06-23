"""
Unified Exception Handling
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class BusinessException(Exception):
    """Business logic exception with code and message"""

    def __init__(self, code: int = 400, message: str = "请求错误"):
        self.code = code
        self.message = message
        super().__init__(message)


def register_exception_handlers(app: FastAPI):
    """Register exception handlers on the FastAPI app"""

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        logger.warning(f"BusinessException: code={exc.code}, message={exc.message}, path={request.url.path}")
        return JSONResponse(
            status_code=exc.code,  # HTTP 200, business error in body
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}, path={request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None},
        )
