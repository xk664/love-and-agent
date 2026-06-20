"""
Yu AI Agent - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import get_logger, setup_logging

from app.api.health import router as health_router
from app.api.chat import router as chat_router

# Setup logging first
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app.APP_NAME} v{settings.app.APP_VERSION}")
    logger.info(f"Environment: {settings.app.APP_ENV}")
    logger.info(f"Debug mode: {settings.app.DEBUG}")

    # Initialize PgVector connection
    try:
        from app.ai.rag.vector_store import vector_store
        await vector_store.init_db()
        logger.info("PgVector database initialized")
    except Exception as e:
        logger.warning(f"PgVector initialization skipped: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Close database connections
    try:
        from app.ai.rag.vector_store import vector_store
        await vector_store.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Database cleanup error: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title=settings.app.APP_NAME,
        description="AI Agent Service with RAG capabilities",
        version=settings.app.APP_VERSION,
        docs_url="/docs" if settings.app.DEBUG else None,
        redoc_url="/redoc" if settings.app.DEBUG else None,
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router, tags=["health"])
    app.include_router(chat_router, tags=["chat"])

    return app


# Create application instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app.APP_NAME,
        "version": settings.app.APP_VERSION,
        "docs": "/docs" if settings.app.DEBUG else None
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.DEBUG,
        log_level="debug" if settings.app.DEBUG else "info"
    )
