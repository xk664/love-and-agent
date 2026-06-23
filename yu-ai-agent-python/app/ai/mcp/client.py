"""
MCP Client Manager - MCP 客户端管理器

管理多个 MCP 服务器连接，支持 SSE 和 Stdio 两种传输方式
提供工具发现和调用能力
"""
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from app.ai.mcp.config import MCPServerConfig
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPServerConnection:
    """单个 MCP 服务器连接"""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session: Optional[ClientSession] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._connected = False
        self._tools: list[dict] = []

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def name(self) -> str:
        return self.config.name

    async def connect(self) -> None:
        """
        连接到 MCP 服务器

        根据 config.transport 选择 SSE 或 Stdio 连接方式
        """
        if self._connected:
            logger.warning(f"MCP server '{self.name}' already connected")
            return

        try:
            self._exit_stack = AsyncExitStack()

            if self.config.transport == "sse":
                await self._connect_sse()
            elif self.config.transport == "stdio":
                await self._connect_stdio()
            else:
                raise ValueError(f"Unsupported MCP transport: {self.config.transport}")

            self._connected = True
            logger.info(f"Connected to MCP server: {self.name} ({self.config.transport})")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{self.name}': {e}")
            await self._cleanup()
            raise

    async def _connect_sse(self) -> None:
        """建立 SSE 连接"""
        if not self.config.url:
            raise ValueError(f"MCP server '{self.name}': SSE URL is required")

        # 创建 SSE 客户端上下文
        transport = await self._exit_stack.enter_async_context(
            sse_client(
                url=self.config.url,
                headers=self.config.env if self.config.env else None,
                timeout=self.config.timeout,
            )
        )
        read_stream, write_stream = transport

        # 创建会话
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        # 初始化会话
        await self.session.initialize()

    async def _connect_stdio(self) -> None:
        """建立 Stdio 连接"""
        if not self.config.command:
            raise ValueError(f"MCP server '{self.name}': Stdio command is required")

        # 创建 Stdio 服务器参数
        server_params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args,
            env=self.config.env if self.config.env else None,
        )

        # 创建 Stdio 客户端上下文
        transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = transport

        # 创建会话
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        # 初始化会话
        await self.session.initialize()

    async def disconnect(self) -> None:
        """断开连接"""
        await self._cleanup()
        logger.info(f"Disconnected from MCP server: {self.name}")

    async def _cleanup(self) -> None:
        """清理资源"""
        self._connected = False
        self.session = None
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except Exception as e:
                logger.warning(f"Error closing MCP connection '{self.name}': {e}")
            self._exit_stack = None

    async def list_tools(self) -> list[dict]:
        """
        获取服务器提供的工具列表

        Returns:
            list[dict]: 工具信息列表，每个工具包含 name, description, inputSchema
        """
        if not self._connected or not self.session:
            raise RuntimeError(f"MCP server '{self.name}' is not connected")

        try:
            result = await self.session.list_tools()
            self._tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                }
                for tool in result.tools
            ]
            logger.info(f"MCP server '{self.name}' has {len(self._tools)} tools")
            return self._tools

        except Exception as e:
            logger.error(f"Failed to list tools from MCP server '{self.name}': {e}")
            raise

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        调用远程工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            Any: 工具执行结果
        """
        if not self._connected or not self.session:
            raise RuntimeError(f"MCP server '{self.name}' is not connected")

        try:
            logger.info(f"Calling MCP tool '{tool_name}' on server '{self.name}'")
            result = await self.session.call_tool(tool_name, arguments)

            # 提取结果内容
            if hasattr(result, 'content'):
                # 处理内容列表
                contents = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        contents.append(item.text)
                    elif hasattr(item, 'type'):
                        contents.append(f"[{item.type} content]")
                    else:
                        contents.append(str(item))
                return "\n".join(contents) if contents else str(result)

            return str(result)

        except Exception as e:
            logger.error(f"Failed to call MCP tool '{tool_name}' on server '{self.name}': {e}")
            raise


class MCPClientManager:
    """
    MCP 客户端管理器

    管理多个 MCP 服务器连接的生命周期
    """

    def __init__(self):
        self._connections: dict[str, MCPServerConnection] = {}

    @property
    def connected_servers(self) -> list[str]:
        """已连接的服务器名称列表"""
        return [name for name, conn in self._connections.items() if conn.connected]

    def get_connection(self, server_name: str) -> Optional[MCPServerConnection]:
        """获取指定服务器的连接"""
        return self._connections.get(server_name)

    async def connect(self, config: MCPServerConfig) -> MCPServerConnection:
        """
        连接到 MCP 服务器

        Args:
            config: 服务器配置

        Returns:
            MCPServerConnection: 服务器连接对象
        """
        if config.name in self._connections:
            existing = self._connections[config.name]
            if existing.connected:
                logger.warning(f"MCP server '{config.name}' already connected, skipping")
                return existing
            # 清理旧连接
            await existing.disconnect()

        connection = MCPServerConnection(config)
        await connection.connect()
        self._connections[config.name] = connection

        return connection

    async def disconnect(self, server_name: str) -> None:
        """断开指定服务器"""
        if server_name in self._connections:
            await self._connections[server_name].disconnect()
            del self._connections[server_name]
            logger.info(f"Removed MCP server: {server_name}")

    async def disconnect_all(self) -> None:
        """断开所有服务器"""
        for name, connection in list(self._connections.items()):
            try:
                await connection.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting MCP server '{name}': {e}")

        self._connections.clear()
        logger.info("All MCP servers disconnected")

    async def list_tools(self, server_name: str) -> list[dict]:
        """
        获取指定服务器的工具列表

        Args:
            server_name: 服务器名称

        Returns:
            list[dict]: 工具列表
        """
        connection = self._connections.get(server_name)
        if not connection or not connection.connected:
            raise RuntimeError(f"MCP server '{server_name}' is not connected")

        return await connection.list_tools()

    async def list_all_tools(self) -> dict[str, list[dict]]:
        """
        获取所有已连接服务器的工具列表

        Returns:
            dict[str, list[dict]]: 服务器名称 → 工具列表
        """
        result = {}
        for name, connection in self._connections.items():
            if connection.connected:
                try:
                    result[name] = await connection.list_tools()
                except Exception as e:
                    logger.error(f"Failed to list tools from '{name}': {e}")
                    result[name] = []
        return result

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        调用指定服务器的工具

        Args:
            server_name: 服务器名称
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            Any: 工具执行结果
        """
        connection = self._connections.get(server_name)
        if not connection or not connection.connected:
            raise RuntimeError(f"MCP server '{server_name}' is not connected")

        return await connection.call_tool(tool_name, arguments)
