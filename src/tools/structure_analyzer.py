"""
结构分析工具
"""

from typing import Dict, Any, List
from collections import Counter
import logging
import re


logger = logging.getLogger(__name__)


class StructureAnalyzerTool:
    """结构分析工具 - 分析PDF的结构特征"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化结构分析工具

        Args:
            config: 配置字典
        """
        self.config = config

    def analyze_font_statistics(self, text_blocks: List[Any]) -> Dict[str, Any]:
        """
        分析字体统计信息

        Args:
            text_blocks: 文本块列表

        Returns:
            字体统计信息
        """
        font_sizes = [block.font_size for block in text_blocks if block.font_size > 0]

        if not font_sizes:
            return {}

        size_counter = Counter(font_sizes)
        most_common_size = size_counter.most_common(1)[0][0]

        return {
            "body_font_size": most_common_size,
            "font_size_distribution": dict(size_counter.most_common()),
            "min_size": min(font_sizes),
            "max_size": max(font_sizes),
            "avg_size": sum(font_sizes) / len(font_sizes),
        }

    def detect_numbering_patterns(self, text_blocks: List[Any]) -> List[Dict[str, Any]]:
        """
        检测编号模式

        Args:
            text_blocks: 文本块列表

        Returns:
            编号模式列表
        """
        patterns = [
            (r"^\d+\.", "数字点号"),
            (r"^\d+\.\d+\.?", "两级编号"),
            (r"^\d+\.\d+\.\d+\.?", "三级编号"),
            (r"^第[一二三四五六七八九十百]+章", "章节"),
            (r"^[A-Z]\.", "字母编号"),
            (r"^\([一二三四五六七八九十]+\)", "括号编号"),
        ]

        detected = []

        for block in text_blocks:
            for pattern, name in patterns:
                if re.match(pattern, block.text):
                    detected.append(
                        {
                            "text": block.text,
                            "pattern": name,
                            "page": block.page,
                        }
                    )
                    break

        return detected

    def analyze_layout_features(self, text_blocks: List[Any]) -> Dict[str, Any]:
        """
        分析布局特征

        Args:
            text_blocks: 文本块列表

        Returns:
            布局特征
        """
        if not text_blocks:
            return {}

        # 左边距统计
        left_margins = [block.bbox[0] for block in text_blocks]
        left_margin_counter = Counter([round(m, -1) for m in left_margins])  # 取整到10

        # 行间距分析（简化版）
        line_gaps = []
        for i in range(1, len(text_blocks)):
            if text_blocks[i].page == text_blocks[i - 1].page:
                gap = text_blocks[i].bbox[1] - text_blocks[i - 1].bbox[3]
                if gap > 0:
                    line_gaps.append(gap)

        return {
            "common_left_margins": dict(left_margin_counter.most_common(5)),
            "avg_line_gap": sum(line_gaps) / len(line_gaps) if line_gaps else 0,
        }

    def get_document_summary(
        self, pdf_info: Dict[str, Any], text_blocks: List[Any]
    ) -> str:
        """
        获取文档摘要（用于LLM）

        Args:
            pdf_info: PDF基本信息
            text_blocks: 文本块列表

        Returns:
            文档摘要文本
        """
        font_stats = self.analyze_font_statistics(text_blocks)
        numbering = self.detect_numbering_patterns(text_blocks)

        summary = f"""文档信息:
- 文件名: {pdf_info.get('file_name', '')}
- 总页数: {pdf_info.get('total_pages', 0)}
- 正文字体大小: {font_stats.get('body_font_size', 0):.1f}pt
- 检测到编号模式: {len(numbering)}个
- 有书签: {'是' if pdf_info.get('has_toc', False) else '否'}
"""

        if numbering:
            summary += "\n编号示例:\n"
            for item in numbering[:5]:
                summary += f"  - {item['text']} (第{item['page']}页)\n"

        return summary

    def __str__(self):
        return "结构分析工具：分析PDF的字体、编号、布局等结构特征"

    def __repr__(self):
        return "StructureAnalyzerTool()"
