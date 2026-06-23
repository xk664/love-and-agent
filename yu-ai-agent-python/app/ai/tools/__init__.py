"""
Tools Module - 工具框架

提供工具基础类、注册机制、内置工具和高级工具
"""
from app.ai.tools.base import (
    BaseTool, ToolParameter, ToolResult, ToolCallLog,
    ToolRegistry, ToolLogger, tool_registry, tool_logger,
)
from app.ai.tools.builtin import register_builtin_tools
from app.ai.tools.advanced import register_advanced_tools

# 自动注册所有工具
register_builtin_tools()
register_advanced_tools()

__all__ = [
    "BaseTool",
    "ToolParameter",
    "ToolResult",
    "ToolCallLog",
    "ToolRegistry",
    "ToolLogger",
    "tool_registry",
    "tool_logger",
    "register_builtin_tools",
    "register_advanced_tools",
]
