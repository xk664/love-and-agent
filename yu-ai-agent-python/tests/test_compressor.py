"""
测试自适应上下文压缩策略
"""

import asyncio
from app.ai.memory.compressor import (
    AdaptiveContextCompressor,
    ImportanceScorer,
    KeyInfoCompressor,
    TopicCompressor,
)


def test_importance_scorer():
    """测试重要性评分器"""
    scorer = ImportanceScorer()

    # 测试消息
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "user", "content": "我决定明天下午两点在星巴克和张老师见面"},
        {"role": "assistant", "content": "好的，我帮你记住了"},
        {"role": "user", "content": "今天天气不错"},
        {"role": "user", "content": "我下周要结婚了，需要准备婚礼"},
    ]

    total = len(messages)
    for i, msg in enumerate(messages):
        score = scorer.score(msg, i, total)
        print(f"消息 {i+1}: {msg['content'][:20]}... -> score={score:.3f}")


def test_key_info_compressor():
    """测试关键信息提取"""
    compressor = KeyInfoCompressor()

    text = "我决定明天下午两点在星巴克和张老师见面讨论项目进度"
    result = asyncio.run(compressor.compress(text))
    print(f"原文: {text}")
    print(f"压缩: {result}")


def test_topic_compressor():
    """测试主题标签提取"""
    compressor = TopicCompressor()

    texts = [
        "我决定明天下午两点在星巴克和张老师见面讨论项目进度",
        "今天和朋友出去吃饭聊天",
        "我要学习 Python 编程课程",
    ]

    for text in texts:
        result = asyncio.run(compressor.compress(text))
        print(f"原文: {text[:30]}...")
        print(f"标签: {result}")
        print()


def test_adaptive_compressor():
    """测试自适应压缩器"""
    # 创建压缩器，设置 Token 预算
    compressor = AdaptiveContextCompressor(max_tokens=150)

    # 模拟对话（较长的消息）
    messages = [
        {"role": "user", "content": "你好，我想咨询一下恋爱问题"},
        {"role": "assistant", "content": "你好，我是恋爱大师，很高兴为你服务"},
        {"role": "user", "content": "我女朋友最近总是不回我消息，我很焦虑，我们已经在一起三年了"},
        {"role": "assistant", "content": "这种情况很常见，你先别着急，我们需要分析一下原因"},
        {"role": "user", "content": "我们在一起三年了，最近她经常说忙，不知道是不是有什么问题"},
        {"role": "assistant", "content": "三年的感情确实很珍贵，我们需要分析一下原因，看看是不是沟通出现了问题"},
        {"role": "user", "content": "我决定下周和她好好谈谈，把问题说清楚"},
        {"role": "assistant", "content": "这个决定很好，沟通是解决问题的关键，建议选择一个合适的时间"},
        {"role": "user", "content": "你觉得我应该什么时候找她谈比较好呢？"},
        {"role": "assistant", "content": "建议选择一个双方都轻松的时间，比如周末下午，这样可以好好聊一聊"},
    ]

    # 压缩
    compressed = asyncio.run(compressor.compress(messages))

    print(f"原始消息数: {len(messages)}")
    print(f"压缩后消息数: {len(compressed)}")
    print()

    for i, msg in enumerate(compressed):
        print(f"{i+1}. [{msg['role']}] {msg['content'][:60]}...")


def test_token_savings():
    """测试 Token 节省率"""
    compressor = AdaptiveContextCompressor(max_tokens=1000)

    messages = [
        {"role": "user", "content": "你好"},
        {"role": "user", "content": "我决定明天下午两点在星巴克和张老师见面"},
        {"role": "assistant", "content": "好的"},
        {"role": "user", "content": "今天天气不错"},
        {"role": "user", "content": "我下周要结婚了"},
    ]

    # 计算原始 Token
    original_tokens = sum(
        compressor._estimate_tokens(m["content"])
        for m in messages
    )

    # 压缩
    compressed = asyncio.run(compressor.compress(messages))

    # 计算压缩后 Token
    compressed_tokens = sum(
        compressor._estimate_tokens(m["content"])
        for m in compressed
    )

    savings = (original_tokens - compressed_tokens) / original_tokens

    print(f"原始 Token: {original_tokens}")
    print(f"压缩后 Token: {compressed_tokens}")
    print(f"节省率: {savings:.1%}")


if __name__ == "__main__":
    print("=" * 50)
    print("测试重要性评分器")
    print("=" * 50)
    test_importance_scorer()

    print()
    print("=" * 50)
    print("测试关键信息提取")
    print("=" * 50)
    test_key_info_compressor()

    print()
    print("=" * 50)
    print("测试主题标签提取")
    print("=" * 50)
    test_topic_compressor()

    print()
    print("=" * 50)
    print("测试自适应压缩器")
    print("=" * 50)
    test_adaptive_compressor()

    print()
    print("=" * 50)
    print("测试 Token 节省率")
    print("=" * 50)
    test_token_savings()
