"""
文本提取工具
"""

import fitz  # PyMuPDF
from typing import Dict, Any, List
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """文本块数据结构"""

    text: str
    page: int
    bbox: tuple  # (x0, y0, x1, y1)
    font_name: str = ""
    font_size: float = 0.0
    font_flags: int = 0

    @property
    def is_bold(self) -> bool:
        """是否为粗体"""
        return bool(self.font_flags & 2**4)

    @property
    def is_italic(self) -> bool:
        """是否为斜体"""
        return bool(self.font_flags & 2**1)


class TextExtractorTool:
    """文本提取工具 - 提取PDF中的文本块及元数据"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化文本提取工具

        Args:
            config: 配置字典
        """
        self.config = config
        self.pdf_config = config.get("pdf", {})
        self.batch_size = self.pdf_config.get("batch_size", 10)

    def extract_text_blocks(
        self, pdf_path: str, start_page: int = 0, end_page: int = None
    ) -> List[TextBlock]:
        """
        提取文本块

        Args:
            pdf_path: PDF文件路径
            start_page: 起始页（0-based）
            end_page: 结束页（不包含），None表示到最后

        Returns:
            文本块列表
        """
        try:
            doc = fitz.open(pdf_path)
            text_blocks = []

            if end_page is None:
                end_page = len(doc)

            for page_num in range(start_page, min(end_page, len(doc))):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]

                for block in blocks:
                    if block["type"] == 0:  # 文本块
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span["text"].strip()
                                if not text:
                                    continue

                                text_block = TextBlock(
                                    text=text,
                                    page=page_num + 1,
                                    bbox=span["bbox"],
                                    font_name=span.get("font", ""),
                                    font_size=span.get("size", 0),
                                    font_flags=span.get("flags", 0),
                                )
                                text_blocks.append(text_block)

            doc.close()

            logger.info(f"提取了 {len(text_blocks)} 个文本块 (页{start_page+1}-{end_page})")

            return text_blocks

        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            raise

    def extract_page_text(self, pdf_path: str, page_num: int) -> str:
        """
        提取指定页的纯文本

        Args:
            pdf_path: PDF文件路径
            page_num: 页码（1-based）

        Returns:
            页面文本
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]
            text = page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"提取页面文本失败: {e}")
            return ""

    def get_context(
        self, text_blocks: List[TextBlock], current_index: int, window: int = 2
    ) -> str:
        """
        获取文本块的上下文

        Args:
            text_blocks: 文本块列表
            current_index: 当前文本块索引
            window: 上下文窗口大小

        Returns:
            上下文文本
        """
        start = max(0, current_index - window)
        end = min(len(text_blocks), current_index + window + 1)

        context_blocks = text_blocks[start:end]
        return "\n".join([block.text for block in context_blocks])

    def __str__(self):
        return "文本提取工具：从PDF中提取文本块及其字体、位置等元数据"

    def __repr__(self):
        return "TextExtractorTool()"
