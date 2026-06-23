"""
ReAct Agent - 推理与行动智能体

实现 Reasoning + Acting 循环模式的智能体
"""
import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from app.ai.agent.base import BaseAgent
from app.ai.agent.models import AgentState, StepStatus
from app.ai.llm.dashscope_client import dashscope_client
from app.ai.tools.base import BaseTool, ToolResult
from app.core.logging import get_logger

logger = get_logger(__name__)

# ReAct 模式的系统提示词模板
REACT_SYSTEM_PROMPT = """你是一个能够使用工具的智能助手。你需要通过推理(Reasoning)和行动(Acting)来解决用户的问题。

## 可用工具

{tools_description}

## 回答格式

对于每个问题，请严格按照以下格式回答：

Thought: <你的推理过程，分析当前情况，决定下一步行动>
Action: <工具名称>
Action Input: <工具输入参数，JSON格式>

当你收集到足够的信息可以回答用户问题时，使用以下格式：

Thought: <你的最终推理>
Final Answer: <你的最终回答>

## 注意事项

1. 每次只能使用一个工具
2. 工具输入必须是有效的JSON格式
3. 如果不需要使用工具，可以直接给出 Final Answer
4. 请用中文回答用户问题
5. 如果工具返回错误，请分析原因并尝试其他方法或直接回答"""


class ReactAgent(BaseAgent):
    """
    ReAct 智能体

    实现 Reasoning + Acting 循环：
    1. Thought: 推理当前情况，决定下一步
    2. Action: 选择并执行工具
    3. Observation: 观察工具执行结果
    4. 循环直到得出最终答案或达到最大步数
    """

    def __init__(
        self,
        max_steps: int = 20,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[BaseTool]] = None,
    ):
        super().__init__(
            max_steps=max_steps,
            model=model,
            temperature=temperature,
            tools=tools,
        )

    def _build_system_prompt(self, state: AgentState) -> str:
        """
        构建 ReAct 系统提示词

        Args:
            state: 当前状态

        Returns:
            str: 系统提示词
        """
        # 构建工具描述
        tools_desc_lines = []
        for tool in self.tools:
            params_desc = ""
            if tool.parameters:
                params_list = []
                for p in tool.parameters:
                    req = "(必填)" if p.required else "(可选)"
                    params_list.append(f"  - {p.name} {req}: {p.description}")
                params_desc = "\n" + "\n".join(params_list)

            tools_desc_lines.append(
                f"- **{tool.name}**: {tool.description}{params_desc}"
            )

        tools_description = "\n".join(tools_desc_lines) if tools_desc_lines else "暂无可用工具"

        return REACT_SYSTEM_PROMPT.format(tools_description=tools_description)

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        解析 LLM 响应

        Args:
            response: LLM 响应文本

        Returns:
            dict: 解析结果，包含 thought, action, action_input, final_answer
        """
        result = {
            "thought": "",
            "action": None,
            "action_input": None,
            "final_answer": None,
        }

        # 提取 Thought
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|\Z)", response, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        # 检查是否有 Final Answer
        final_answer_match = re.search(r"Final Answer:\s*(.*?)$", response, re.DOTALL)
        if final_answer_match:
            result["final_answer"] = final_answer_match.group(1).strip()
            return result

        # 提取 Action
        action_match = re.search(r"Action:\s*(.*?)(?=\nAction Input:|\nThought:|\Z)", response, re.DOTALL)
        if action_match:
            result["action"] = action_match.group(1).strip()

        # 提取 Action Input
        action_input_match = re.search(r"Action Input:\s*(.*?)(?=\nThought:|\Z)", response, re.DOTALL)
        if action_input_match:
            input_str = action_input_match.group(1).strip()
            try:
                # 尝试解析为 JSON
                result["action_input"] = json.loads(input_str)
            except json.JSONDecodeError:
                # 如果不是 JSON，作为简单参数处理
                result["action_input"] = {"query": input_str}

        return result

    async def _run_agent_loop(self, state: AgentState, **kwargs) -> str:
        """
        执行 ReAct 主循环

        Args:
            state: 当前状态
            **kwargs: 额外参数（如 user_id）

        Returns:
            str: 最终回答
        """
        user_id = kwargs.get("user_id", 0)
        system_prompt = self._build_system_prompt(state)

        logger.info(f"ReAct loop started: task_id={state.task_id}, max_steps={state.max_steps}")

        while not state.has_reached_max_steps():
            # 检查是否被取消
            await asyncio.sleep(0)

            # 构建消息
            messages = self._build_messages(system_prompt, state.user_message, state)

            # 添加工具使用说明到消息末尾
            if state.steps:
                messages.append({
                    "role": "user",
                    "content": "请继续思考和行动，或者给出最终回答。",
                })

            # 调用 LLM
            logger.info(f"ReAct step {state.current_step + 1}: calling LLM")
            llm_response = dashscope_client.chat(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                stream=False,
            )

            # 解析响应
            parsed = self._parse_llm_response(llm_response)
            logger.info(
                f"ReAct step {state.current_step + 1}: "
                f"thought={parsed['thought'][:50]}..., "
                f"action={parsed['action']}, "
                f"has_final_answer={parsed['final_answer'] is not None}"
            )

            # 如果有最终答案，结束循环
            if parsed["final_answer"]:
                # 记录最后一步
                step = state.add_step(thought=parsed["thought"])
                step.mark_success(parsed["final_answer"])
                await self._notify_step(step)

                logger.info(f"ReAct loop finished with final answer: task_id={state.task_id}")
                return parsed["final_answer"]

            # 如果没有指定工具，直接返回思考内容
            if not parsed["action"]:
                # 记录步骤
                step = state.add_step(thought=parsed["thought"])
                step.mark_success("无需使用工具")

                # 将思考内容作为最终答案
                if parsed["thought"]:
                    return parsed["thought"]
                continue

            # 执行工具
            step = state.add_step(
                thought=parsed["thought"],
                action=parsed["action"],
                action_input=parsed["action_input"],
            )
            step.mark_running()

            # 执行工具
            tool_result: ToolResult = await self._execute_tool(
                tool_name=parsed["action"],
                tool_input=parsed["action_input"] or {},
                user_id=user_id,
            )

            # 更新步骤状态
            if tool_result.success:
                step.mark_success(str(tool_result.output))
            else:
                step.mark_failed(tool_result.error or "工具执行失败")

            # 通知步骤完成
            await self._notify_step(step)

            logger.info(
                f"ReAct step {step.step_number}: "
                f"tool={parsed['action']}, "
                f"success={tool_result.success}, "
                f"duration={step.duration_ms:.0f}ms"
            )

        # 达到最大步数，强制终止
        logger.warning(
            f"ReAct loop reached max steps: task_id={state.task_id}, "
            f"steps={state.current_step}"
        )

        # 构建最终回答
        final_answer = self._build_force_stop_answer(state)
        return final_answer

    def _build_force_stop_answer(self, state: AgentState) -> str:
        """
        构建强制终止时的回答

        Args:
            state: 当前状态

        Returns:
            str: 基于已有信息的回答
        """
        # 尝试从最后一步的观察结果中提取有用信息
        last_observation = ""
        for step in reversed(state.steps):
            if step.observation and step.status == StepStatus.SUCCESS:
                last_observation = step.observation
                break

        if last_observation:
            return (
                f"基于已收集的信息，我的回答是：\n\n{last_observation}\n\n"
                f"（注：已达到最大执行步数 {state.max_steps} 步，以上回答基于已检索到的信息）"
            )

        return (
            f"抱歉，经过 {state.max_steps} 步推理后仍未找到满意的答案。"
            "请尝试简化您的问题，或提供更多具体信息。"
        )
