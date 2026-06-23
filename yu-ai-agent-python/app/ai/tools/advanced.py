"""
Advanced Tools - 高级工具集

提供搜索、文件操作、网页抓取和PDF解析等高级工具
"""
import os
from pathlib import Path
from typing import Any

import httpx

from app.ai.tools.base import BaseTool, ToolParameter, ToolResult, tool_registry
from app.core.logging import get_logger

logger = get_logger(__name__)

# 项目根目录（love-and-agent）
# __file__ = .../love-and-agent/yu-ai-agent-python/app/ai/tools/advanced.py
# 需要向上 5 级到达 love-and-agent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
# 文件操作的工作目录（workspace 子目录）
WORKSPACE_DIR = PROJECT_ROOT / "workspace"


def _ensure_workspace():
    """确保工作目录存在"""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_path(file_path: str) -> Path:
    """
    将用户路径限制在项目目录内，防止路径穿越

    支持：
    - 相对路径：相对于 workspace 目录
    - 绝对路径：必须在项目根目录内

    Args:
        file_path: 用户提供的路径

    Returns:
        Path: 安全的绝对路径
    """
    _ensure_workspace()

    # 处理绝对路径
    if os.path.isabs(file_path):
        target = Path(file_path).resolve()
    else:
        # 相对路径基于 workspace 目录
        target = (WORKSPACE_DIR / file_path).resolve()

    # 确保路径在项目根目录内（防止路径穿越到系统敏感目录）
    project_root_str = str(PROJECT_ROOT.resolve())
    target_str = str(target)
    if not target_str.startswith(project_root_str):
        raise ValueError(f"路径不允许超出项目目录: {file_path}")

    return target


class SearchTool(BaseTool):
    """
    网页搜索工具

    通过搜索引擎 API 搜索互联网信息
    支持多种搜索后端（当前使用 DuckDuckGo Lite 作为默认免费搜索）
    """

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "搜索互联网信息。当需要查找实时信息、百科知识、新闻资讯等互联网内容时使用此工具。"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="搜索关键词",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type="integer",
                description="返回结果数量，默认5",
                required=False,
                default=5,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        if not query:
            return ToolResult(success=False, error="搜索关键词不能为空")

        try:
            results = await self._search_duckduckgo(query, max_results)

            if not results:
                return ToolResult(
                    success=True,
                    output="未找到相关搜索结果",
                    metadata={"count": 0},
                )

            # 格式化结果
            formatted = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                url = r.get("url", "")
                formatted.append(f"[{i}] {title}\n    {snippet}\n    链接: {url}")

            output = "\n\n".join(formatted)
            return ToolResult(
                success=True,
                output=output,
                metadata={"count": len(results)},
            )

        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return ToolResult(success=False, error=f"搜索失败: {str(e)}")

    async def _search_duckduckgo(self, query: str, max_results: int) -> list:
        """
        使用 DuckDuckGo Lite 进行搜索（免费，无需 API Key）

        Args:
            query: 搜索关键词
            max_results: 最大结果数

        Returns:
            list: 搜索结果列表
        """
        url = "https://lite.duckduckgo.com/lite/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.post(
                url,
                data={"q": query},
                headers=headers,
            )
            response.raise_for_status()

        # 解析 HTML 结果
        html = response.text
        results = []

        # 简单的 HTML 解析提取搜索结果
        import re

        # 提取结果块
        result_blocks = re.findall(
            r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>.*?'
            r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>',
            html,
            re.DOTALL,
        )

        for url, title, snippet in result_blocks[:max_results]:
            # 清理 HTML 标签
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            clean_snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            if clean_title and url:
                results.append({
                    "title": clean_title,
                    "snippet": clean_snippet,
                    "url": url,
                })

        # 备用解析：如果上面的正则没匹配到
        if not results:
            links = re.findall(r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', html)
            for url, title in links[:max_results]:
                if title.strip():
                    results.append({
                        "title": title.strip(),
                        "snippet": "",
                        "url": url,
                    })

        return results


class FileTool(BaseTool):
    """
    文件操作工具

    在安全的工作目录内进行文件读写操作
    支持文本文件的创建、读取、追加和列出目录
    """

    @property
    def name(self) -> str:
        return "file_operation"

    @property
    def description(self) -> str:
        return "操作文件。支持读取文件内容、写入文件、追加内容和列出目录。支持相对路径（相对于workspace目录）和绝对路径（项目目录内）。"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型: read(读取), write(写入), append(追加), list(列出目录)",
                required=True,
            ),
            ToolParameter(
                name="path",
                type="string",
                description="文件路径，支持相对路径（相对于workspace目录）或绝对路径（项目目录内）",
                required=True,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="写入或追加的内容（read/list操作时不需要）",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action", "")
        file_path = kwargs.get("path", "")
        content = kwargs.get("content", "")

        if not action:
            return ToolResult(success=False, error="操作类型不能为空")
        if not file_path:
            return ToolResult(success=False, error="文件路径不能为空")

        try:
            if action == "read":
                return await self._read_file(file_path)
            elif action == "write":
                return await self._write_file(file_path, content)
            elif action == "append":
                return await self._append_file(file_path, content)
            elif action == "list":
                return await self._list_dir(file_path)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作类型: {action}，可选: read, write, append, list",
                )

        except Exception as e:
            logger.error(f"File operation failed: {str(e)}")
            return ToolResult(success=False, error=f"文件操作失败: {str(e)}")

    async def _read_file(self, file_path: str) -> ToolResult:
        """读取文件内容"""
        target = _safe_path(file_path)
        if not target.exists():
            return ToolResult(success=False, error=f"文件不存在: {file_path}")
        if not target.is_file():
            return ToolResult(success=False, error=f"不是文件: {file_path}")

        # 限制文件大小（最大 1MB）
        if target.stat().st_size > 1024 * 1024:
            return ToolResult(success=False, error="文件过大（超过1MB），请使用其他工具处理")

        content = target.read_text(encoding="utf-8", errors="replace")
        return ToolResult(
            success=True,
            output=content,
            metadata={"path": file_path, "size": len(content)},
        )

    async def _write_file(self, file_path: str, content: str) -> ToolResult:
        """写入文件（覆盖）"""
        if not content:
            return ToolResult(success=False, error="写入内容不能为空")

        target = _safe_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        return ToolResult(
            success=True,
            output=f"文件写入成功: {file_path}（{len(content)} 字符）",
            metadata={"path": file_path, "size": len(content)},
        )

    async def _append_file(self, file_path: str, content: str) -> ToolResult:
        """追加内容到文件"""
        if not content:
            return ToolResult(success=False, error="追加内容不能为空")

        target = _safe_path(file_path)
        if not target.exists():
            return ToolResult(success=False, error=f"文件不存在: {file_path}")

        with open(target, "a", encoding="utf-8") as f:
            f.write(content)

        return ToolResult(
            success=True,
            output=f"内容已追加到文件: {file_path}（{len(content)} 字符）",
            metadata={"path": file_path, "appended_size": len(content)},
        )

    async def _list_dir(self, dir_path: str) -> ToolResult:
        """列出目录内容"""
        target = _safe_path(dir_path)
        if not target.exists():
            return ToolResult(success=False, error=f"目录不存在: {dir_path}")
        if not target.is_dir():
            return ToolResult(success=False, error=f"不是目录: {dir_path}")

        items = []
        for item in sorted(target.iterdir()):
            prefix = "📁" if item.is_dir() else "📄"
            size = ""
            if item.is_file():
                size_bytes = item.stat().st_size
                if size_bytes < 1024:
                    size = f" ({size_bytes}B)"
                elif size_bytes < 1024 * 1024:
                    size = f" ({size_bytes / 1024:.1f}KB)"
                else:
                    size = f" ({size_bytes / (1024 * 1024):.1f}MB)"
            items.append(f"{prefix} {item.name}{size}")

        if not items:
            output = f"目录为空: {dir_path}"
        else:
            output = f"目录 {dir_path} 的内容:\n" + "\n".join(items)

        return ToolResult(
            success=True,
            output=output,
            metadata={"count": len(items)},
        )


class WebTool(BaseTool):
    """
    网页抓取工具

    获取指定 URL 的网页内容并提取文本
    类似 Java 端 Jsoup 的功能
    """

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "获取网页内容。当需要读取特定网页的文本内容时使用此工具。输入URL，返回网页的纯文本内容。"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="url",
                type="string",
                description="要获取的网页URL",
                required=True,
            ),
            ToolParameter(
                name="max_length",
                type="integer",
                description="返回内容的最大字符数，默认5000",
                required=False,
                default=5000,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url", "")
        max_length = kwargs.get("max_length", 5000)

        if not url:
            return ToolResult(success=False, error="URL不能为空")

        # 基本 URL 校验
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            html = response.text
            text = self._extract_text(html)

            # 截断到最大长度
            if len(text) > max_length:
                text = text[:max_length] + f"\n\n... (内容已截断，总长度约 {len(text)} 字符)"

            return ToolResult(
                success=True,
                output=text,
                metadata={"url": str(response.url), "text_length": len(text)},
            )

        except httpx.TimeoutException:
            return ToolResult(success=False, error=f"网页请求超时: {url}")
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, error=f"HTTP错误 {e.response.status_code}: {url}")
        except Exception as e:
            logger.error(f"Web fetch failed: {str(e)}")
            return ToolResult(success=False, error=f"网页获取失败: {str(e)}")

    def _extract_text(self, html: str) -> str:
        """
        从 HTML 中提取纯文本

        简单但有效的 HTML → Text 转换
        """
        import re

        # 移除 script 和 style 标签及其内容
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # 移除 HTML 注释
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

        # 将块级标签转换为换行
        text = re.sub(r'<(?:br|p|div|h[1-6]|li|tr|blockquote)[^>]*/?>', '\n', text, flags=re.IGNORECASE)

        # 移除所有剩余的 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)

        # 解码 HTML 实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = re.sub(r'&#?\w+;', '', text)

        # 清理多余空白
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = text.strip()

        return text


class PdfTool(BaseTool):
    """
    PDF 解析工具

    读取 PDF 文件并提取文本内容
    支持指定页码范围
    """

    @property
    def name(self) -> str:
        return "pdf_read"

    @property
    def description(self) -> str:
        return "读取PDF文件内容。当需要提取PDF文档中的文字信息时使用此工具。"

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path",
                type="string",
                description="PDF文件路径（相对于工作目录）",
                required=True,
            ),
            ToolParameter(
                name="pages",
                type="string",
                description="页码范围，如 '1-5' 或 '1,3,5'，默认读取全部",
                required=False,
                default="",
            ),
            ToolParameter(
                name="max_length",
                type="integer",
                description="返回内容的最大字符数，默认10000",
                required=False,
                default=10000,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("path", "")
        pages_str = kwargs.get("pages", "")
        max_length = kwargs.get("max_length", 10000)

        if not file_path:
            return ToolResult(success=False, error="文件路径不能为空")

        try:
            import PyPDF2
        except ImportError:
            return ToolResult(success=False, error="PDF处理库未安装，请安装 PyPDF2")

        try:
            target = _safe_path(file_path)
            if not target.exists():
                return ToolResult(success=False, error=f"文件不存在: {file_path}")
            if not target.is_file():
                return ToolResult(success=False, error=f"不是文件: {file_path}")
            if not target.suffix.lower() == '.pdf':
                return ToolResult(success=False, error=f"不是PDF文件: {file_path}")

            # 解析页码范围
            page_numbers = self._parse_page_range(pages_str) if pages_str else None

            with open(target, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)

                # 确定要读取的页码
                if page_numbers:
                    # 过滤有效页码
                    pages_to_read = [p for p in page_numbers if 1 <= p <= total_pages]
                else:
                    pages_to_read = list(range(1, total_pages + 1))

                if not pages_to_read:
                    return ToolResult(
                        success=False,
                        error=f"指定的页码无效，PDF共 {total_pages} 页",
                    )

                # 提取文本
                text_parts = []
                for page_num in pages_to_read:
                    page = reader.pages[page_num - 1]  # PDF 页码从 0 开始
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- 第 {page_num} 页 ---\n{page_text.strip()}")

            full_text = "\n\n".join(text_parts)

            if not full_text:
                return ToolResult(
                    success=True,
                    output="PDF文件未提取到文本内容（可能是扫描件或纯图片PDF）",
                    metadata={"total_pages": total_pages, "pages_read": len(pages_to_read)},
                )

            # 截断
            truncated = False
            if len(full_text) > max_length:
                full_text = full_text[:max_length] + f"\n\n... (内容已截断，总长度约 {len(full_text)} 字符)"
                truncated = True

            return ToolResult(
                success=True,
                output=full_text,
                metadata={
                    "total_pages": total_pages,
                    "pages_read": len(pages_to_read),
                    "text_length": len(full_text),
                    "truncated": truncated,
                },
            )

        except Exception as e:
            logger.error(f"PDF read failed: {str(e)}")
            return ToolResult(success=False, error=f"PDF读取失败: {str(e)}")

    def _parse_page_range(self, pages_str: str) -> list:
        """
        解析页码范围字符串

        支持格式: "1-5", "1,3,5", "1-3,7,10-12"
        """
        pages = set()
        parts = pages_str.replace(" ", "").split(",")

        for part in parts:
            if "-" in part:
                start, end = part.split("-", 1)
                try:
                    start, end = int(start), int(end)
                    pages.update(range(start, end + 1))
                except ValueError:
                    continue
            else:
                try:
                    pages.add(int(part))
                except ValueError:
                    continue

        return sorted(pages)


def register_advanced_tools():
    """注册所有高级工具"""
    tool_registry.register(SearchTool())
    tool_registry.register(FileTool())
    tool_registry.register(WebTool())
    tool_registry.register(PdfTool())
    logger.info("Advanced tools registered: web_search, file_operation, web_fetch, pdf_read")
