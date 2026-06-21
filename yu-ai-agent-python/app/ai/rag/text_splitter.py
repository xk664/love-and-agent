"""
Text Splitter - 文本分块工具
将长文本按语义边界切分为适合向量化的小块
"""
import re
from typing import List

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 句子结束符：中文标点 + 英文标点 + 换行
_SENTENCE_DELIMITERS = re.compile(r'(?<=[。！？.!?\n])')


def split_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[str]:
    """
    将文本按语义边界切分为多个块

    Args:
        text: 待切分的文本
        chunk_size: 每块的最大字符数（默认从配置读取）
        chunk_overlap: 块之间的重叠字符数（默认从配置读取）

    Returns:
        切分后的文本块列表
    """
    if not text or not text.strip():
        return []

    chunk_size = chunk_size or settings.rag.RAG_CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.rag.RAG_CHUNK_OVERLAP

    # 如果文本长度小于 chunk_size，直接返回
    if len(text) <= chunk_size:
        return [text.strip()]

    # 先按段落切分（双换行）
    paragraphs = re.split(r'\n\s*\n', text)

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # 如果当前块加上新段落不超过 chunk_size，合并
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk = (current_chunk + "\n" + paragraph).strip() if current_chunk else paragraph
        else:
            # 当前块已满，保存
            if current_chunk:
                chunks.append(current_chunk)

            # 如果段落本身超过 chunk_size，需要按句子进一步切分
            if len(paragraph) > chunk_size:
                sub_chunks = _split_paragraph(paragraph, chunk_size, chunk_overlap)
                chunks.extend(sub_chunks)
                current_chunk = ""
            else:
                current_chunk = paragraph

    # 处理最后一个块
    if current_chunk:
        chunks.append(current_chunk)

    # 添加重叠（如果配置了 overlap）
    if chunk_overlap > 0 and len(chunks) > 1:
        chunks = _add_overlap(chunks, chunk_overlap)

    logger.debug(f"Text split: {len(text)} chars → {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks


def _split_paragraph(paragraph: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """将超长段落按句子切分"""
    sentences = _SENTENCE_DELIMITERS.split(paragraph)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)

            # 如果单个句子仍然超过 chunk_size，强制按字符切分
            if len(sentence) > chunk_size:
                for i in range(0, len(sentence), chunk_size - chunk_overlap):
                    chunks.append(sentence[i:i + chunk_size])
                current_chunk = ""
            else:
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _add_overlap(chunks: List[str], overlap: int) -> List[str]:
    """为相邻块添加重叠内容"""
    if len(chunks) <= 1:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        # 取前一个块的末尾 overlap 个字符
        prev_tail = chunks[i - 1][-overlap:]
        # 将重叠内容添加到当前块的开头
        result.append(prev_tail + chunks[i])

    return result
