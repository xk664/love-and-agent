"""
MCP Tool Adapter - MCP 工具适配器

将远程 MCP 服务器提供的工具包装为本地 BaseTool 实现
支持自动转换 MCP inputSchema 为 ToolParameter 列表
"""
from typing import Any, Optional

from app.ai.tools.base import BaseTool, ToolParameter, ToolResult, tool_registry
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPToolAdapter(BaseTool):
    """
    MCP 工具适配器

    将远程 MCP 工具包装为 BaseTool，使其可以被 Agent 框架使用
    """

    def __init__(
        self,
        tool_info: dict,
        server_name: str,
        call_tool_func,
    ):
        """
        初始化 MCP 工具适配器

        Args:
            tool_info: MCP 工具信息，包含 name, description, inputSchema
            server_name: MCP 服务器名称
            call_tool_func: 调用远程工具的异步函数 (tool_name, arguments) -> result
        """
        self._tool_name = tool_info.get("name", "")
        self._description = tool_info.get("description", "")
        self._input_schema = tool_info.get("inputSchema", {})
        self._server_name = server_name
        self._call_tool_func = call_tool_func

        # 解析 inputSchema 为 ToolParameter 列表
        self._parameters = self._parse_parameters(self._input_schema)

        logger.info(
            f"MCPToolAdapter created: {self._tool_name} "
            f"(server={server_name}, params={len(self._parameters)})"
        )

    @property
    def name(self) -> str:
        """工具名称，添加 mcp_ 前缀避免冲突"""
        return f"mcp_{self._server_name}_{self._tool_name}"

    @property
    def description(self) -> str:
        """工具描述，附加 MCP 来源信息"""
        return f"[MCP:{self._server_name}] {self._description}"

    @property
    def parameters(self) -> list[ToolParameter]:
        """工具参数列表"""
        return self._parameters

    @property
    def original_name(self) -> str:
        """远程工具的原始名称"""
        return self._tool_name

    @property
    def server_name(self) -> str:
        """MCP 服务器名称"""
        return self._server_name

    def _parse_parameters(self, schema: dict) -> list[ToolParameter]:
        """
        将 MCP inputSchema (JSON Schema) 转换为 ToolParameter 列表

        MCP 使用标准 JSON Schema 格式:
        {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }

        Args:
            schema: MCP inputSchema

        Returns:
            list[ToolParameter]: 工具参数列表
        """
        parameters = []

        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        for prop_name, prop_schema in properties.items():
            param_type = prop_schema.get("type", "string")
            description = prop_schema.get("description", "")
            default_value = prop_schema.get("default")
            is_required = prop_name in required_fields

            # 类型映射：JSON Schema 类型 → 工具参数类型
            type_mapping = {
                "string": "string",
                "integer": "integer",
                "number": "number",
                "boolean": "boolean",
                "array": "array",
                "object": "object",
            }
            param_type = type_mapping.get(param_type, "string")

            # 枚举值支持：将 enum 信息添加到描述中
            enum_values = prop_schema.get("enum")
            if enum_values:
                enum_str = ", ".join(str(v) for v in enum_values)
                description = f"{description}（可选值: {enum_str}）"

            parameter = ToolParameter(
                name=prop_name,
                type=param_type,
                description=description or f"参数: {prop_name}",
                required=is_required,
                default=default_value,
            )
            parameters.append(parameter)

        return parameters

    async def execute(self, **kwargs) -> ToolResult:
        """
        执行远程 MCP 工具

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        try:
            # 提取参数，过滤空值
            arguments = {}
            for param in self._parameters:
                value = kwargs.get(param.name)
                if value is not None:
                    arguments[param.name] = value

            logger.info(
                f"Executing MCP tool '{self._tool_name}' "
                f"on server '{self._server_name}' with args: {arguments}"
            )

            # 调用远程工具
            result = await self._call_tool_func(
                self._server_name,
                self._tool_name,
                arguments,
            )

            # 处理结果
            if isinstance(result, str):
                output = result
            elif isinstance(result, dict):
                import json
                output = json.dumps(result, ensure_ascii=False, indent=2)
            else:
                output = str(result)

            return ToolResult(
                success=True,
                output=output,
                metadata={
                    "server": self._server_name,
                    "tool": self._tool_name,
                    "arguments": arguments,
                },
            )

        except Exception as e:
            logger.error(
                f"MCP tool execution failed: {self._tool_name} "
                f"on server '{self._server_name}': {e}"
            )
            return ToolResult(
                success=False,
                error=f"MCP 工具执行失败: {str(e)}",
                metadata={
                    "server": self._server_name,
                    "tool": self._tool_name,
                },
            )


def register_mcp_tools(
    tools_info: list[dict],
    server_name: str,
    call_tool_func,
) -> list[MCPToolAdapter]:
    """
    批量注册 MCP 工具到全局 tool_registry

    Args:
        tools_info: 工具信息列表
        server_name: MCP 服务器名称
        call_tool_func: 调用远程工具的函数

    Returns:
        list[MCPToolAdapter]: 创建的适配器列表
    """
    adapters = []

    for tool_info in tools_info:
        adapter = MCPToolAdapter(
            tool_info=tool_info,
            server_name=server_name,
            call_tool_func=call_tool_func,
        )

        # 检查是否已存在同名工具
        if tool_registry.has(adapter.name):
            logger.warning(
                f"MCP tool '{adapter.name}' already registered, updating"
            )

        tool_registry.register(adapter)
        adapters.append(adapter)
        logger.info(f"Registered MCP tool: {adapter.name}")

    return adapters


def unregister_mcp_tools(server_name: str) -> int:
    """
    注销指定 MCP 服务器的所有工具

    Args:
        server_name: MCP 服务器名称

    Returns:
        int: 注销的工具数量
    """
    prefix = f"mcp_{server_name}_"
    tools_to_remove = [
        tool.name
        for tool in tool_registry.list_tools()
        if tool.name.startswith(prefix)
    ]

    for tool_name in tools_to_remove:
        tool_registry.unregister(tool_name)
        logger.info(f"Unregistered MCP tool: {tool_name}")

    return len(tools_to_remove)
