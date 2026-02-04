"""
标题检测器模块
负责识别文本块中的标题并判定其层级
"""

import re
import logging
from typing import List, Dict, Any, Optional
from collections import Counter


logger = logging.getLogger(__name__)


class Heading:
    """标题数据结构"""

    def __init__(
        self,
        text: str,
        level: int,
        page: int,
        confidence: float = 1.0,
        numbering: str = "",
        font_size: float = 0,
        font_name: str = "",
    ):
        self.text = text
        self.level = level
        self.page = page
        self.confidence = confidence
        self.numbering = numbering
        self.font_size = font_size
        self.font_name = font_name
        self.children = []

    def add_child(self, child: "Heading"):
        """添加子标题"""
        self.children.append(child)

    def to_dict(self, include_confidence: bool = False, include_font_info: bool = False) -> Dict:
        """转换为字典"""
        result = {
            "level": self.level,
            "text": self.text,
            "page": self.page,
        }

        if include_confidence:
            result["confidence"] = self.confidence

        if include_font_info:
            result["font_size"] = self.font_size
            result["font_name"] = self.font_name

        if self.numbering:
            result["numbering"] = self.numbering

        if self.children:
            result["children"] = [
                child.to_dict(include_confidence, include_font_info)
                for child in self.children
            ]

        return result

    def __repr__(self):
        return f"Heading(level={self.level}, text='{self.text[:30]}...', page={self.page})"


class HeadingDetector:
    """标题检测器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化标题检测器

        Args:
            config: 配置字典
        """
        self.config = config
        self.detector_config = config.get("detector", {})
        self.methods = self.detector_config.get("methods", [])
        self.thresholds = self.detector_config.get("thresholds", {})
        self.numbering_config = self.detector_config.get("numbering", {})

        # 编译编号模式
        self.numbering_patterns = [
            re.compile(pattern)
            for pattern in self.numbering_config.get("patterns", [])
        ]

    def detect(self, parsed_data: Dict[str, Any]) -> List[Heading]:
        """
        检测标题

        Args:
            parsed_data: 解析后的PDF数据

        Returns:
            标题列表
        """
        logger.info("开始检测标题...")

        text_blocks = parsed_data["text_blocks"]
        bookmarks = parsed_data["bookmarks"]

        headings = []

        # 方法1: 使用PDF书签（最可靠）
        if "bookmark" in self.methods and bookmarks:
            logger.info("使用书签检测标题")
            bookmark_headings = self._detect_from_bookmarks(bookmarks)
            headings.extend(bookmark_headings)

        # 方法2: 基于内容分析
        if not headings or "bookmark" not in self.methods:
            logger.info("使用内容分析检测标题")
            content_headings = self._detect_from_content(text_blocks)
            headings.extend(content_headings)

        # 构建标题树
        heading_tree = self._build_heading_tree(headings)

        logger.info(f"检测完成，共找到 {len(headings)} 个标题")

        return heading_tree

    def _detect_from_bookmarks(self, bookmarks: List[Dict]) -> List[Heading]:
        """从书签中提取标题"""
        headings = []

        for bookmark in bookmarks:
            heading = Heading(
                text=bookmark["text"],
                level=bookmark["level"],
                page=bookmark["page"],
                confidence=1.0,
            )
            headings.append(heading)

        return headings

    def _detect_from_content(self, text_blocks: List[Any]) -> List[Heading]:
        """从内容中检测标题"""
        headings = []

        # 计算正文字体大小（中位数）
        font_sizes = [block.font_size for block in text_blocks if block.font_size > 0]
        if not font_sizes:
            logger.warning("无法获取字体大小信息")
            return headings

        body_font_size = sorted(font_sizes)[len(font_sizes) // 2]
        min_heading_size = body_font_size * self.thresholds.get("heading_size_ratio", 1.15)

        logger.info(f"正文字体大小: {body_font_size}, 标题最小字体: {min_heading_size}")

        # 分析每个文本块
        processed_texts = set()  # 避免重复

        for block in text_blocks:
            text = block.text.strip()

            # 跳过空文本和重复文本
            if not text or text in processed_texts:
                continue

            # 跳过过长的文本（可能是正文）
            if len(text) > 200:
                continue

            confidence = 0.0
            level = 0

            # 检测编号模式
            numbering, numbering_level = self._detect_numbering(text)
            if numbering and "numbering" in self.methods:
                confidence += 0.5
                level = numbering_level

            # 检测字体大小
            if "font_size" in self.methods and block.font_size >= min_heading_size:
                confidence += 0.3
                # 根据字体大小估计层级
                size_ratio = block.font_size / body_font_size
                if level == 0:
                    if size_ratio >= 1.8:
                        level = 1
                    elif size_ratio >= 1.5:
                        level = 2
                    elif size_ratio >= 1.2:
                        level = 3
                    else:
                        level = 4

            # 检测字体粗细
            if "font_weight" in self.methods and block.is_bold:
                confidence += 0.2

            # 检测位置（左对齐，有间距）
            if "position" in self.methods and block.x0 < 100:  # 左边距小
                confidence += 0.1

            # 判断是否为标题
            min_confidence = self.thresholds.get("min_confidence", 0.6)
            if confidence >= min_confidence and level > 0:
                max_level = self.thresholds.get("max_level", 6)
                level = min(level, max_level)

                heading = Heading(
                    text=text,
                    level=level,
                    page=block.page,
                    confidence=confidence,
                    numbering=numbering,
                    font_size=block.font_size,
                    font_name=block.font_name,
                )
                headings.append(heading)
                processed_texts.add(text)

        return headings

    def _detect_numbering(self, text: str) -> tuple[str, int]:
        """
        检测编号模式

        Returns:
            (编号字符串, 层级)
        """
        for pattern in self.numbering_patterns:
            match = pattern.match(text)
            if match:
                numbering = match.group(0)
                # 根据编号推断层级
                level = self._infer_level_from_numbering(numbering)
                return numbering, level

        return "", 0

    def _infer_level_from_numbering(self, numbering: str) -> int:
        """从编号推断层级"""
        # 计算点的数量
        dots = numbering.count(".")

        # 1. -> level 1
        # 1.1 -> level 2
        # 1.1.1 -> level 3
        if dots > 0:
            return dots

        # 第X章 -> level 1
        if "章" in numbering:
            return 1

        # (一) -> level 2 or 3
        if "(" in numbering or "）" in numbering:
            return 2

        # A. B. C. -> level 2
        if numbering[0].isupper() and len(numbering) == 2:
            return 2

        return 1

    def _build_heading_tree(self, headings: List[Heading]) -> List[Heading]:
        """构建标题树结构"""
        if not headings:
            return []

        # 按页码和出现顺序排序
        headings.sort(key=lambda h: (h.page, -h.confidence))

        # 构建树
        root_headings = []
        stack = []

        for heading in headings:
            # 找到合适的父节点
            while stack and stack[-1].level >= heading.level:
                stack.pop()

            if stack:
                # 添加为子节点
                stack[-1].add_child(heading)
            else:
                # 作为根节点
                root_headings.append(heading)

            stack.append(heading)

        return root_headings
