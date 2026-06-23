"""
Built-in Tools - 内置工具集

提供常用的内置工具实现
"""
import asyncio
from datetime import datetime

from app.ai.rag.retriever import hybrid_retrieve
from app.ai.tools.base import BaseTool, ToolParameter, ToolResult, tool_registry
from app.core.logging import get_logger

logger = get_logger(__name__)


class KnowledgeSearchTool(BaseTool):
    """知识库检索工具"""

    @property
    def name(self) -> str:
        return "knowledge_search"

    @property
    def description(self) -> str:
        return "从知识库中检索相关信息。当需要查找知识库中的内容来回答用户问题时使用此工具。"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="检索查询内容",
                required=True,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        try:
            query = kwargs.get("query", "")
            user_id = kwargs.get("user_id", 0)

            if not query:
                return ToolResult(success=False, error="查询内容不能为空")

            results = await hybrid_retrieve(query=query, user_id=user_id)

            if not results:
                return ToolResult(
                    success=True,
                    output="未找到相关知识库内容",
                    metadata={"count": 0},
                )

            # 格式化检索结果
            formatted = []
            for i, r in enumerate(results, 1):
                content = r.get("content", "")
                score = r.get("score", 0)
                formatted.append(f"[{i}] (相关度: {score:.2f}) {content}")

            output = "\n\n".join(formatted)
            return ToolResult(
                success=True,
                output=output,
                metadata={"count": len(results)},
            )

        except Exception as e:
            logger.error(f"Knowledge search failed: {str(e)}")
            return ToolResult(success=False, error=f"知识库检索失败: {str(e)}")


class CurrentTimeTool(BaseTool):
    """获取当前时间工具"""

    @property
    def name(self) -> str:
        return "current_time"

    @property
    def description(self) -> str:
        return "获取当前日期和时间。当用户询问当前时间或日期相关问题时使用此工具。"

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    async def execute(self, **kwargs) -> ToolResult:
        try:
            now = datetime.now()
            formatted = now.strftime("%Y年%m月%d日 %H:%M:%S")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]

            output = f"当前时间：{formatted} {weekday}"
            return ToolResult(success=True, output=output)

        except Exception as e:
            logger.error(f"Get current time failed: {str(e)}")
            return ToolResult(success=False, error=f"获取时间失败: {str(e)}")


class CalculatorTool(BaseTool):
    """计算器工具"""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "执行数学计算。当需要进行数值计算、数学运算时使用此工具。支持基本运算和常见数学函数。"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type="string",
                description="数学表达式，如 '2 + 3 * 4' 或 'sqrt(16)'",
                required=True,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        try:
            expression = kwargs.get("expression", "")

            if not expression:
                return ToolResult(success=False, error="表达式不能为空")

            # 安全的数学函数白名单
            safe_dict = {
                "abs": abs, "round": round,
                "min": min, "max": max,
                "sum": sum, "pow": pow,
                "int": int, "float": float,
            }

            # 只允许数字、运算符和白名单函数
            import math
            safe_dict.update({
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "pi": math.pi,
                "e": math.e,
            })

            result = eval(expression, {"__builtins__": {}}, safe_dict)
            output = f"{expression} = {result}"

            return ToolResult(success=True, output=output)

        except Exception as e:
            logger.error(f"Calculator failed: {str(e)}")
            return ToolResult(success=False, error=f"计算失败: {str(e)}")


def register_builtin_tools():
    """注册所有内置工具"""
    tool_registry.register(KnowledgeSearchTool())
    tool_registry.register(CurrentTimeTool())
    tool_registry.register(CalculatorTool())
    logger.info("Built-in tools registered")
