"""
文件内容提取服务
支持: Markdown, TXT, PDF
"""

import io
import logging

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text(filename: str, content: bytes) -> str:
    """
    根据文件名后缀提取文本内容

    Args:
        filename: 文件名
        content: 文件二进制内容

    Returns:
        提取后的纯文本

    Raises:
        ValueError: 不支持的文件类型或提取失败
    """
    lower = filename.lower()

    if lower.endswith(".md") or lower.endswith(".markdown"):
        return _extract_markdown(content)
    elif lower.endswith(".txt"):
        return _extract_txt(content)
    elif lower.endswith(".pdf"):
        return _extract_pdf(content)
    else:
        raise ValueError(f"不支持的文件类型: {filename}")


def _extract_markdown(content: bytes) -> str:
    """Markdown 文件直接读取文本"""
    return content.decode("utf-8", errors="ignore").strip()


def _extract_txt(content: bytes) -> str:
    """TXT 文件直接读取文本"""
    return content.decode("utf-8", errors="ignore").strip()


def _extract_pdf(content: bytes) -> str:
    """PDF 文件提取文本"""
    try:
        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts).strip()
    except Exception as e:
        logger.error(f"PDF 文本提取失败: {e}")
        raise ValueError(f"PDF 文本提取失败: {e}")
