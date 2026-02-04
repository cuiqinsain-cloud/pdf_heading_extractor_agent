"""
PDF读取工具
"""

import fitz  # PyMuPDF
from typing import Dict, Any, List
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class PDFReaderTool:
    """PDF读取工具 - Agent的基础工具"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化PDF读取工具

        Args:
            config: 配置字典
        """
        self.config = config
        self.pdf_config = config.get("pdf", {})

    def read_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """
        读取PDF基本信息

        Args:
            pdf_path: PDF文件路径

        Returns:
            包含PDF信息的字典
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)

            info = {
                "file_path": pdf_path,
                "file_name": Path(pdf_path).name,
                "total_pages": len(doc),
                "metadata": {
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "subject": doc.metadata.get("subject", ""),
                    "keywords": doc.metadata.get("keywords", ""),
                },
                "has_toc": len(doc.get_toc()) > 0,
            }

            # 提取书签/目录
            if self.pdf_config.get("extract_bookmarks", True):
                info["bookmarks"] = self._extract_bookmarks(doc)

            doc.close()

            logger.info(f"成功读取PDF信息: {pdf_path} ({info['total_pages']}页)")

            return info

        except Exception as e:
            logger.error(f"读取PDF失败: {e}")
            raise

    def _extract_bookmarks(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """提取PDF书签"""
        bookmarks = []
        toc = doc.get_toc()  # [[level, title, page], ...]

        for item in toc:
            level, title, page = item
            bookmarks.append(
                {
                    "level": level,
                    "text": title,
                    "page": page,
                }
            )

        return bookmarks

    def get_page_count(self, pdf_path: str) -> int:
        """
        获取PDF页数

        Args:
            pdf_path: PDF文件路径

        Returns:
            页数
        """
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception as e:
            logger.error(f"获取页数失败: {e}")
            return 0

    def __str__(self):
        return "PDF阅读器工具：读取PDF文件的基本信息、元数据和书签"

    def __repr__(self):
        return "PDFReaderTool()"
