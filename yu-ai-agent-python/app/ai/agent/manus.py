"""
Manus Agent - 任务规划型智能体

在 ReAct 基础上增加复杂任务自主规划和多工具协同能力：
1. 规划阶段：分析任务，分解为多个子任务
2. 执行阶段：按计划逐步执行，每个子任务内部使用 ReAct 循环
3. 汇总阶段：整合所有子任务结果，生成最终回答
"""
import asyncio
import json
from typing import Any, Dict, List, Optional

from app.ai.agent.models import AgentState, ManusPlan, SubTask, SubTaskStatus, StepStatus
from app.ai.agent.react import ReactAgent
from app.ai.llm.dashscope_client import dashscope_client
from app.ai.tools.base import BaseTool, ToolResult
from app.core.logging import get_logger

logger = get_logger(__name__)

# 规划阶段系统提示词
PLAN_SYSTEM_PROMPT = """你是一个任务规划专家。你的职责是分析用户的复杂任务，将其分解为可执行的子任务列表。

## 可用工具

{tools_description}

## 规划规则

1. 分析任务复杂度，决定是否需要分解
2. 简单任务（单步可完成）直接返回 1 个子任务
3. 复杂任务分解为 2-8 个有序子任务
4. 每个子任务应独立可执行，描述清晰
5. 考虑子任务之间的依赖关系
6. 为每个子任务提示可能使用的工具

## 输出格式

请严格按照以下 JSON 格式输出，不要输出其他内容：

```json
{{
  "goal": "任务目标的一句话描述",
  "subtasks": [
    {{"id": 1, "description": "子任务描述", "tool_hint": "建议工具名称或null"}},
    {{"id": 2, "description": "子任务描述", "tool_hint": "建议工具名称或null"}}
  ]
}}
```"""

# 子任务执行阶段系统提示词
SUBTASK_SYSTEM_PROMPT = """你是一个能够使用工具的智能助手。你当前正在执行一个复杂任务中的子任务。

## 当前任务背景

总目标: {goal}
当前子任务: {subtask_description}
执行进度: {progress}

## 已完成的上下文

{completed_context}

## 可用工具

{tools_description}

## 回答格式

对于每个问题，请严格按照以下格式回答：

Thought: <你的推理过程，分析当前情况，决定下一步行动>
Action: <工具名称>
Action Input: <工具输入参数，JSON格式>

当你完成当前子任务时，使用以下格式：

Thought: <你的最终推理>
Final Answer: <当前子任务的完成结果，简洁明确>

## 注意事项

1. 专注于当前子任务，不要重复已完成的工作
2. 每次只能使用一个工具
3. 工具输入必须是有效的JSON格式
4. 如果不需要使用工具，可以直接给出 Final Answer
5. 请用中文回答"""

# 汇总阶段系统提示词
SUMMARY_SYSTEM_PROMPT = """你是一个智能助手。你需要根据一个复杂任务的执行过程和各子任务结果，生成一份完整的最终回答。

## 任务目标

{goal}

## 用户原始问题

{user_message}

## 各子任务执行结果

{subtask_results}

## 要求

1. 综合所有子任务的结果，生成一份完整、连贯的回答
2. 回答应直接面向用户的问题，不要暴露内部执行细节
3. 如果有子任务失败，说明原因并基于成功的结果给出回答
4. 使用清晰的结构（如分段、列表等）组织回答
5. 用中文回答"""


class ManusAgent(ReactAgent):
    """
    Manus 智能体

    在 ReAct 基础上增加：
    - 任务规划：将复杂任务分解为子任务序列
    - 多工具协同：按计划协调多个工具完成子任务
    - 动态调整：根据执行结果评估是否需要调整计划
    - 结果汇总：整合所有子任务结果生成最终回答
    """

    def __init__(
        self,
        max_steps: int = 30,
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

    async def _run_agent_loop(self, state: AgentState, **kwargs) -> str:
        """
        Manus 主循环：规划 → 执行 → 汇总

        Args:
            state: 当前状态
            **kwargs: 额外参数

        Returns:
            str: 最终回答
        """
        user_id = kwargs.get("user_id", 0)

        logger.info(f"Manus loop started: task_id={state.task_id}, max_steps={state.max_steps}")

        # Phase 1: 任务规划
        logger.info(f"Manus Phase 1: Planning task_id={state.task_id}")
        plan = await self._plan_task(state)
        if plan is None:
            # 规划失败，降级为普通 ReAct 模式
            logger.warning(f"Manus planning failed, falling back to ReAct: task_id={state.task_id}")
            return await super()._run_agent_loop(state, **kwargs)

        # 记录规划步骤
        plan_step = state.add_step(
            thought=f"任务规划: {plan.goal}",
            action="plan",
            action_input={"subtasks": [st.to_dict() for st in plan.subtasks]},
        )
        plan_step.mark_success(f"已生成 {len(plan.subtasks)} 个子任务，进度: {plan.progress}")
        await self._notify_step(plan_step)

        logger.info(
            f"Manus plan created: task_id={state.task_id}, "
            f"subtasks={len(plan.subtasks)}, goal={plan.goal}"
        )

        # Phase 2: 逐步执行子任务
        logger.info(f"Manus Phase 2: Executing plan task_id={state.task_id}")
        await self._execute_plan(state, plan, user_id)

        # Phase 3: 汇总结果
        logger.info(f"Manus Phase 3: Summarizing task_id={state.task_id}")
        final_answer = await self._summarize_results(state, plan)

        logger.info(
            f"Manus loop finished: task_id={state.task_id}, "
            f"progress={plan.progress}, steps={state.current_step}"
        )

        return final_answer

    async def _plan_task(self, state: AgentState) -> Optional[ManusPlan]:
        """
        规划阶段：分析任务并生成子任务列表

        Args:
            state: 当前状态

        Returns:
            ManusPlan: 执行计划，规划失败返回 None
        """
        # 构建工具描述
        tools_desc = self._build_tools_description()

        system_prompt = PLAN_SYSTEM_PROMPT.format(tools_description=tools_desc)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state.user_message},
        ]

        try:
            response = dashscope_client.chat(
                messages=messages,
                model=self.model,
                temperature=0.3,  # 规划用较低温度，保证稳定性
                stream=False,
            )

            # 解析计划
            plan = self._parse_plan(response, state.task_id, state.user_message)
            return plan

        except Exception as e:
            logger.error(f"Manus planning failed: task_id={state.task_id}, error={str(e)}")
            return None

    def _parse_plan(self, response: str, task_id: str, user_message: str = "") -> Optional[ManusPlan]:
        """
        解析 LLM 返回的计划 JSON

        Args:
            response: LLM 响应文本
            task_id: 任务 ID

        Returns:
            ManusPlan: 解析后的计划，失败返回 None
        """
        try:
            # 尝试从响应中提取 JSON
            json_str = response.strip()

            # 处理 markdown 代码块包裹的 JSON
            if "```json" in json_str:
                start = json_str.index("```json") + len("```json")
                end = json_str.index("```", start)
                json_str = json_str[start:end].strip()
            elif "```" in json_str:
                start = json_str.index("```") + len("```")
                end = json_str.index("```", start)
                json_str = json_str[start:end].strip()

            data = json.loads(json_str)

            goal = data.get("goal", "")
            subtasks_data = data.get("subtasks", [])

            if not subtasks_data:
                logger.warning("Plan parsing: no subtasks found")
                return None

            subtasks = []
            for st in subtasks_data:
                subtasks.append(SubTask(
                    id=st.get("id", len(subtasks) + 1),
                    description=st.get("description", ""),
                    tool_hint=st.get("tool_hint"),
                ))

            plan = ManusPlan(
                task_id=task_id,
                goal=goal or user_message[:100],
                subtasks=subtasks,
            )

            logger.info(f"Plan parsed: {len(subtasks)} subtasks")
            return plan

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Plan parsing failed: {str(e)}, response={response[:200]}")
            return None

    async def _execute_plan(self, state: AgentState, plan: ManusPlan, user_id: int):
        """
        执行计划：逐个完成子任务

        Args:
            state: 当前状态
            plan: 执行计划
            user_id: 用户 ID
        """
        while not plan.is_complete:
            # 检查是否达到最大步数
            if state.has_reached_max_steps():
                logger.warning(
                    f"Manus reached max steps during execution: "
                    f"task_id={state.task_id}, progress={plan.progress}"
                )
                # 标记剩余子任务为跳过
                for st in plan.get_pending_subtasks():
                    st.mark_skipped("达到最大执行步数")
                break

            # 检查是否被取消
            await asyncio.sleep(0)

            # 获取当前子任务
            subtask = plan.get_current_subtask()
            if subtask is None:
                break

            # 执行子任务
            subtask.mark_running()
            logger.info(
                f"Manus executing subtask: task_id={state.task_id}, "
                f"subtask_id={subtask.id}, desc={subtask.description}"
            )

            result = await self._execute_subtask(state, plan, subtask, user_id)

            if result is not None:
                subtask.mark_success(result)
                logger.info(
                    f"Manus subtask completed: task_id={state.task_id}, "
                    f"subtask_id={subtask.id}, result_len={len(result)}"
                )
            else:
                subtask.mark_failed("子任务执行失败")
                logger.warning(
                    f"Manus subtask failed: task_id={state.task_id}, "
                    f"subtask_id={subtask.id}"
                )

    async def _execute_subtask(
        self,
        state: AgentState,
        plan: ManusPlan,
        subtask: SubTask,
        user_id: int,
    ) -> Optional[str]:
        """
        执行单个子任务（内部使用 ReAct 循环）

        Args:
            state: 全局状态
            plan: 执行计划
            subtask: 当前子任务
            user_id: 用户 ID

        Returns:
            str: 子任务结果，失败返回 None
        """
        # 构建已完成上下文
        completed_context = self._build_completed_context(plan)

        # 构建子任务系统提示词
        tools_desc = self._build_tools_description()
        system_prompt = SUBTASK_SYSTEM_PROMPT.format(
            goal=plan.goal,
            subtask_description=subtask.description,
            progress=plan.progress,
            completed_context=completed_context or "暂无",
            tools_description=tools_desc,
        )

        # 子任务内部 ReAct 循环（限制步数，避免单个子任务消耗过多步数）
        subtask_max_steps = min(8, state.max_steps - state.current_step)

        for step_idx in range(subtask_max_steps):
            # 检查全局步数限制
            if state.has_reached_max_steps():
                break

            await asyncio.sleep(0)

            # 构建消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": subtask.description},
            ]

            # 添加子任务内部的历史步骤
            for prev_step in subtask.steps:
                if prev_step.action:
                    messages.append({
                        "role": "assistant",
                        "content": prev_step.thought or "",
                    })
                    if prev_step.observation:
                        messages.append({
                            "role": "user",
                            "content": f"工具 {prev_step.action} 的执行结果:\n{prev_step.observation}",
                        })

            if subtask.steps:
                messages.append({
                    "role": "user",
                    "content": "请继续思考和行动，或者给出当前子任务的完成结果。",
                })

            # 调用 LLM
            llm_response = dashscope_client.chat(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                stream=False,
            )

            # 解析响应（复用 ReactAgent 的解析逻辑）
            parsed = self._parse_llm_response(llm_response)

            # 如果有最终答案，子任务完成
            if parsed["final_answer"]:
                step = state.add_step(
                    thought=f"[子任务{subtask.id}] {parsed['thought']}",
                )
                step.mark_success(parsed["final_answer"])
                subtask.steps.append(step)
                await self._notify_step(step)
                return parsed["final_answer"]

            # 如果没有指定工具，将思考内容作为结果
            if not parsed["action"]:
                if parsed["thought"]:
                    step = state.add_step(
                        thought=f"[子任务{subtask.id}] {parsed['thought']}",
                    )
                    step.mark_success("无需使用工具")
                    subtask.steps.append(step)
                    return parsed["thought"]
                continue

            # 执行工具
            step = state.add_step(
                thought=f"[子任务{subtask.id}] {parsed['thought']}",
                action=parsed["action"],
                action_input=parsed["action_input"],
            )
            step.mark_running()

            tool_result: ToolResult = await self._execute_tool(
                tool_name=parsed["action"],
                tool_input=parsed["action_input"] or {},
                user_id=user_id,
            )

            if tool_result.success:
                step.mark_success(str(tool_result.output))
            else:
                step.mark_failed(tool_result.error or "工具执行失败")

            subtask.steps.append(step)
            await self._notify_step(step)

            logger.info(
                f"Manus subtask step: subtask_id={subtask.id}, "
                f"tool={parsed['action']}, success={tool_result.success}"
            )

        # 子任务循环结束但未得到最终答案
        # 尝试从最后的成功步骤中提取结果
        for step in reversed(subtask.steps):
            if step.observation and step.status == StepStatus.SUCCESS:
                return step.observation

        return None

    async def _summarize_results(self, state: AgentState, plan: ManusPlan) -> str:
        """
        汇总所有子任务结果，生成最终回答

        Args:
            state: 当前状态
            plan: 执行计划

        Returns:
            str: 最终回答
        """
        # 构建子任务结果摘要
        subtask_results_lines = []
        for st in plan.subtasks:
            status_desc = {
                SubTaskStatus.SUCCESS: "✅ 完成",
                SubTaskStatus.FAILED: "❌ 失败",
                SubTaskStatus.SKIPPED: "⏭️ 跳过",
            }.get(st.status, "❓ 未知")

            subtask_results_lines.append(
                f"子任务[{st.id}] {st.description}\n"
                f"  状态: {status_desc}\n"
                f"  结果: {st.result or '无'}"
            )

        subtask_results = "\n\n".join(subtask_results_lines)

        # 如果只有一个子任务且成功，直接返回其结果
        if len(plan.subtasks) == 1 and plan.subtasks[0].status == SubTaskStatus.SUCCESS:
            return plan.subtasks[0].result or "任务已完成"

        # 如果所有子任务都失败，返回错误信息
        all_failed = all(
            st.status in (SubTaskStatus.FAILED, SubTaskStatus.SKIPPED)
            for st in plan.subtasks
        )
        if all_failed:
            return (
                f"抱歉，任务执行未能成功完成。\n\n"
                f"执行计划: {plan.goal}\n"
                f"执行详情:\n{subtask_results}"
            )

        # 调用 LLM 汇总
        system_prompt = SUMMARY_SYSTEM_PROMPT.format(
            goal=plan.goal,
            user_message=state.user_message,
            subtask_results=subtask_results,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请根据以上各子任务的执行结果，生成一份完整的最终回答。"},
        ]

        try:
            final_answer = dashscope_client.chat(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                stream=False,
            )

            # 记录汇总步骤
            summary_step = state.add_step(
                thought="汇总所有子任务结果，生成最终回答",
            )
            summary_step.mark_success("汇总完成")
            await self._notify_step(summary_step)

            return final_answer

        except Exception as e:
            logger.error(f"Manus summarize failed: {str(e)}")
            # 降级：直接拼接结果
            return self._build_fallback_summary(plan)

    def _build_tools_description(self) -> str:
        """构建工具描述文本"""
        lines = []
        for tool in self.tools:
            params_desc = ""
            if tool.parameters:
                params_list = []
                for p in tool.parameters:
                    req = "(必填)" if p.required else "(可选)"
                    params_list.append(f"  - {p.name} {req}: {p.description}")
                params_desc = "\n" + "\n".join(params_list)

            lines.append(f"- **{tool.name}**: {tool.description}{params_desc}")

        return "\n".join(lines) if lines else "暂无可用工具"

    def _build_completed_context(self, plan: ManusPlan) -> str:
        """构建已完成子任务的上下文"""
        completed = [
            st for st in plan.subtasks
            if st.status == SubTaskStatus.SUCCESS and st.result
        ]

        if not completed:
            return ""

        lines = []
        for st in completed:
            lines.append(f"- 子任务{st.id} ({st.description}): {st.result[:200]}")

        return "\n".join(lines)

    def _build_fallback_summary(self, plan: ManusPlan) -> str:
        """降级汇总：直接拼接各子任务结果"""
        parts = [f"任务目标: {plan.goal}\n"]

        for st in plan.subtasks:
            if st.status == SubTaskStatus.SUCCESS and st.result:
                parts.append(f"**{st.description}**:\n{st.result}\n")
            elif st.status == SubTaskStatus.FAILED:
                parts.append(f"**{st.description}**: 执行失败\n")

        return "\n".join(parts)
