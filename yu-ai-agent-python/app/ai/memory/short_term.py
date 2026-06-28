"""
短期记忆 (Short-term Memory)

当前会话的上下文窗口，直接放入LLM的prompt
特点：内存存储，会话级生命周期，token限制自动裁剪
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


class ShortTermMemory:
    """短期记忆：当前会话的即时记忆，随会话结束消失"""

    def __init__(self, max_messages: int = 50, max_tokens: int = 4000):
        """
        初始化短期记忆

        Args:
            max_messages: 最大消息数量
            max_tokens: 最大token数（估算）
        """
        self.messages: list[dict] = []
        self.max_messages = max_messages
        self.max_tokens = max_tokens

    def add(self, role: str, content: str) -> None:
        """
        添加消息到短期记忆

        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
        """
        self.messages.append({"role": role, "content": content})
        self._trim_to_limit()
        logger.debug(f"短期记忆添加消息: role={role}, 当前消息数={len(self.messages)}")

    def get_context(self) -> list[dict]:
        """获取当前会话上下文"""
        return self.messages.copy()

    def get_recent(self, n: int = 10) -> list[dict]:
        """获取最近n条消息"""
        return self.messages[-n:] if len(self.messages) >= n else self.messages.copy()

    def clear(self) -> None:
        """清空短期记忆（会话结束时调用）"""
        self.messages.clear()
        logger.debug("短期记忆已清空")

    def size(self) -> int:
        """获取当前消息数量"""
        return len(self.messages)

    def _trim_to_limit(self) -> None:
        """裁剪消息到限制范围内"""
        # 按消息数量裁剪
        if len(self.messages) > self.max_messages:
            excess = len(self.messages) - self.max_messages
            self.messages = self.messages[excess:]
            logger.debug(f"短期记忆裁剪: 移除{excess}条旧消息")

    def _estimate_tokens(self, text: str) -> int:
        """估算token数量（简化版：中文约1.5字/token，英文约4字符/token）"""
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars / 4)

    def get_total_tokens(self) -> int:
        """估算当前记忆的总token数"""
        return sum(self._estimate_tokens(msg["content"]) for msg in self.messages)
