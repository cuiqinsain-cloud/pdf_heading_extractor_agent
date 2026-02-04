"""
PDF标题提取Agent - 核心类 (基于LLM)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .llm import LLMClient, PromptManager, ResponseParser
from .tools import PDFReaderTool, TextExtractorTool, StructureAnalyzerTool
from .memory.context_manager import ContextManager
from .output.formatter import OutputFormatter


logger = logging.getLogger(__name__)
console = Console()


class PDFHeadingExtractorAgent:
    """
    PDF多级标题提取Agent (LLM驱动)

    这是一个智能Agent，利用LLM的理解能力来提取PDF中的多级标题。
    Agent能够：
    - 自主规划提取策略
    - 调用工具获取PDF信息
    - 使用LLM进行语义理解
    - 反思和验证结果
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化Agent

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)

        # 设置日志
        self._setup_logging()

        # 初始化LLM客户端
        self.llm_client = LLMClient(self.config)

        # 初始化Prompt管理器
        self.prompt_manager = PromptManager(self.config)

        # 初始化响应解析器
        self.response_parser = ResponseParser()

        # 初始化工具
        self.pdf_reader = PDFReaderTool(self.config)
        self.text_extractor = TextExtractorTool(self.config)
        self.structure_analyzer = StructureAnalyzerTool(self.config)

        # 初始化记忆管理器
        self.memory = ContextManager(self.config)

        # 初始化输出格式化器
        self.formatter = OutputFormatter(self.config)

        # Agent配置
        self.agent_config = self.config.get("agent", {})
        self.max_iterations = self.agent_config.get("max_iterations", 10)
        self.enable_reflection = self.agent_config.get("enable_reflection", True)
        self.verbose = self.agent_config.get("enable_verbose", True)

        # 统计信息
        self.stats = {
            "llm_calls": 0,
            "tokens_used": 0,
            "tool_calls": 0,
        }

        logger.info("PDF标题提取Agent初始化完成")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config

    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.get("logging", {})
        level = log_config.get("level", "INFO")
        log_file = log_config.get("file", "logs/agent.log")

        # 创建日志目录
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 配置日志
        handlers = [logging.FileHandler(log_file, encoding="utf-8")]

        if log_config.get("console", True):
            handlers.append(logging.StreamHandler())

        logging.basicConfig(
            level=getattr(logging, level),
            format=log_config.get(
                "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            handlers=handlers,
        )

    def extract_headings(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        提取PDF中的多级标题（Agent主流程）

        Args:
            pdf_path: PDF文件路径

        Returns:
            标题树结构
        """
        logger.info(f"=" * 60)
        logger.info(f"开始处理PDF: {pdf_path}")
        logger.info(f"=" * 60)

        try:
            # Phase 1: 文档分析
            console.print("\n[bold cyan]Phase 1:[/] 文档分析...")
            pdf_info, text_blocks = self._phase_document_analysis(pdf_path)

            # Phase 2: 标题识别
            console.print("\n[bold cyan]Phase 2:[/] 标题识别...")
            candidate_headings = self._phase_heading_identification(
                text_blocks, pdf_info
            )

            # Phase 3: 层级判定
            console.print("\n[bold cyan]Phase 3:[/] 层级判定...")
            headings_with_level = self._phase_level_determination(candidate_headings)

            # Phase 4: 关系构建
            console.print("\n[bold cyan]Phase 4:[/] 关系构建...")
            heading_tree = self._phase_relationship_building(headings_with_level)

            # Phase 5: 反思验证（可选）
            if self.enable_reflection:
                console.print("\n[bold cyan]Phase 5:[/] 反思验证...")
                heading_tree = self._phase_reflection(heading_tree, pdf_info)

            # 保存结果
            self._save_results(heading_tree, pdf_path, pdf_info)

            # 输出统计
            self._print_statistics()

            logger.info(f"处理完成！提取了 {len(heading_tree)} 个顶级标题")

            return heading_tree

        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)
            raise

    def _phase_document_analysis(
        self, pdf_path: str
    ) -> tuple[Dict[str, Any], List[Any]]:
        """Phase 1: 文档分析"""
        self.stats["tool_calls"] += 1

        # 使用工具读取PDF信息
        pdf_info = self.pdf_reader.read_pdf_info(pdf_path)
        console.print(f"  ✓ PDF信息: {pdf_info['total_pages']}页")

        # 提取文本块
        self.stats["tool_calls"] += 1
        text_blocks = self.text_extractor.extract_text_blocks(pdf_path)
        console.print(f"  ✓ 提取文本块: {len(text_blocks)}个")

        # 结构分析
        self.stats["tool_calls"] += 1
        doc_summary = self.structure_analyzer.get_document_summary(
            pdf_info, text_blocks
        )

        # LLM分析文档整体结构
        system_prompt = self.prompt_manager.get_system_prompt()
        analysis_prompt = f"""请分析这个PDF文档的整体结构特征：

{doc_summary}

请简要说明：
1. 这个文档的类型（论文、报告、书籍等）
2. 可能的标题组织方式
3. 识别标题时需要注意的特征
"""

        self.stats["llm_calls"] += 1
        analysis = self.llm_client.invoke(system_prompt, analysis_prompt)

        console.print(f"  ✓ LLM文档分析完成")
        logger.info(f"文档分析结果: {analysis}")

        # 记忆保存
        self.memory.add_context("document_analysis", analysis)

        return pdf_info, text_blocks

    def _phase_heading_identification(
        self, text_blocks: List[Any], pdf_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Phase 2: 标题识别"""
        candidate_headings = []

        # 如果有书签，优先使用
        bookmarks = pdf_info.get("bookmarks", [])
        if bookmarks:
            console.print(f"  ✓ 使用PDF书签: {len(bookmarks)}个")
            for bookmark in bookmarks:
                candidate_headings.append(
                    {
                        "text": bookmark["text"],
                        "page": bookmark["page"],
                        "level": bookmark["level"],
                        "confidence": 1.0,
                        "source": "bookmark",
                    }
                )

        # 如果书签足够，直接返回
        if len(candidate_headings) > 10:
            console.print(f"  ✓ 书签数量充足，跳过LLM分析")
            return candidate_headings

        # 使用LLM进行内容分析（补充书签或独立识别）
        console.print(f"  → 使用LLM分析候选文本块...")

        # 预筛选：只分析可能是标题的文本块
        candidates = []
        for i, block in enumerate(text_blocks):
            # 标题特征：短文本、大字体、独立行
            if 5 < len(block.text) < 100 and block.font_size > 10:
                candidates.append((i, block))

        console.print(f"  → 预筛选出 {len(candidates)} 个候选文本块")

        # 限制分析数量
        max_analyze = min(len(candidates), 50)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("识别中...", total=max_analyze)

            for idx, (i, block) in enumerate(candidates[:max_analyze]):
                # 获取上下文
                context = self.text_extractor.get_context(text_blocks, i, window=2)

                # 使用LLM判断
                heading_prompt = self.prompt_manager.get_heading_identification_prompt(
                    block.text, context
                )

                try:
                    self.stats["llm_calls"] += 1
                    response = self.llm_client.invoke(
                        self.prompt_manager.get_system_prompt(), heading_prompt
                    )

                    # 解析响应
                    result = self.response_parser.extract_json_from_text(response)

                    if result and result.get("is_heading"):
                        candidate_headings.append(
                            {
                                "text": block.text,
                                "page": block.page,
                                "level": result.get("level_guess", 0),
                                "confidence": result.get("confidence", 0.5),
                                "source": "llm",
                                "font_size": block.font_size,
                            }
                        )

                except Exception as e:
                    logger.warning(f"LLM识别失败: {e}")

                progress.update(task, advance=1)

        console.print(f"  ✓ 识别候选标题: {len(candidate_headings)}个")

        return candidate_headings

    def _phase_level_determination(
        self, candidate_headings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Phase 3: 层级判定"""
        # 如果标题已经有层级信息（来自书签），直接使用
        has_level = all(h.get("level", 0) > 0 for h in candidate_headings)

        if has_level:
            console.print(f"  ✓ 书签已包含层级信息，直接使用")
            return candidate_headings

        # 否则使用LLM进行层级判定（分批处理）
        console.print(f"  → 使用LLM判定层级（分批处理）...")

        batch_size = 50
        all_results = []

        for i in range(0, len(candidate_headings), batch_size):
            batch = candidate_headings[i:i+batch_size]
            console.print(f"  → 处理批次 {i//batch_size + 1}/{(len(candidate_headings)-1)//batch_size + 1}")

            level_prompt = self.prompt_manager.get_level_determination_prompt(batch)

            self.stats["llm_calls"] += 1
            response = self.llm_client.invoke(
                self.prompt_manager.get_system_prompt(), level_prompt
            )

            # 解析响应
            result = self.response_parser.extract_json_from_text(response)

            if result and "headings" in result:
                all_results.extend(result["headings"])
            else:
                all_results.extend(batch)

        console.print(f"  ✓ 层级判定完成: {len(all_results)}个标题")
        return all_results

    def _phase_relationship_building(
        self, headings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Phase 4: 关系构建"""
        # 根据层级构建树形结构
        console.print(f"  → 根据层级构建树形结构...")

        # 为每个标题添加ID和children字段
        for idx, heading in enumerate(headings):
            heading["id"] = idx
            heading["children"] = []

        # 构建父子关系
        stack = []  # 用于追踪父节点
        for heading in headings:
            level = heading.get("level", 1)

            # 找到父节点：弹出所有层级>=当前层级的节点
            while stack and stack[-1]["level"] >= level:
                stack.pop()

            if stack:
                # 添加到父节点的children
                parent = stack[-1]
                parent["children"].append(heading["id"])

            stack.append(heading)

        # 在过滤前添加页码范围信息（基于所有节点，包括将被过滤的节点）
        # 这样可以保留原始的章节边界信息
        self._add_page_ranges(headings)

        # 统计顶级标题数量
        top_level_count = sum(1 for h in headings if not any(h["id"] in other.get("children", []) for other in headings))

        console.print(f"  ✓ 关系构建完成: {top_level_count}个顶级标题, 共{len(headings)}个标题")
        return headings

    def _phase_reflection(
        self, heading_tree: List[Dict[str, Any]], pdf_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Phase 5: 反思验证（简化版）"""
        # 统计验证
        total_headings = len(heading_tree)
        top_level = sum(1 for h in heading_tree if not any(h["id"] in other.get("children", []) for other in heading_tree))
        max_level = max(h.get("level", 1) for h in heading_tree) if heading_tree else 0

        # 简单的完整性检查
        is_complete = total_headings > 0 and top_level > 0
        confidence = 1.0 if all(h.get("source") == "bookmark" for h in heading_tree) else 0.8

        console.print(f"  ✓ 验证完成: 完整性={is_complete}, 置信度={confidence:.2f}")
        console.print(f"  → 统计: {total_headings}个标题, {top_level}个顶级, {max_level}级深度")

        return heading_tree

    def _save_results(
        self, heading_tree: List[Dict[str, Any]], pdf_path: str, pdf_info: Dict[str, Any]
    ):
        """保存结果"""
        # 过滤财务报表相关节点
        # 注意：页码范围信息已在过滤前计算，基于所有节点（包括被过滤的节点）
        # 这样可以保留原始的章节边界，更准确地反映实际内容范围
        filtered_tree = self._filter_financial_statements(heading_tree)

        output_path = self.formatter.save(
            filtered_tree, Path(pdf_path).name, pdf_info.get("total_pages", 0)
        )
        console.print(f"\n[bold green]✓ 结果已保存到:[/] {output_path}")
        console.print(f"  → 过滤后保留 {len(filtered_tree)} 个财务报表相关节点")

    def _add_page_ranges(self, headings: List[Dict[str, Any]]):
        """为每个标题添加页码范围信息（下一个同级标题的页码）"""
        # 构建父子关系映射
        parent_map = {}  # {child_id: parent_id}
        for heading in headings:
            for child_id in heading.get("children", []):
                parent_map[child_id] = heading["id"]

        # 为每个标题找到下一个同级标题
        for i, heading in enumerate(headings):
            heading_id = heading["id"]
            heading_level = heading.get("level", 1)
            parent_id = parent_map.get(heading_id)

            # 查找下一个同级标题
            next_sibling_page = None

            # 从当前标题之后开始查找
            for j in range(i + 1, len(headings)):
                next_heading = headings[j]
                next_id = next_heading["id"]
                next_level = next_heading.get("level", 1)
                next_parent_id = parent_map.get(next_id)

                # 判断是否为同级标题（相同父节点和相同层级）
                if next_level == heading_level and next_parent_id == parent_id:
                    next_sibling_page = next_heading.get("page")
                    break

                # 如果遇到更高层级的标题，说明当前标题没有后续同级标题了
                if next_level < heading_level:
                    break

            # 添加页码范围信息
            heading["next_sibling_page"] = next_sibling_page

            # 如果有下一个同级标题，计算页码范围
            if next_sibling_page is not None:
                current_page = heading.get("page", 0)
                # 包容方式：包含到下一个标题所在页（不包括下一个标题页）
                # 但考虑到标题可能在页面中部，我们包含到下一个标题所在页的前一页
                #
                # 特殊处理：如果下一个标题在当前页的下一页（相邻页），则包含到下一个标题所在页
                # 例如：合并利润表(81页) -> 母公司利润表(83页)，则合并利润表应覆盖81-83页
                # 因为第83页的标题可能在页面中部，上半部分仍是合并利润表的内容
                if next_sibling_page - current_page <= 2:
                    # 相邻或间隔一页，包含到下一个标题所在页
                    end_page = next_sibling_page
                else:
                    # 间隔较远，保守处理，到下一个标题前一页
                    end_page = next_sibling_page - 1

                # 确保 end >= start
                end_page = max(current_page, end_page)
                heading["page_range"] = {
                    "start": current_page,
                    "end": end_page
                }
            else:
                # 没有下一个同级标题，范围到文档末尾或父节点结束
                heading["page_range"] = {
                    "start": heading.get("page", 0),
                    "end": None  # 表示到文档末尾或父节点结束
                }

        console.print(f"  ✓ 页码范围信息已添加")

    def _filter_financial_statements(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出财务报表相关的节点"""
        keywords = [
            "合并资产负债表",
            "合并利润表",
            "合并现金流量表",
            "合并财务报表项目注释",
            "财务报表附注",
            "报表附注",
            "附注"
        ]

        # 构建ID到标题的映射
        heading_map = {h["id"]: h for h in headings}

        # 找到匹配的节点及其所有子孙节点
        result_ids = set()

        def add_node_and_children(node_id):
            """递归添加节点及其所有子节点"""
            if node_id in result_ids:
                return
            result_ids.add(node_id)
            node = heading_map.get(node_id)
            if node:
                for child_id in node.get("children", []):
                    add_node_and_children(child_id)

        # 查找匹配的节点
        for heading in headings:
            text = heading.get("text", "")
            if any(kw in text for kw in keywords):
                add_node_and_children(heading["id"])

        # 返回过滤后的节点
        return [h for h in headings if h["id"] in result_ids]

    def _print_statistics(self):
        """打印统计信息"""
        console.print(f"\n[bold]统计信息:[/]")
        console.print(f"  LLM调用次数: {self.stats['llm_calls']}")
        console.print(f"  工具调用次数: {self.stats['tool_calls']}")

    def get_reasoning_trace(self) -> str:
        """获取Agent的推理轨迹"""
        return self.memory.get_all_context()

    def get_tool_usage(self) -> Dict[str, int]:
        """获取工具使用统计"""
        return {
            "pdf_reader": 1,
            "text_extractor": 1,
            "structure_analyzer": 1,
            "llm_calls": self.stats["llm_calls"],
        }
