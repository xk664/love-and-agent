"""
Tool Base Classes - 工具基础框架

提供工具的抽象基类、工具注册机制和调用日志
"""
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Optional[Any] = None


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolCallLog(BaseModel):
    """工具调用日志记录"""
    tool_name: str
    params: Dict[str, Any]
    success: bool
    output_preview: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float
    timestamp: str


class ToolLogger:
    """
    工具调用日志管理器

    记录所有工具调用的历史，支持查询和回调
    """

    def __init__(self, max_logs: int = 1000):
        self._logs: List[ToolCallLog] = []
        self._max_logs = max_logs
        self._on_log_callback: Optional[Callable] = None

    def on_log(self, callback: Callable):
        """注册日志回调"""
        self._on_log_callback = callback

    def log(self, entry: ToolCallLog):
        """记录一条日志"""
        self._logs.append(entry)
        # 超过上限时清理旧日志
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]
        # 触发回调
        if self._on_log_callback:
            try:
                self._on_log_callback(entry)
            except Exception:
                pass

    def get_logs(self, limit: int = 50) -> List[ToolCallLog]:
        """获取最近的调用日志"""
        return self._logs[-limit:]

    def get_logs_by_tool(self, tool_name: str, limit: int = 20) -> List[ToolCallLog]:
        """按工具名称筛选日志"""
        return [l for l in self._logs if l.tool_name == tool_name][-limit:]

    def clear(self):
        """清空日志"""
        self._logs.clear()


# 全局工具日志实例
tool_logger = ToolLogger()


class BaseTool(ABC):
    """
    工具抽象基类

    所有自定义工具需继承此类并实现：
    - name: 工具名称
    - description: 工具描述
    - parameters: 参数定义列表
    - execute(): 执行逻辑
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述，用于 LLM 理解工具用途"""
        pass

    @property
    def parameters(self) -> list[ToolParameter]:
        """参数定义列表，子类可覆盖"""
        return []

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        pass

    async def run(self, **kwargs) -> ToolResult:
        """
        带日志记录的工具执行入口

        自动记录调用参数、执行耗时和结果
        """
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = await self.execute(**kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # 记录日志
            output_preview = str(result.output)[:200] if result.output else None
            log_entry = ToolCallLog(
                tool_name=self.name,
                params=kwargs,
                success=result.success,
                output_preview=output_preview,
                error=result.error,
                duration_ms=round(duration_ms, 2),
                timestamp=timestamp,
            )
            tool_logger.log(log_entry)

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_entry = ToolCallLog(
                tool_name=self.name,
                params=kwargs,
                success=False,
                error=str(e),
                duration_ms=round(duration_ms, 2),
                timestamp=timestamp,
            )
            tool_logger.log(log_entry)
            raise

    def to_function_schema(self) -> Dict[str, Any]:
        """
        转换为 OpenAI Function Calling 格式的 schema

        Returns:
            dict: Function schema
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def validate_params(self, **kwargs) -> Dict[str, Any]:
        """
        验证并处理参数

        Args:
            **kwargs: 原始参数

        Returns:
            dict: 验证后的参数
        """
        validated = {}
        for param in self.parameters:
            if param.name in kwargs:
                validated[param.name] = kwargs[param.name]
            elif param.required:
                raise ValueError(f"Missing required parameter: {param.name}")
            elif param.default is not None:
                validated[param.name] = param.default
        return validated


class ToolRegistry:
    """
    工具注册中心

    管理所有可用工具的注册和查找
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """根据名称获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """获取所有已注册工具"""
        return list(self._tools.values())

    def get_schemas(self) -> list[Dict[str, Any]]:
        """获取所有工具的 Function Calling schema"""
        return [tool.to_function_schema() for tool in self._tools.values()]

    def has(self, name: str) -> bool:
        """检查工具是否已注册"""
        return name in self._tools

    def unregister(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            bool: 是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False


# 全局工具注册中心
tool_registry = ToolRegistry()
