"""
Base Agent - 智能体抽象基类

定义智能体的基础接口和通用逻辑
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from app.ai.agent.models import AgentState, AgentStep
from app.ai.llm.dashscope_client import dashscope_client
from app.ai.tools.base import BaseTool, ToolResult, tool_registry
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    智能体抽象基类

    提供智能体的基础框架，子类需实现：
    - _build_system_prompt(): 构建系统提示词
    - _run_agent_loop(): 执行智能体主循环
    """

    def __init__(
        self,
        max_steps: int = 20,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[BaseTool]] = None,
    ):
        """
        初始化智能体

        Args:
            max_steps: 最大执行步骤数
            model: 使用的模型名称
            temperature: 温度参数
            tools: 可用工具列表，为 None 时使用全局注册的工具
        """
        self.max_steps = max_steps
        self.model = model
        self.temperature = temperature

        # 初始化工具
        self._tools: Dict[str, BaseTool] = {}
        if tools:
            for tool in tools:
                self._tools[tool.name] = tool
        else:
            # 使用全局注册的工具
            for tool in tool_registry.list_tools():
                self._tools[tool.name] = tool

        # 回调函数
        self._on_step_callback: Optional[Callable] = None
        self._on_finish_callback: Optional[Callable] = None

    @property
    def tools(self) -> List[BaseTool]:
        """获取所有可用工具"""
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """根据名称获取工具"""
        return self._tools.get(name)

    def on_step(self, callback: Callable):
        """注册步骤完成回调"""
        self._on_step_callback = callback

    def on_finish(self, callback: Callable):
        """注册任务完成回调"""
        self._on_finish_callback = callback

    async def _notify_step(self, step: AgentStep):
        """通知步骤完成"""
        if self._on_step_callback:
            try:
                await self._on_step_callback(step)
            except Exception as e:
                logger.error(f"Step callback error: {str(e)}")

    async def _notify_finish(self, state: AgentState):
        """通知任务完成"""
        if self._on_finish_callback:
            try:
                await self._on_finish_callback(state)
            except Exception as e:
                logger.error(f"Finish callback error: {str(e)}")

    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any], **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            **kwargs: 额外参数（如 user_id）

        Returns:
            ToolResult: 执行结果
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"工具 '{tool_name}' 不存在",
            )

        try:
            # 合并额外参数
            params = {**tool_input, **kwargs}
            result = await tool.run(**params)
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}, error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"工具执行失败: {str(e)}",
            )

    def _get_tool_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 Function Calling schema"""
        return [tool.to_function_schema() for tool in self._tools.values()]

    def _build_messages(
        self,
        system_prompt: str,
        user_message: str,
        state: AgentState,
    ) -> List[Dict[str, str]]:
        """
        构建消息列表

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            state: 当前状态

        Returns:
            list: 消息列表
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # 添加历史步骤到消息中（作为 assistant 和 tool 消息）
        for step in state.steps:
            if step.action:
                # assistant 消息：包含思考和工具调用
                assistant_content = step.thought or ""
                messages.append({
                    "role": "assistant",
                    "content": assistant_content,
                })
                # tool 消息：工具执行结果
                if step.observation:
                    messages.append({
                        "role": "user",
                        "content": f"工具 {step.action} 的执行结果:\n{step.observation}",
                    })

        return messages

    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        调用 LLM

        Args:
            messages: 消息列表
            tools: 工具 schema 列表

        Returns:
            dict: LLM 响应
        """
        try:
            # 使用 dashscope_client 的 chat 方法
            # 注意：这里需要扩展 dashscope_client 以支持 function calling
            # 目前先使用简单的文本生成
            response = dashscope_client.chat(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                stream=False,
            )
            return {"content": response}
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise

    @abstractmethod
    def _build_system_prompt(self, state: AgentState) -> str:
        """
        构建系统提示词

        Args:
            state: 当前状态

        Returns:
            str: 系统提示词
        """
        pass

    @abstractmethod
    async def _run_agent_loop(self, state: AgentState, **kwargs) -> str:
        """
        执行智能体主循环

        Args:
            state: 当前状态
            **kwargs: 额外参数

        Returns:
            str: 最终回答
        """
        pass

    async def run(
        self,
        task_id: str,
        chat_id: str,
        message: str,
        **kwargs,
    ) -> AgentState:
        """
        运行智能体

        Args:
            task_id: 任务 ID
            chat_id: 会话 ID
            message: 用户消息
            **kwargs: 额外参数

        Returns:
            AgentState: 执行状态
        """
        # 初始化状态
        state = AgentState(
            task_id=task_id,
            chat_id=chat_id,
            user_message=message,
            max_steps=self.max_steps,
        )

        logger.info(
            f"Agent started: task_id={task_id}, "
            f"max_steps={self.max_steps}, tools={list(self._tools.keys())}"
        )

        try:
            # 执行主循环
            final_answer = await self._run_agent_loop(state, **kwargs)
            state.final_answer = final_answer
            state.is_finished = True
            state.finish_reason = "completed"

        except asyncio.CancelledError:
            state.is_finished = True
            state.finish_reason = "cancelled"
            logger.info(f"Agent cancelled: task_id={task_id}")
            raise

        except Exception as e:
            state.is_finished = True
            state.finish_reason = "error"
            state.final_answer = f"执行出错: {str(e)}"
            logger.error(f"Agent error: task_id={task_id}, error={str(e)}")

        # 通知完成
        await self._notify_finish(state)

        logger.info(
            f"Agent finished: task_id={task_id}, "
            f"steps={state.current_step}, reason={state.finish_reason}"
        )

        return state
