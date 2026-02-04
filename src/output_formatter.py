"""
输出格式化器模块
负责将标题数据格式化为不同的输出格式
"""

import json
import csv
import logging
from typing import List, Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)


class OutputFormatter:
    """输出格式化器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化输出格式化器

        Args:
            config: 配置字典
        """
        self.config = config
        self.output_config = config.get("output", {})
        self.format = self.output_config.get("format", "json")
        self.output_dir = Path(self.output_config.get("directory", "output"))
        self.include_page_numbers = self.output_config.get("include_page_numbers", True)
        self.include_confidence = self.output_config.get("include_confidence", False)
        self.include_font_info = self.output_config.get("include_font_info", False)

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def format_output(
        self,
        headings: List[Any],
        pdf_name: str,
        total_pages: int,
        format_type: str = None,
    ) -> str:
        """
        格式化输出

        Args:
            headings: 标题列表
            pdf_name: PDF文件名
            total_pages: 总页数
            format_type: 输出格式，如果为None则使用配置中的格式

        Returns:
            格式化后的字符串
        """
        format_type = format_type or self.format

        logger.info(f"格式化输出为 {format_type} 格式")

        if format_type == "json":
            return self._format_json(headings, pdf_name, total_pages)
        elif format_type == "markdown":
            return self._format_markdown(headings, pdf_name, total_pages)
        elif format_type == "txt":
            return self._format_txt(headings, pdf_name, total_pages)
        elif format_type == "csv":
            return self._format_csv(headings, pdf_name, total_pages)
        elif format_type == "all":
            # 生成所有格式
            results = {}
            for fmt in ["json", "markdown", "txt", "csv"]:
                results[fmt] = self.format_output(headings, pdf_name, total_pages, fmt)
            return results
        else:
            raise ValueError(f"不支持的输出格式: {format_type}")

    def save_output(
        self,
        content: str,
        pdf_name: str,
        format_type: str = None,
    ) -> str:
        """
        保存输出到文件

        Args:
            content: 内容
            pdf_name: PDF文件名
            format_type: 输出格式

        Returns:
            输出文件路径
        """
        format_type = format_type or self.format
        base_name = Path(pdf_name).stem
        extension = format_type

        if format_type == "markdown":
            extension = "md"

        output_path = self.output_dir / f"{base_name}_headings.{extension}"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"输出已保存到: {output_path}")
        return str(output_path)

    def _format_json(self, headings: List[Any], pdf_name: str, total_pages: int) -> str:
        """格式化为JSON"""
        json_config = self.output_config.get("json", {})
        indent = json_config.get("indent", 2)
        ensure_ascii = json_config.get("ensure_ascii", False)

        data = {
            "document": pdf_name,
            "total_pages": total_pages,
            "headings": [
                h.to_dict(self.include_confidence, self.include_font_info)
                for h in headings
            ],
        }

        return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)

    def _format_markdown(self, headings: List[Any], pdf_name: str, total_pages: int) -> str:
        """格式化为Markdown"""
        markdown_config = self.output_config.get("markdown", {})
        show_page_numbers = markdown_config.get("show_page_numbers", True)
        page_format = markdown_config.get("page_number_format", "(p.{page})")

        lines = [f"# {pdf_name} - 目录\n"]
        lines.append(f"总页数: {total_pages}\n")
        lines.append("---\n")

        def format_heading(heading: Any, indent_level: int = 0):
            # Markdown标题符号
            prefix = "#" * heading.level

            # 页码
            page_info = ""
            if show_page_numbers and self.include_page_numbers:
                page_info = " " + page_format.format(page=heading.page)

            line = f"{prefix} {heading.text}{page_info}\n"
            lines.append(line)

            # 递归处理子标题
            for child in heading.children:
                format_heading(child, indent_level + 1)

        for heading in headings:
            format_heading(heading)

        return "".join(lines)

    def _format_txt(self, headings: List[Any], pdf_name: str, total_pages: int) -> str:
        """格式化为纯文本树"""
        lines = [f"{pdf_name} - 目录\n"]
        lines.append("=" * 60 + "\n")
        lines.append(f"总页数: {total_pages}\n")
        lines.append("=" * 60 + "\n\n")

        def format_heading(heading: Any, indent_level: int = 0):
            indent = "  " * indent_level
            page_info = ""
            if self.include_page_numbers:
                page_info = f" [p.{heading.page}]"

            line = f"{indent}{'└─ ' if indent_level > 0 else ''}{heading.text}{page_info}\n"
            lines.append(line)

            # 递归处理子标题
            for child in heading.children:
                format_heading(child, indent_level + 1)

        for heading in headings:
            format_heading(heading)

        return "".join(lines)

    def _format_csv(self, headings: List[Any], pdf_name: str, total_pages: int) -> str:
        """格式化为CSV"""
        rows = [["Level", "Text", "Page", "Numbering"]]

        if self.include_confidence:
            rows[0].append("Confidence")

        if self.include_font_info:
            rows[0].extend(["Font Size", "Font Name"])

        def flatten_headings(heading: Any, parent_path: str = ""):
            path = f"{parent_path}/{heading.text}" if parent_path else heading.text

            row = [
                heading.level,
                heading.text,
                heading.page,
                heading.numbering or "",
            ]

            if self.include_confidence:
                row.append(f"{heading.confidence:.2f}")

            if self.include_font_info:
                row.extend([heading.font_size, heading.font_name])

            rows.append(row)

            for child in heading.children:
                flatten_headings(child, path)

        for heading in headings:
            flatten_headings(heading)

        # 转换为CSV字符串
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        return output.getvalue()
