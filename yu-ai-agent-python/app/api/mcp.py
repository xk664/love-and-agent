"""
MCP API Router - MCP 服务管理 API

提供 MCP 服务的热插拔管理能力：
- 列出已连接的 MCP 服务
- 添加并连接新的 MCP 服务
- 断开并移除 MCP 服务
- 列出所有 MCP 工具
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])

# 全局 MCP 管理器引用（在 main.py 中设置）
_mcp_manager = None


def set_mcp_manager(manager):
    """设置全局 MCP 管理器"""
    global _mcp_manager
    _mcp_manager = manager


def get_mcp_manager():
    """获取全局 MCP 管理器"""
    return _mcp_manager


# ===== 请求/响应模型 =====

class MCPServerRequest(BaseModel):
    """添加 MCP 服务的请求"""
    name: str = Field(description="服务名称")
    transport: str = Field(default="sse", description="连接方式: sse 或 stdio")
    url: str = Field(default="", description="SSE 端点 URL")
    command: str = Field(default="", description="Stdio 可执行命令")
    args: list[str] = Field(default_factory=list, description="Stdio 命令参数")
    env: dict[str, str] = Field(default_factory=dict, description="环境变量")
    timeout: int = Field(default=30, description="连接超时（秒）")


class MCPServerResponse(BaseModel):
    """MCP 服务信息响应"""
    name: str
    transport: str
    connected: bool
    tool_count: int


class MCPToolResponse(BaseModel):
    """MCP 工具信息响应"""
    name: str
    original_name: str
    server_name: str
    description: str
    parameters: list[dict]


class MCPStatusResponse(BaseModel):
    """MCP 状态响应"""
    enabled: bool
    connected_servers: int
    total_mcp_tools: int
    servers: list[MCPServerResponse]


# ===== API 端点 =====

@router.get("/status", response_model=MCPStatusResponse)
async def get_mcp_status():
    """获取 MCP 服务状态"""
    manager = get_mcp_manager()
    if not manager:
        return MCPStatusResponse(
            enabled=False,
            connected_servers=0,
            total_mcp_tools=0,
            servers=[],
        )

    # 获取已连接的服务器信息
    servers = []
    all_tools = await manager.list_all_tools()

    for server_name in manager.connected_servers:
        connection = manager.get_connection(server_name)
        tools = all_tools.get(server_name, [])
        servers.append(MCPServerResponse(
            name=server_name,
            transport=connection.config.transport if connection else "unknown",
            connected=True,
            tool_count=len(tools),
        ))

    # 计算 MCP 工具总数
    from app.ai.tools import tool_registry
    mcp_tools = [t for t in tool_registry.list_tools() if t.name.startswith("mcp_")]

    return MCPStatusResponse(
        enabled=True,
        connected_servers=len(manager.connected_servers),
        total_mcp_tools=len(mcp_tools),
        servers=servers,
    )


@router.get("/servers", response_model=list[MCPServerResponse])
async def list_mcp_servers():
    """列出所有已连接的 MCP 服务器"""
    manager = get_mcp_manager()
    if not manager:
        return []

    servers = []
    all_tools = await manager.list_all_tools()

    for server_name in manager.connected_servers:
        connection = manager.get_connection(server_name)
        tools = all_tools.get(server_name, [])
        servers.append(MCPServerResponse(
            name=server_name,
            transport=connection.config.transport if connection else "unknown",
            connected=True,
            tool_count=len(tools),
        ))

    return servers


@router.post("/servers", response_model=MCPServerResponse)
async def add_mcp_server(request: MCPServerRequest):
    """添加并连接新的 MCP 服务器"""
    manager = get_mcp_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")

    from app.ai.mcp import MCPServerConfig, register_mcp_tools

    # 检查是否已存在
    if manager.get_connection(request.name):
        raise HTTPException(
            status_code=409,
            detail=f"MCP server '{request.name}' already connected"
        )

    # 创建配置
    config = MCPServerConfig(
        name=request.name,
        transport=request.transport,
        url=request.url,
        command=request.command,
        args=request.args,
        env=request.env,
        timeout=request.timeout,
    )

    try:
        # 连接服务器
        connection = await manager.connect(config)

        # 获取工具列表
        tools = await connection.list_tools()

        # 注册工具
        if tools:
            register_mcp_tools(
                tools_info=tools,
                server_name=request.name,
                call_tool_func=manager.call_tool,
            )

        logger.info(f"Added MCP server '{request.name}' with {len(tools)} tools")

        return MCPServerResponse(
            name=request.name,
            transport=request.transport,
            connected=True,
            tool_count=len(tools),
        )

    except Exception as e:
        logger.error(f"Failed to add MCP server '{request.name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to MCP server: {str(e)}"
        )


@router.delete("/servers/{server_name}")
async def remove_mcp_server(server_name: str):
    """断开并移除 MCP 服务器"""
    manager = get_mcp_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="MCP manager not initialized")

    # 检查是否存在
    if not manager.get_connection(server_name):
        raise HTTPException(
            status_code=404,
            detail=f"MCP server '{server_name}' not found"
        )

    try:
        from app.ai.mcp import unregister_mcp_tools

        # 注销工具
        removed_count = unregister_mcp_tools(server_name)

        # 断开连接
        await manager.disconnect(server_name)

        logger.info(
            f"Removed MCP server '{server_name}' "
            f"and unregistered {removed_count} tools"
        )

        return {
            "message": f"MCP server '{server_name}' removed",
            "tools_unregistered": removed_count,
        }

    except Exception as e:
        logger.error(f"Failed to remove MCP server '{server_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove MCP server: {str(e)}"
        )


@router.get("/tools", response_model=list[MCPToolResponse])
async def list_mcp_tools():
    """列出所有 MCP 工具"""
    from app.ai.tools import tool_registry

    mcp_tools = []
    for tool in tool_registry.list_tools():
        if tool.name.startswith("mcp_") and hasattr(tool, 'original_name'):
            # 解析参数
            params = []
            for param in tool.parameters:
                params.append({
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                })

            mcp_tools.append(MCPToolResponse(
                name=tool.name,
                original_name=tool.original_name,
                server_name=tool.server_name,
                description=tool.description,
                parameters=params,
            ))

    return mcp_tools
