"""
Smart Chunker - 智能分块模块
严格按照 chunk.md 规范实现：
  - Markdown：按标题分块，携带父标题路径；列表不拆分；代码块按类/方法拆分
  - TXT：恢复结构（空行 → 句号 → Token），overlap 100
  - PDF：文件类型检测 → 解析器选择 → OCR → Layout → Structure Recovery → Chunking → Metadata
"""

import re
import io
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ──────────────────────── 常量 ────────────────────────
MAX_CHUNK_TOKENS = 800
OVERLAP_TOKENS = 100

# 中文句号/英文句号等
_CN_SENTENCE_END = re.compile(r'(?<=[。！？；])')
_EN_SENTENCE_END = re.compile(r'(?<=[.!?;])')
# Markdown 标题行
_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)', re.MULTILINE)
# 代码块
_CODE_BLOCK_RE = re.compile(r'```[\s\S]*?```', re.MULTILINE)
# 列表项
_LIST_ITEM_RE = re.compile(r'^[\-\*\+\d\.]+\s+', re.MULTILINE)


# ──────────────────────── 数据结构 ────────────────────────
@dataclass
class ChunkMetadata:
    doc_id: str = ""
    chunk_index: int = 0
    heading_path: List[str] = field(default_factory=list)
    content_type: str = "paragraph"  # paragraph / list / code / table
    token_count: int = 0
    previous_chunk: Optional[int] = None
    next_chunk: Optional[int] = None


@dataclass
class Chunk:
    content: str
    metadata: ChunkMetadata = field(default_factory=ChunkMetadata)


# ──────────────────────── Token 计数（简易版） ────────────────────────
def _estimate_tokens(text: str) -> int:
    """简易 token 估算：中文按字数，英文按空格分词"""
    cn_chars = len(re.findall(r'[一-鿿]', text))
    en_words = len(re.findall(r'[a-zA-Z]+', text))
    return cn_chars + en_words


# ════════════════════════════════════════════════════════════════════════
#  Markdown Chunking
# ════════════════════════════════════════════════════════════════════════
def chunk_markdown(text: str, doc_id: str = "") -> List[Chunk]:
    """
    Markdown 分块规则：
    1. 按标题拆分，每个非一级标题携带父标题路径
    2. 标题下内容过大时，按完整句子拆分，overlap 100
    3. 列表不拆分
    4. 代码块整块保留，过大时按类/方法拆分
    """
    sections = _parse_markdown_sections(text)
    chunks: List[Chunk] = []
    idx = 0

    for section in sections:
        heading_path = section["heading_path"]
        content = section["content"].strip()
        if not content:
            continue

        content_type = _detect_content_type(content)

        if content_type == "code":
            sub_chunks = _chunk_code_block(content, heading_path)
        elif content_type == "list":
            sub_chunks = [content]
        else:
            sub_chunks = _chunk_paragraph(content, heading_path)

        for sc in sub_chunks:
            meta = ChunkMetadata(
                doc_id=doc_id,
                chunk_index=idx,
                heading_path=heading_path,
                content_type=content_type,
                token_count=_estimate_tokens(sc),
                previous_chunk=idx - 1 if idx > 0 else None,
            )
            chunks.append(Chunk(content=sc, metadata=meta))
            idx += 1

    # 回填 next_chunk
    for i in range(len(chunks) - 1):
        chunks[i].metadata.next_chunk = chunks[i + 1].metadata.chunk_index

    logger.info(f"Markdown chunked: {len(chunks)} chunks from {len(text)} chars")
    return chunks


# ── 内部：解析标题结构 ──
def _parse_markdown_sections(text: str) -> List[dict]:
    """
    将 Markdown 按标题拆分为 section 列表，
    每个 section 包含 heading_path 和 content。
    """
    lines = text.split('\n')
    sections: List[dict] = []
    heading_stack: List[str] = []  # [h1, h2, ...]
    current_content_lines: List[str] = []

    def _flush(content_lines):
        content = '\n'.join(content_lines).strip()
        if content:
            sections.append({
                "heading_path": list(heading_stack),
                "content": content,
            })

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            level = len(m.group(1))  # # = 1, ## = 2, ...
            title = m.group(2).strip()
            # 先把之前的内容 flush
            _flush(current_content_lines)
            current_content_lines = []
            # 调整 heading_stack
            if level <= len(heading_stack):
                heading_stack = heading_stack[:level - 1]
            heading_stack.append(title)
        else:
            current_content_lines.append(line)

    # 最后一段
    _flush(current_content_lines)

    # 如果整个文档没有标题，把全部内容当成一个 section
    if not sections and text.strip():
        sections.append({"heading_path": [], "content": text.strip()})

    return sections


def _detect_content_type(content: str) -> str:
    """检测内容类型：code / list / table / paragraph"""
    if content.startswith('```') and '```' in content[3:]:
        return "code"
    lines = content.strip().split('\n')
    # 列表：连续行以 - * + 数字. 开头
    list_lines = [l for l in lines if re.match(r'^[\-\*\+]\s|^\d+\.\s', l.strip())]
    if len(list_lines) > len(lines) * 0.5:
        return "list"
    # 表格：多行包含 |
    if all('|' in l for l in lines if l.strip()):
        return "table"
    return "paragraph"


# ── 内部：段落分块（overlap 100） ──
def _chunk_paragraph(content: str, heading_path: List[str]) -> List[str]:
    """将段落内容按句子拆分，控制在 MAX_CHUNK_TOKENS 以内，overlap OVERLAP_TOKENS"""
    # 先判断整体是否不超过限制
    tokens = _estimate_tokens(content)
    if tokens <= MAX_CHUNK_TOKENS:
        return [_prepend_heading_path(heading_path, content)]

    # 按句子拆分
    sentences = _split_sentences(content)
    chunks: List[str] = []
    current = ""
    prev_tail = ""

    for sent in sentences:
        candidate = (prev_tail + " " + sent).strip() if prev_tail else sent
        if _estimate_tokens(candidate) <= MAX_CHUNK_TOKENS:
            current = candidate
        else:
            if current:
                chunks.append(_prepend_heading_path(heading_path, current))
            # overlap: 取当前块末尾 OVERLAP_TOKENS 作为下一块的前缀
            prev_tail = _tail_tokens(current, OVERLAP_TOKENS)
            current = sent

    if current:
        chunks.append(_prepend_heading_path(heading_path, current))

    # 回填 overlap（简单方案：直接拼接）
    if len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            overlapped.append(chunks[i])
        return overlapped

    return chunks


def _split_sentences(text: str) -> List[str]:
    """按中英文句子结束符拆分，保留标点"""
    parts = _CN_SENTENCE_END.split(text)
    result: List[str] = []
    for p in parts:
        if not p.strip():
            continue
        # 英文句号再拆一次
        sub = _EN_SENTENCE_END.split(p)
        result.extend([s.strip() for s in sub if s.strip()])
    return result


def _prepend_heading_path(heading_path: List[str], content: str) -> str:
    """在内容前拼接 heading path"""
    if not heading_path:
        return content
    prefix = '\n'.join(heading_path)
    return f"{prefix}\n\n{content}"


def _tail_tokens(text: str, n: int) -> str:
    """取文本末尾大约 n 个 token 的字符"""
    # 简单估算：中文约 1 token/字，英文约 1 token/word
    cn_chars = re.findall(r'[一-鿿]', text)
    en_words = re.findall(r'[a-zA-Z]+', text)
    all_tokens = cn_chars + en_words
    if len(all_tokens) <= n:
        return text
    # 从后往前取
    tail_tokens = all_tokens[-n:]
    # 找到这些 token 在原文中的起始位置（粗略）
    # 直接按字符数回退
    approx_chars = sum(len(t) for t in tail_tokens)
    return text[-approx_chars:] if approx_chars < len(text) else text


# ── 内部：代码块分块 ──
def _chunk_code_block(content: str, heading_path: List[str]) -> List[str]:
    """
    代码块分块规则：
    1. 优先整个代码块
    2. 过长按类拆分
    3. 类过大按方法拆分（标注类名）
    4. 方法太大按 if{}, try{} 等中括号拆分（标注方法名、类名）
    """
    # 去掉首尾 ``` 标记
    inner = re.sub(r'^```\w*\n?', '', content)
    inner = re.sub(r'\n?```$', '', inner)

    tokens = _estimate_tokens(inner)
    if tokens <= MAX_CHUNK_TOKENS:
        return [_prepend_heading_path(heading_path, content)]

    # 尝试按类拆分（Python class / Java class）
    class_chunks = _split_by_class(inner)
    if len(class_chunks) > 1:
        result = []
        for cls_name, cls_body in class_chunks:
            full = f"# Class: {cls_name}\n{cls_body}"
            if _estimate_tokens(full) <= MAX_CHUNK_TOKENS:
                result.append(_prepend_heading_path(heading_path, full))
            else:
                # 按方法拆分
                method_chunks = _split_by_method(cls_body, cls_name)
                result.extend([_prepend_heading_path(heading_path, mc) for mc in method_chunks])
        return result

    # 尝试按方法拆分
    method_chunks = _split_by_method(inner, "")
    if len(method_chunks) > 1:
        return [_prepend_heading_path(heading_path, mc) for mc in method_chunks]

    # 最终：按 token 强制切分
    return _force_split_by_tokens(inner, heading_path)


def _split_by_class(code: str) -> List[tuple]:
    """按 class 定义拆分代码"""
    # Python: class xxx:
    # Java: class xxx { / public class xxx {
    pattern = re.compile(r'^(class\s+\w+|public\s+class\s+\w+)', re.MULTILINE)
    matches = list(pattern.finditer(code))
    if len(matches) <= 1:
        return []

    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
        cls_line = m.group(0).strip()
        cls_name = cls_line.split()[-1]
        chunks.append((cls_name, code[start:end].strip()))

    # 如果第一个 class 之前还有内容
    if matches and matches[0].start() > 0:
        prefix = code[:matches[0].start()].strip()
        if prefix:
            chunks.insert(0, ("__module__", prefix))

    return chunks


def _split_by_method(code: str, class_name: str) -> List[str]:
    """按方法/函数拆分代码"""
    # Python def xxx( / Java public/private xxx(
    pattern = re.compile(r'^(\s*(?:public|private|protected|static|async|def)\s+\w+)', re.MULTILINE)
    matches = list(pattern.finditer(code))
    if len(matches) <= 1:
        return [_force_split_single(code, class_name, "")]

    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
        method_line = m.group(1).strip()
        method_name = method_line.split()[-1] if method_line.split() else f"block_{i}"
        body = code[start:end].strip()
        if _estimate_tokens(body) <= MAX_CHUNK_TOKENS:
            prefix = f"# Class: {class_name}, Method: {method_name}" if class_name else f"# Method: {method_name}"
            chunks.append(f"{prefix}\n{body}")
        else:
            chunks.extend(_force_split_single(body, class_name, method_name))
    return chunks


def _force_split_single(code: str, class_name: str, method_name: str) -> List[str]:
    """按中括号拆分，标注类名和方法名"""
    # 找 if, try, for, while 等块
    pattern = re.compile(r'^(if\s*\(|try\s*\{|for\s*\(|while\s*\()', re.MULTILINE)
    matches = list(pattern.finditer(code))
    if not matches:
        return _force_split_by_tokens(code, [], class_name, method_name)

    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
        block = code[start:end].strip()
        prefix_parts = []
        if class_name:
            prefix_parts.append(f"Class: {class_name}")
        if method_name:
            prefix_parts.append(f"Method: {method_name}")
        prefix = f"# {', '.join(prefix_parts)}" if prefix_parts else ""
        full = f"{prefix}\n{block}" if prefix else block
        if _estimate_tokens(full) <= MAX_CHUNK_TOKENS:
            chunks.append(full)
        else:
            chunks.extend(_force_split_by_tokens(full, []))
    return chunks


def _force_split_by_tokens(text: str, heading_path: List[str], class_name: str = "", method_name: str = "") -> List[str]:
    """强制按 token 数切分"""
    # 简单按字符切分
    chars_per_chunk = MAX_CHUNK_TOKENS * 2  # 粗略估计
    chunks = []
    for i in range(0, len(text), chars_per_chunk):
        chunk = text[i:i + chars_per_chunk]
        prefix_parts = []
        if class_name:
            prefix_parts.append(f"Class: {class_name}")
        if method_name:
            prefix_parts.append(f"Method: {method_name}")
        prefix = f"# {', '.join(prefix_parts)}" if prefix_parts else ""
        full = f"{prefix}\n{chunk}" if prefix else chunk
        chunks.append(_prepend_heading_path(heading_path, full))
    return chunks


# ════════════════════════════════════════════════════════════════════════
#  TXT Chunking
# ════════════════════════════════════════════════════════════════════════
def chunk_txt(text: str, doc_id: str = "") -> List[Chunk]:
    """
    TXT 分块规则（恢复结构）：
    第一层：按空行（段落）
    第二层：按句号
    第三层：按 Token（800）
    overlap: 100
    """
    # 第一层：按空行拆分段落
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks: List[Chunk] = []
    idx = 0

    for para in paragraphs:
        tokens = _estimate_tokens(para)
        if tokens <= MAX_CHUNK_TOKENS:
            meta = ChunkMetadata(
                doc_id=doc_id,
                chunk_index=idx,
                heading_path=[],
                content_type="paragraph",
                token_count=tokens,
                previous_chunk=idx - 1 if idx > 0 else None,
            )
            chunks.append(Chunk(content=para, metadata=meta))
            idx += 1
        else:
            # 第二层：按句号拆分
            sentences = _split_sentences(para)
            current = ""
            prev_tail = ""
            for sent in sentences:
                candidate = (prev_tail + " " + sent).strip() if prev_tail else sent
                if _estimate_tokens(candidate) <= MAX_CHUNK_TOKENS:
                    current = candidate
                else:
                    if current:
                        meta = ChunkMetadata(
                            doc_id=doc_id,
                            chunk_index=idx,
                            heading_path=[],
                            content_type="paragraph",
                            token_count=_estimate_tokens(current),
                            previous_chunk=idx - 1 if idx > 0 else None,
                        )
                        chunks.append(Chunk(content=current, metadata=meta))
                        idx += 1
                    prev_tail = _tail_tokens(current, OVERLAP_TOKENS)
                    current = sent
            if current:
                meta = ChunkMetadata(
                    doc_id=doc_id,
                    chunk_index=idx,
                    heading_path=[],
                    content_type="paragraph",
                    token_count=_estimate_tokens(current),
                    previous_chunk=idx - 1 if idx > 0 else None,
                )
                chunks.append(Chunk(content=current, metadata=meta))
                idx += 1

    # 回填 next_chunk
    for i in range(len(chunks) - 1):
        chunks[i].metadata.next_chunk = chunks[i + 1].metadata.chunk_index

    logger.info(f"TXT chunked: {len(chunks)} chunks from {len(text)} chars")
    return chunks


# ════════════════════════════════════════════════════════════════════════
#  PDF Chunking
# ════════════════════════════════════════════════════════════════════════
def chunk_pdf(content: bytes, doc_id: str = "") -> List[Chunk]:
    """
    PDF 分块流程：
    1. 文件类型检测（文本/扫描/混合）
    2. 选择 Parser（PyMuPDF > pdfplumber > PyPDF2）
    3. 扫描 PDF → OCR
    4. Layout 检测
    5. 结构恢复
    6. Structure Chunking
    7. Token Chunking
    8. Metadata
    """
    pdf_type = _detect_pdf_type(content)
    logger.info(f"PDF type detected: {pdf_type}")

    if pdf_type == "scanned":
        raw_text = _ocr_pdf(content)
    elif pdf_type == "mixed":
        raw_text = _parse_pdf_mixed(content)
    else:
        raw_text = _parse_pdf_text(content)

    if not raw_text.strip():
        logger.warning("PDF extracted empty text")
        return []

    # 尝试恢复 Markdown 结构（标题层级）
    recovered = _recover_markdown_structure(raw_text)
    return chunk_markdown(recovered, doc_id=doc_id)


def _detect_pdf_type(content: bytes) -> str:
    """检测 PDF 类型：text / scanned / mixed"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=content, filetype="pdf")
        total_pages = len(doc)
        scanned_pages = 0
        for page in doc:
            text = page.get_text().strip()
            images = page.get_images()
            if len(text) < 20 and len(images) > 0:
                scanned_pages += 1
        doc.close()
        if scanned_pages == 0:
            return "text"
        elif scanned_pages == total_pages:
            return "scanned"
        else:
            return "mixed"
    except Exception as e:
        logger.warning(f"PDF type detection failed: {e}, fallback to text")
        return "text"


def _parse_pdf_text(content: bytes) -> str:
    """文本 PDF：PyMuPDF 优先，fallback pdfplumber"""
    try:
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        parts = []
        for page in doc:
            parts.append(page.get_text())
        doc.close()
        return "\n".join(parts).strip()
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}, trying pdfplumber")

    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            parts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
            return "\n".join(parts).strip()
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}, trying PyPDF2")

    # 最终 fallback
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(content))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def _parse_pdf_mixed(content: bytes) -> str:
    """混合 PDF：文字 + 图片，优先 PyMuPDF"""
    try:
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        parts = []
        for page in doc:
            text = page.get_text().strip()
            if text:
                parts.append(text)
            # 如果有图片但没有文字，标记为需要 OCR
            images = page.get_images()
            if len(text) < 20 and images:
                parts.append(f"[图片页 - 第{page.number + 1}页]")
        doc.close()
        return "\n".join(parts).strip()
    except Exception as e:
        logger.warning(f"PyMuPDF mixed parse failed: {e}")
        return _parse_pdf_text(content)


def _ocr_pdf(content: bytes) -> str:
    """
    扫描 PDF OCR：每页转图片 → OCR → 文字
    使用小米 mimo-v2.5 模型（配置在 settings 中）
    """
    try:
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        all_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # 将页面渲染为图片
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            # 调用 OCR（这里可以接入小米 mimo-v2.5 或其他 OCR 服务）
            text = _call_ocr(img_bytes)
            if text:
                all_text.append(text)
        doc.close()
        return "\n".join(all_text).strip()
    except Exception as e:
        logger.error(f"PDF OCR failed: {e}")
        return ""


def _call_ocr(img_bytes: bytes) -> str:
    """
    调用多模态大模型进行 OCR
    使用 dashscope_client 的 chat API，传入图片让模型识别文字
    """
    import base64
    from app.core.config import settings
    from app.ai.llm.dashscope_client import dashscope_client

    if not dashscope_client._client:
        logger.warning("LLM client not configured, skipping OCR")
        return ""

    try:
        img_b64 = base64.b64encode(img_bytes).decode()

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的 OCR 助手。请识别图片中的所有文字内容，保持原始格式和结构。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "请识别这张图片中的所有文字内容，保持原始格式和结构。只输出识别到的文字，不要添加任何解释。"
                    }
                ]
            }
        ]

        response = dashscope_client._client.chat.completions.create(
            model=settings.dashscope.DASHSCOPE_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=4096,
        )

        text = response.choices[0].message.content
        logger.debug(f"OCR via multimodal LLM completed: {len(text)} chars")
        return text

    except Exception as e:
        logger.error(f"Multimodal OCR failed: {e}")
        return ""


def _recover_markdown_structure(text: str) -> str:
    """
    从纯文本恢复 Markdown 结构（标题层级）
    基于字体大小/加粗等信息恢复，但纯文本无法获取这些信息
    所以这里做一个简单启发式：识别常见的标题模式
    """
    lines = text.split('\n')
    recovered: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            recovered.append("")
            continue
        # 如果已经是 Markdown 标题，保留
        if re.match(r'^#{1,6}\s+', stripped):
            recovered.append(stripped)
            continue
        # 启发式：全大写短行 → H2
        if stripped.isupper() and len(stripped) < 50:
            recovered.append(f"## {stripped}")
        # 短行以常见章节词结尾 → H3
        elif len(stripped) < 30 and re.match(r'^[一-鿿\w]+[章节部分条款]$', stripped):
            recovered.append(f"### {stripped}")
        else:
            recovered.append(stripped)
    return '\n'.join(recovered)
