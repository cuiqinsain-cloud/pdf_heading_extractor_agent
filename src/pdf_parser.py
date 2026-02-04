"""
PDF解析器模块
负责解析PDF文件，提取文本内容、字体信息和布局数据
"""

import fitz  # PyMuPDF
import pdfplumber
from typing import List, Dict, Any, Optional
import logging


logger = logging.getLogger(__name__)


class TextBlock:
    """文本块数据结构"""

    def __init__(
        self,
        text: str,
        page: int,
        bbox: tuple,
        font_name: str = "",
        font_size: float = 0,
        font_flags: int = 0,
        font_color: tuple = (0, 0, 0),
    ):
        self.text = text.strip()
        self.page = page
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.font_name = font_name
        self.font_size = font_size
        self.font_flags = font_flags
        self.font_color = font_color

    @property
    def is_bold(self) -> bool:
        """判断是否为粗体"""
        return bool(self.font_flags & 2**4)

    @property
    def is_italic(self) -> bool:
        """判断是否为斜体"""
        return bool(self.font_flags & 2**1)

    @property
    def x0(self) -> float:
        return self.bbox[0]

    @property
    def y0(self) -> float:
        return self.bbox[1]

    def __repr__(self):
        return f"TextBlock(text='{self.text[:30]}...', page={self.page}, font_size={self.font_size})"


class PDFParser:
    """PDF解析器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化PDF解析器

        Args:
            config: 配置字典
        """
        self.config = config
        self.engine = config.get("parser", {}).get("engine", "pymupdf")
        self.extract_fonts = config.get("parser", {}).get("extract_fonts", True)
        self.extract_layout = config.get("parser", {}).get("extract_layout", True)

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """
        解析PDF文件

        Args:
            pdf_path: PDF文件路径

        Returns:
            包含文本块、元数据的字典
        """
        logger.info(f"开始解析PDF: {pdf_path}, 使用引擎: {self.engine}")

        if self.engine == "pymupdf":
            return self._parse_with_pymupdf(pdf_path)
        elif self.engine == "pdfplumber":
            return self._parse_with_pdfplumber(pdf_path)
        else:
            raise ValueError(f"不支持的解析引擎: {self.engine}")

    def _parse_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """使用PyMuPDF解析"""
        doc = fitz.open(pdf_path)
        text_blocks = []
        bookmarks = self._extract_bookmarks(doc)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 提取文本块及其字体信息
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
                                font_color=span.get("color", (0, 0, 0)),
                            )
                            text_blocks.append(text_block)

        doc.close()

        logger.info(f"解析完成，共提取 {len(text_blocks)} 个文本块")

        return {
            "text_blocks": text_blocks,
            "bookmarks": bookmarks,
            "total_pages": len(doc),
            "metadata": {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
            },
        }

    def _parse_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """使用pdfplumber解析"""
        text_blocks = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # 提取文本和字符信息
                chars = page.chars

                for char in chars:
                    text = char["text"].strip()
                    if not text:
                        continue

                    text_block = TextBlock(
                        text=text,
                        page=page_num + 1,
                        bbox=(char["x0"], char["top"], char["x1"], char["bottom"]),
                        font_name=char.get("fontname", ""),
                        font_size=char.get("size", 0),
                    )
                    text_blocks.append(text_block)

            total_pages = len(pdf.pages)

        logger.info(f"解析完成，共提取 {len(text_blocks)} 个文本块")

        return {
            "text_blocks": text_blocks,
            "bookmarks": [],
            "total_pages": total_pages,
            "metadata": {},
        }

    def _extract_bookmarks(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """提取PDF书签"""
        bookmarks = []
        toc = doc.get_toc()  # [[level, title, page], ...]

        for item in toc:
            level, title, page = item
            bookmarks.append({"level": level, "text": title, "page": page})

        logger.info(f"提取到 {len(bookmarks)} 个书签")
        return bookmarks
