"""
自适应上下文压缩策略 (Adaptive Context Compression)

基于多维度重要性评分的四级压缩策略：
- Level 0: 原始保留 (不压缩)
- Level 1: 关键信息提取
- Level 2: 语义摘要
- Level 3: 主题标签

通过动态 Token 预算管理，在保证对话质量的前提下降低 Token 消耗。
"""

import re
from typing import List, Optional
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScoredMessage:
    """带评分的消息"""
    message: dict
    score: float
    level: int
    original_index: int = 0  # 原始索引，用于恢复顺序


class ImportanceScorer:
    """重要性评分器"""

    # 决策/承诺关键词
    DECISION_KEYWORDS = ["决定", "选择", "承诺", "保证", "一定", "确认", "同意", "同意"]
    # 问题标记
    QUESTION_MARKS = ["?", "？"]

    def __init__(self, weights: dict = None):
        """
        初始化评分器

        Args:
            weights: 各维度权重，可自定义
        """
        self.weights = weights or {
            "role": 0.2,
            "recency": 0.25,
            "semantic_density": 0.2,
            "entity_density": 0.15,
            "question": 0.1,
            "decision": 0.1,
        }

    def score(self, message: dict, index: int, total: int) -> float:
        """
        计算消息重要性评分

        Args:
            message: 消息内容 {"role": str, "content": str}
            index: 消息在列表中的索引
            total: 消息总数

        Returns:
            重要性评分 (0-1)
        """
        content = message.get("content", "")
        score = 0.0

        # 1. 角色权重 (user=1.0, assistant=0.7, system=0.5)
        role_weight = 1.0 if message.get("role") == "user" else 0.7
        score += role_weight * self.weights["role"]

        # 2. 时间衰减 (越近越重要)
        recency = 1.0 - (total - index) / total if total > 0 else 0.5
        score += recency * self.weights["recency"]

        # 3. 语义密度 (信息量)
        density = self._calc_semantic_density(content)
        score += density * self.weights["semantic_density"]

        # 4. 实体密度 (人名/地点/时间)
        entity_count = self._count_entities(content)
        entity_density = min(entity_count / 5, 1.0)
        score += entity_density * self.weights["entity_density"]

        # 5. 问题标记 (用户提问更重要)
        if any(mark in content for mark in self.QUESTION_MARKS):
            score += self.weights["question"]

        # 6. 决策/承诺标记
        if any(kw in content for kw in self.DECISION_KEYWORDS):
            score += self.weights["decision"]

        # 归一化到 0-1
        return min(max(score, 0), 1)

    def _calc_semantic_density(self, text: str) -> float:
        """
        计算语义密度 - 衡量文本的信息量

        原理：
        - 信息量大的文本通常句子较长、结构复杂
        - 信息量小的文本通常句子短、简单
        """
        if not text:
            return 0.0

        # 按句号分割
        sentences = [s.strip() for s in text.split("。") if s.strip()]

        if not sentences:
            return 0.0

        # 计算平均句子长度
        total_chars = sum(len(s) for s in sentences)
        avg_length = total_chars / len(sentences)

        # 归一化：50字以上认为是高密度
        return min(avg_length / 50, 1.0)

    def _count_entities(self, text: str) -> int:
        """
        统计实体数量 - 人名、地名、时间等

        原理：
        - 包含实体的文本通常更具体、更重要
        - 实体是信息的关键载体
        """
        if not text:
            return 0

        entities = 0

        # 1. 人名模式：中文名 + 称谓
        name_patterns = [
            r'[一-鿿]{2,3}(?:老师|同学|先生|女士|哥|姐|弟|妹)',
            r'(?:小|老)[一-鿿]{1,2}',
        ]
        for pattern in name_patterns:
            entities += len(re.findall(pattern, text))

        # 2. 时间模式
        time_patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{1,2}[月日]',
            r'(?:明天|后天|大后天|昨天|前天)',
            r'(?:下?周[一二三四五六日天])',
            r'(?:上午|下午|晚上)\d{1,2}[点时]',
        ]
        for pattern in time_patterns:
            entities += len(re.findall(pattern, text))

        # 3. 地名模式
        location_patterns = [
            r'[一-鿿]{2,4}(?:市|省|区|县|镇)',
            r'[一-鿿]{2,6}(?:路|街|巷|弄)',
            r'[一-鿿]{2,4}(?:店|餐厅|酒店|公司)',
        ]
        for pattern in location_patterns:
            entities += len(re.findall(pattern, text))

        return entities


class OriginalCompressor:
    """Level 0: 保留原始消息，不压缩"""

    async def compress(self, text: str) -> str:
        return text


class KeyInfoCompressor:
    """Level 1: 提取关键信息 - 实体 + 意图 + 结论"""

    INTENT_KEYWORDS = {
        "meeting": ["见面", "开会", "讨论", "商讨"],
        "decision": ["决定", "选择", "确认"],
        "request": ["希望", "想要", "需要", "请"],
        "promise": ["保证", "承诺", "一定"],
    }

    async def compress(self, text: str) -> str:
        """提取关键信息"""
        # 1. 提取实体
        entities = self._extract_entities(text)

        # 2. 提取意图
        intent = self._extract_intent(text)

        # 3. 提取结论
        conclusion = self._extract_conclusion(text)

        # 4. 组合
        parts = []
        if entities:
            parts.append(f"【实体】{entities}")
        if intent:
            parts.append(f"【意图】{intent}")
        if conclusion:
            parts.append(f"【结论】{conclusion}")

        return " ".join(parts) if parts else text[:50]

    def _extract_entities(self, text: str) -> str:
        """提取实体"""
        entities = []

        # 人名
        names = re.findall(r'[一-鿿]{2,3}(?:老师|同学|先生|女士)', text)
        entities.extend(names)

        # 时间
        times = re.findall(
            r'(?:明天|后天|下周[一二三四五六日]|上午|下午)\d{0,2}[点时]?\d{0,2}分?',
            text
        )
        entities.extend(times)

        # 地点
        locations = re.findall(r'[一-鿿]{2,4}(?:店|餐厅|酒店|公司|星巴克)', text)
        entities.extend(locations)

        return "、".join(entities) if entities else ""

    def _extract_intent(self, text: str) -> str:
        """提取意图"""
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return intent_type
        return ""

    def _extract_conclusion(self, text: str) -> str:
        """提取结论"""
        # 简单策略：取最后一个句子
        sentences = text.split("。")
        last_sentence = sentences[-1].strip() if sentences else ""
        return last_sentence[:30]  # 限制长度


class SemanticCompressor:
    """Level 2: 生成语义摘要"""

    def __init__(self, llm_client=None):
        """
        初始化语义压缩器

        Args:
            llm_client: LLM 客户端（可选，用于高质量摘要）
        """
        self.llm_client = llm_client

    async def compress(self, text: str) -> str:
        """生成语义摘要"""
        # 策略1: LLM 摘要（高质量但慢）
        if self.llm_client:
            try:
                return await self._llm_summary(text)
            except Exception as e:
                logger.warning(f"LLM 摘要失败，使用规则摘要: {e}")

        # 策略2: 规则摘要（快速但简单）
        return self._rule_summary(text)

    async def _llm_summary(self, text: str) -> str:
        """使用 LLM 生成摘要"""
        prompt = f"请用一句话概括以下内容的核心意思（不超过30字）：\n{text}"

        response = await self.llm_client.generate(prompt)
        return response.strip()[:30]

    def _rule_summary(self, text: str) -> str:
        """使用规则生成摘要"""
        # 策略：取关键词 + 第一个句子
        sentences = [s.strip() for s in text.split("。") if s.strip()]
        first_sentence = sentences[0] if sentences else ""

        # 提取关键词（简单分词）
        keywords = self._extract_keywords(first_sentence)

        return "关键词：" + "、".join(keywords) if keywords else first_sentence[:30]

    def _extract_keywords(self, text: str) -> list:
        """提取关键词"""
        if not text:
            return []

        # 简单策略：取长度 > 1 的词
        # 实际项目中可以使用 jieba 分词
        words = []
        for word in text:
            if len(word) > 1 and not word.isspace():
                words.append(word)

        return words[:5]  # 最多 5 个关键词


class TopicCompressor:
    """Level 3: 提取主题标签"""

    TOPIC_KEYWORDS = {
        "工作": ["项目", "会议", "任务", "进度", "deadline", "工作"],
        "生活": ["吃饭", "睡觉", "休息", "娱乐", "生活"],
        "学习": ["学习", "课程", "考试", "作业", "学习"],
        "社交": ["朋友", "聚会", "聊天", "社交"],
        "情感": ["喜欢", "爱", "分手", "恋爱", "情感"],
    }

    async def compress(self, text: str) -> str:
        """提取主题标签"""
        # 策略1: 预定义主题匹配
        topics = self._match_topics(text)

        if topics:
            return f"[{'/'.join(topics)}]"

        # 策略2: 提取名词短语
        return self._extract_noun_phrases(text)

    def _match_topics(self, text: str) -> list:
        """匹配预定义主题"""
        matched = []
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                matched.append(topic)

        return matched[:3]  # 最多 3 个主题

    def _extract_noun_phrases(self, text: str) -> str:
        """提取名词短语（简化版）"""
        # 简化：取长度 > 1 的连续中文字符
        nouns = re.findall(r'[一-鿿]{2,}', text)

        return "[" + "/".join(nouns[:3]) + "]" if nouns else "[...]"


class AdaptiveContextCompressor:
    """自适应上下文压缩器"""

    # 压缩级别阈值
    DEFAULT_THRESHOLDS = {
        "high": 0.8,    # 高重要性：不压缩
        "medium": 0.5,  # 中等：关键信息提取
        "low": 0.3,     # 较低：语义摘要
        # < 0.3: 主题标签
    }

    def __init__(
        self,
        max_tokens: int = 4000,
        thresholds: dict = None,
        llm_client=None,
    ):
        """
        初始化压缩器

        Args:
            max_tokens: Token 预算上限
            thresholds: 压缩级别阈值
            llm_client: LLM 客户端（用于语义摘要）
        """
        self.max_tokens = max_tokens
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS

        # 初始化评分器
        self.scorer = ImportanceScorer()

        # 初始化压缩器
        self.compressors = {
            0: OriginalCompressor(),
            1: KeyInfoCompressor(),
            2: SemanticCompressor(llm_client),
            3: TopicCompressor(),
        }

    async def compress(self, messages: list, context: dict = None) -> list:
        """
        压缩消息列表

        Args:
            messages: 消息列表 [{"role": str, "content": str}, ...]
            context: 上下文信息（可选）

        Returns:
            压缩后的消息列表
        """
        if not messages:
            return []

        context = context or {}

        # 1. 计算每条消息的重要性
        scored_messages = self._score_messages(messages)

        # 2. 根据 token 预算选择压缩级别
        compressed = await self._adaptive_compress(scored_messages)

        # 3. 确保关键信息不丢失
        compressed = await self._ensure_critical_info(compressed, context)

        logger.info(
            f"上下文压缩完成: 原始 {len(messages)} 条, "
            f"压缩后 {len(compressed)} 条, "
            f"Token 节省 {self._calc_token_savings(messages, compressed):.1%}"
        )

        return [item.message for item in compressed]

    def _score_messages(self, messages: list) -> list:
        """
        为每条消息计算重要性评分

        Args:
            messages: 消息列表

        Returns:
            评分后的消息列表
        """
        scored = []
        total = len(messages)

        for i, msg in enumerate(messages):
            score = self.scorer.score(msg, i, total)

            # 根据分数决定压缩级别
            if score >= self.thresholds["high"]:
                level = 0  # 高重要性：不压缩
            elif score >= self.thresholds["medium"]:
                level = 1  # 中等：关键信息提取
            elif score >= self.thresholds["low"]:
                level = 2  # 较低：语义摘要
            else:
                level = 3  # 低：主题标签

            scored.append(ScoredMessage(message=msg, score=score, level=level, original_index=i))

        return scored

    async def _adaptive_compress(self, scored_messages: list) -> list:
        """
        根据 Token 预算自适应选择压缩策略

        Args:
            scored_messages: 评分后的消息列表

        Returns:
            压缩后的消息列表
        """
        # 1. 计算当前 Token 使用量
        current_tokens = sum(
            self._estimate_tokens(m.message["content"])
            for m in scored_messages
        )

        # 2. Token 预算充足，保持原样
        if current_tokens <= self.max_tokens:
            return scored_messages

        # 3. 需要压缩，计算目标 Token
        target_tokens = int(self.max_tokens * 0.85)  # 留 15% 余量

        # 4. 贪心策略：从低分消息开始压缩
        # 按分数升序排列（低分优先压缩）
        sorted_messages = sorted(scored_messages, key=lambda x: x.score)

        result = []
        token_budget = target_tokens

        for item in sorted_messages:
            content = item.message["content"]
            tokens = self._estimate_tokens(content)

            if token_budget <= 0:
                # Token 用完，强制压缩到最低级
                compressed_content = await self.compressors[3].compress(content)
                result.append(ScoredMessage(
                    message={"role": item.message["role"], "content": compressed_content},
                    score=item.score,
                    level=3,
                    original_index=item.original_index
                ))
            elif tokens <= token_budget:
                # Token 够用，保持原级
                token_budget -= tokens
                result.append(item)
            else:
                # Token 不够，选择更高级别压缩
                for try_level in range(item.level, 4):
                    compressed_content = await self.compressors[try_level].compress(content)
                    compressed_tokens = self._estimate_tokens(compressed_content)

                    if compressed_tokens <= token_budget:
                        token_budget -= compressed_tokens
                        result.append(ScoredMessage(
                            message={"role": item.message["role"], "content": compressed_content},
                            score=item.score,
                            level=try_level,
                            original_index=item.original_index
                        ))
                        break
                else:
                    # 所有级别都不够，强制最低级
                    compressed_content = await self.compressors[3].compress(content)
                    result.append(ScoredMessage(
                        message={"role": item.message["role"], "content": compressed_content},
                        score=item.score,
                        level=3,
                        original_index=item.original_index
                    ))

        # 恢复原始顺序
        result.sort(key=lambda x: x.original_index)

        return result

    async def _ensure_critical_info(self, compressed: list, context: dict) -> list:
        """
        确保关键信息不被压缩丢失

        Args:
            compressed: 压缩后的消息列表
            context: 上下文信息

        Returns:
            保护后的消息列表
        """
        # 1. 识别关键信息类型
        critical_patterns = {
            "decision": ["决定", "选择", "确认", "同意"],
            "commitment": ["承诺", "保证", "一定", "会"],
            "preference": ["喜欢", "偏好", "想要", "需要"],
            "constraint": ["不能", "不要", "避免", "禁止"],
        }

        # 2. 扫描压缩后的消息
        critical_info = []
        for item in compressed:
            content = item.message["content"]

            for info_type, keywords in critical_patterns.items():
                if any(kw in content for kw in keywords):
                    # 提取包含关键信息的句子
                    sentences = content.split("。")
                    for sent in sentences:
                        if any(kw in sent for kw in keywords):
                            critical_info.append({
                                "type": info_type,
                                "content": sent,
                                "original_item": item
                            })

        # 3. 如果关键信息被压缩过度，升级压缩级别
        for critical in critical_info:
            item = critical["original_item"]
            if item.level >= 2:  # 被压缩到摘要或主题级别
                # 恢复到关键信息提取级别
                original_content = item.message["content"]
                restored_content = await self.compressors[1].compress(original_content)

                item.message["content"] = restored_content
                item.level = 1

        # 4. 将关键信息添加到消息开头
        if critical_info:
            critical_summary = "【关键信息】" + "；".join(
                [f"{c['type']}: {c['content']}" for c in critical_info[:3]]
            )

            # 在第一条消息前插入
            compressed.insert(0, ScoredMessage(
                message={"role": "system", "content": critical_summary},
                score=1.0,
                level=0,
                original_index=-1
            ))

        return compressed

    def _estimate_tokens(self, text: str) -> int:
        """
        估算 Token 数量

        Args:
            text: 文本内容

        Returns:
            估算的 Token 数
        """
        if not text:
            return 0

        # 简化：中文约 1.5 字/token，英文约 4 字符/token
        chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
        other_chars = len(text) - chinese_chars

        return int(chinese_chars * 1.5 + other_chars / 4)

    def _calc_token_savings(self, original: list, compressed: list) -> float:
        """
        计算 Token 节省率

        Args:
            original: 原始消息列表
            compressed: 压缩后的消息列表

        Returns:
            节省率 (0-1)
        """
        original_tokens = sum(
            self._estimate_tokens(m["content"])
            for m in original
        )

        compressed_tokens = sum(
            self._estimate_tokens(m.message["content"])
            for m in compressed
        )

        if original_tokens == 0:
            return 0.0

        return (original_tokens - compressed_tokens) / original_tokens
