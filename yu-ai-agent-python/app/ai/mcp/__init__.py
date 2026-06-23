"""
MCP Module - Model Context Protocol 集成

提供 MCP 客户端管理、工具适配和配置加载能力
"""
from app.ai.mcp.client import MCPClientManager, MCPServerConnection
from app.ai.mcp.config import MCPConfig, MCPServerConfig, load_mcp_config
from app.ai.mcp.tool_adapter import (
    MCPToolAdapter,
    register_mcp_tools,
    unregister_mcp_tools,
)

__all__ = [
    # 客户端
    "MCPClientManager",
    "MCPServerConnection",
    # 配置
    "MCPConfig",
    "MCPServerConfig",
    "load_mcp_config",
    # 工具适配
    "MCPToolAdapter",
    "register_mcp_tools",
    "unregister_mcp_tools",
]
