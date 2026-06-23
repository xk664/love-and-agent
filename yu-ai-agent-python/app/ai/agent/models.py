"""
Agent Models - 智能体数据模型

定义智能体执行过程中使用的数据结构
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    """步骤执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentStep(BaseModel):
    """
    智能体执行步骤记录

    记录每一步的工具调用、输入输出、状态和耗时
    """
    step_number: int = Field(..., description="步骤编号")
    thought: str = Field(default="", description="推理思考内容")
    action: Optional[str] = Field(default=None, description="执行的工具名称")
    action_input: Optional[Dict[str, Any]] = Field(default=None, description="工具输入参数")
    observation: Optional[str] = Field(default=None, description="工具执行结果")
    status: StepStatus = Field(default=StepStatus.PENDING, description="步骤状态")
    error: Optional[str] = Field(default=None, description="错误信息")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    duration_ms: Optional[float] = Field(default=None, description="执行耗时(毫秒)")

    def mark_running(self):
        """标记为运行中"""
        self.status = StepStatus.RUNNING
        self.start_time = datetime.now()

    def mark_success(self, observation: str):
        """标记为成功"""
        self.status = StepStatus.SUCCESS
        self.observation = observation
        self.end_time = datetime.now()
        if self.start_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def mark_failed(self, error: str):
        """标记为失败"""
        self.status = StepStatus.FAILED
        self.error = error
        self.end_time = datetime.now()
        if self.start_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于回调"""
        return {
            "step": self.step_number,
            "thought": self.thought,
            "action": self.action,
            "action_input": self.action_input,
            "observation": self.observation,
            "status": self.status.value,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms else None,
        }


class AgentState(BaseModel):
    """
    智能体执行状态

    跟踪整个智能体执行过程的状态
    """
    task_id: str
    chat_id: str
    user_message: str
    current_step: int = Field(default=0, description="当前步骤数")
    max_steps: int = Field(default=20, description="最大执行步骤")
    steps: List[AgentStep] = Field(default_factory=list, description="执行步骤列表")
    final_answer: Optional[str] = Field(default=None, description="最终回答")
    is_finished: bool = Field(default=False, description="是否已完成")
    finish_reason: Optional[str] = Field(default=None, description="完成原因")

    def add_step(self, thought: str = "", action: str = None, action_input: dict = None) -> AgentStep:
        """添加新步骤"""
        self.current_step += 1
        step = AgentStep(
            step_number=self.current_step,
            thought=thought,
            action=action,
            action_input=action_input,
        )
        self.steps.append(step)
        return step

    def has_reached_max_steps(self) -> bool:
        """是否达到最大步骤数"""
        return self.current_step >= self.max_steps

    def get_steps_summary(self) -> str:
        """获取步骤摘要，用于 prompt 构建"""
        if not self.steps:
            return ""

        lines = []
        for step in self.steps:
            if step.action:
                lines.append(f"Step {step.step_number}: 使用工具 {step.action}")
                if step.observation:
                    lines.append(f"  结果: {step.observation[:200]}...")
            else:
                lines.append(f"Step {step.step_number}: {step.thought[:100]}...")
        return "\n".join(lines)

    def to_callback_steps(self) -> List[Dict[str, Any]]:
        """转换为回调格式的步骤列表"""
        return [step.to_dict() for step in self.steps]


class SubTaskStatus(str, Enum):
    """子任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class SubTask(BaseModel):
    """
    子任务定义

    ManusAgent 规划阶段生成的子任务单元
    """
    id: int = Field(..., description="子任务编号")
    description: str = Field(..., description="子任务描述")
    tool_hint: Optional[str] = Field(default=None, description="建议使用的工具")
    status: SubTaskStatus = Field(default=SubTaskStatus.PENDING, description="子任务状态")
    result: Optional[str] = Field(default=None, description="子任务执行结果")
    steps: List[AgentStep] = Field(default_factory=list, description="子任务内部执行步骤")

    def mark_running(self):
        """标记为运行中"""
        self.status = SubTaskStatus.RUNNING

    def mark_success(self, result: str):
        """标记为成功"""
        self.status = SubTaskStatus.SUCCESS
        self.result = result

    def mark_failed(self, error: str):
        """标记为失败"""
        self.status = SubTaskStatus.FAILED
        self.result = error

    def mark_skipped(self, reason: str = ""):
        """标记为跳过"""
        self.status = SubTaskStatus.SKIPPED
        self.result = reason or "已跳过"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "description": self.description,
            "tool_hint": self.tool_hint,
            "status": self.status.value,
            "result": self.result[:200] if self.result else None,
            "steps_count": len(self.steps),
        }


class ManusPlan(BaseModel):
    """
    Manus 任务执行计划

    包含任务分解后的子任务列表和执行进度
    """
    task_id: str = Field(..., description="关联的任务ID")
    goal: str = Field(..., description="任务目标描述")
    subtasks: List[SubTask] = Field(default_factory=list, description="子任务列表")
    current_index: int = Field(default=0, description="当前执行到的子任务索引")

    @property
    def is_complete(self) -> bool:
        """所有子任务是否都已完成"""
        return all(
            st.status in (SubTaskStatus.SUCCESS, SubTaskStatus.FAILED, SubTaskStatus.SKIPPED)
            for st in self.subtasks
        )

    @property
    def progress(self) -> str:
        """进度描述"""
        done = sum(
            1 for st in self.subtasks
            if st.status in (SubTaskStatus.SUCCESS, SubTaskStatus.FAILED, SubTaskStatus.SKIPPED)
        )
        return f"{done}/{len(self.subtasks)}"

    def get_pending_subtasks(self) -> List[SubTask]:
        """获取待执行的子任务"""
        return [st for st in self.subtasks if st.status == SubTaskStatus.PENDING]

    def get_current_subtask(self) -> Optional[SubTask]:
        """获取当前待执行的子任务"""
        for st in self.subtasks:
            if st.status == SubTaskStatus.PENDING:
                return st
        return None

    def get_summary(self) -> str:
        """获取执行摘要"""
        lines = [f"目标: {self.goal}", f"进度: {self.progress}", ""]
        for st in self.subtasks:
            status_icon = {
                SubTaskStatus.PENDING: "⏳",
                SubTaskStatus.RUNNING: "🔄",
                SubTaskStatus.SUCCESS: "✅",
                SubTaskStatus.FAILED: "❌",
                SubTaskStatus.SKIPPED: "⏭️",
            }.get(st.status, "❓")
            lines.append(f"  {status_icon} [{st.id}] {st.description}")
            if st.result and st.status != SubTaskStatus.PENDING:
                lines.append(f"      结果: {st.result[:100]}...")
        return "\n".join(lines)

    def to_callback_format(self) -> List[Dict[str, Any]]:
        """转换为回调格式（包含规划信息和各子任务步骤）"""
        callback_steps = []
        # 规划步骤
        callback_steps.append({
            "step": 0,
            "thought": f"任务规划: {self.goal}",
            "action": "plan",
            "action_input": {"subtasks": [st.to_dict() for st in self.subtasks]},
            "observation": f"已生成 {len(self.subtasks)} 个子任务",
            "status": "success",
            "error": None,
            "duration_ms": None,
        })
        # 各子任务的执行步骤
        step_num = 1
        for st in self.subtasks:
            for agent_step in st.steps:
                step_dict = agent_step.to_dict()
                step_dict["step"] = step_num
                step_dict["subtask_id"] = st.id
                callback_steps.append(step_dict)
                step_num += 1
        return callback_steps
