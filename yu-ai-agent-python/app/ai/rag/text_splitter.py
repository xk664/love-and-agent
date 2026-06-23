"""
Text Splitter - 文本分块工具
统一入口，根据文件类型调用不同的分块策略：
  - Markdown → chunk_markdown
  - TXT     → chunk_txt
  - PDF     → chunk_pdf
"""

from typing import List

from app.core.config import settings
from app.core.logging import get_logger
from app.ai.rag.chunker import (
    Chunk,
    chunk_markdown,
    chunk_txt,
    chunk_pdf,
)

logger = get_logger(__name__)


def split_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    filename: str = "",
    file_content: bytes = None,
) -> List[str]:
    """
    统一分块入口

    Args:
        text: 已提取的纯文本（MD/TXT 使用）
        chunk_size: 未使用，保留兼容
        chunk_overlap: 未使用，保留兼容
        filename: 文件名（用于判断类型）
        file_content: 原始文件二进制内容（PDF 时使用）

    Returns:
        切分后的文本块列表
    """
    if not text or not text.strip():
        return []

    lower = filename.lower()

    if lower.endswith(".pdf") and file_content:
        chunks = chunk_pdf(file_content)
    elif lower.endswith(".md") or lower.endswith(".markdown"):
        chunks = chunk_markdown(text)
    elif lower.endswith(".txt"):
        chunks = chunk_txt(text)
    else:
        # fallback：旧逻辑
        chunks = _legacy_split(text, chunk_size, chunk_overlap)

    # 将 Chunk 对象列表转为纯文本列表
    return [c.content for c in chunks]


def split_text_with_metadata(
    text: str,
    filename: str = "",
    file_content: bytes = None,
) -> List[Chunk]:
    """
    带元数据的分块入口（向量化时可保存 metadata）

    Returns:
        Chunk 对象列表，包含 content 和 metadata
    """
    if not text or not text.strip():
        return []

    lower = filename.lower()

    if lower.endswith(".pdf") and file_content:
        return chunk_pdf(file_content)
    elif lower.endswith(".md") or lower.endswith(".markdown"):
        return chunk_markdown(text)
    elif lower.endswith(".txt"):
        return chunk_txt(text)
    else:
        # fallback
        return [Chunk(content=c) for c in _legacy_split(text, None, None)]


def _legacy_split(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[str]:
    """旧分块逻辑（fallback）"""
    import re

    chunk_size = chunk_size or settings.rag.RAG_CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.rag.RAG_CHUNK_OVERLAP

    if len(text) <= chunk_size:
        return [text.strip()]

    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk = (current_chunk + "\n" + paragraph).strip() if current_chunk else paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(paragraph) > chunk_size:
                sub_chunks = _split_paragraph_legacy(paragraph, chunk_size, chunk_overlap)
                chunks.extend(sub_chunks)
                current_chunk = ""
            else:
                current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    if chunk_overlap > 0 and len(chunks) > 1:
        chunks = _add_overlap_legacy(chunks, chunk_overlap)

    return chunks


def _split_paragraph_legacy(paragraph: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """旧：超长段落按句子切分"""
    import re
    _SENTENCE_DELIMITERS = re.compile(r'(?<=[。！？.!?\n])')
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
            if len(sentence) > chunk_size:
                for i in range(0, len(sentence), chunk_size - chunk_overlap):
                    chunks.append(sentence[i:i + chunk_size])
                current_chunk = ""
            else:
                current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def _add_overlap_legacy(chunks: List[str], overlap: int) -> List[str]:
    """旧：重叠"""
    if len(chunks) <= 1:
        return chunks
    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-overlap:]
        result.append(prev_tail + chunks[i])
    return result
