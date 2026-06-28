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
from app.api.knowledge import router as knowledge_router
from app.api.agent import router as agent_router
from app.api.user import router as user_router
from app.api.chat_v1 import router as chat_v1_router
from app.api.message_v1 import router as message_v1_router
from app.api.agent_v1 import router as agent_v1_router
from app.api.knowledge_v1 import router as knowledge_v1_router
from app.api.chat_ai_v1 import router as chat_ai_v1_router
from app.api.digital_friend_v1 import router as digital_friend_v1_router
from app.api.mcp import router as mcp_router
from app.api.mcp import set_mcp_manager
from app.core.exceptions import register_exception_handlers
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

    # Initialize MySQL connection
    try:
        from app.core.database import init_db
        await init_db()
        logger.info("MySQL database initialized")
    except Exception as e:
        logger.warning(f"MySQL initialization failed: {e}")

    # Initialize PgVector connection (creates embeddings table)
    try:
        from app.ai.rag.vector_store import vector_store
        await vector_store.init_db()
        logger.info("PgVector database initialized")
    except Exception as e:
        logger.warning(f"PgVector initialization skipped: {e}")

    # Initialize MCP connections
    mcp_manager = None
    try:
        from app.ai.mcp import MCPClientManager, load_mcp_config, register_mcp_tools

        mcp_config = load_mcp_config()
        if mcp_config.enabled and mcp_config.servers:
            mcp_manager = MCPClientManager()
            for server_config in mcp_config.servers:
                if not server_config.enabled:
                    logger.info(f"MCP server '{server_config.name}' is disabled, skipping")
                    continue
                try:
                    connection = await mcp_manager.connect(server_config)
                    tools = await connection.list_tools()
                    if tools:
                        register_mcp_tools(
                            tools_info=tools,
                            server_name=server_config.name,
                            call_tool_func=mcp_manager.call_tool,
                        )
                        logger.info(
                            f"MCP server '{server_config.name}': "
                            f"registered {len(tools)} tools"
                        )
                    else:
                        logger.info(f"MCP server '{server_config.name}': no tools available")
                except Exception as e:
                    logger.warning(f"Failed to connect MCP server '{server_config.name}': {e}")

            logger.info(f"MCP initialized: {len(mcp_manager.connected_servers)} servers connected")
            # 设置全局 MCP 管理器引用（用于 API 热插拔）
            set_mcp_manager(mcp_manager)
        else:
            logger.info("MCP is disabled or no servers configured")
    except Exception as e:
        logger.warning(f"MCP initialization skipped: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Disconnect MCP servers
    if mcp_manager:
        try:
            from app.ai.mcp import unregister_mcp_tools

            for server_name in mcp_manager.connected_servers:
                unregister_mcp_tools(server_name)
            await mcp_manager.disconnect_all()
            logger.info("MCP connections closed")
        except Exception as e:
            logger.warning(f"MCP cleanup error: {e}")

    # Close MySQL connections
    try:
        from app.core.database import close_db
        await close_db()
        logger.info("MySQL connections closed")
    except Exception as e:
        logger.warning(f"MySQL cleanup error: {e}")

    # Close PgVector connections
    try:
        from app.ai.rag.vector_store import vector_store
        await vector_store.close()
        logger.info("PgVector connections closed")
    except Exception as e:
        logger.warning(f"PgVector cleanup error: {e}")


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

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers
    app.include_router(health_router, tags=["health"])
    app.include_router(chat_router, tags=["chat"])
    app.include_router(knowledge_router, tags=["knowledge"])
    app.include_router(agent_router, tags=["agent"])
    app.include_router(mcp_router, tags=["mcp"])
    app.include_router(user_router, tags=["user"])
    app.include_router(chat_v1_router, tags=["chat"])
    app.include_router(message_v1_router, tags=["message"])
    app.include_router(agent_v1_router, tags=["agent"])
    app.include_router(knowledge_v1_router, tags=["knowledge"])
    app.include_router(chat_ai_v1_router, tags=["chat"])
    app.include_router(digital_friend_v1_router, tags=["digital_friend"])
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
