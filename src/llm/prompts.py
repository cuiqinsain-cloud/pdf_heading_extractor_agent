"""
Prompt模板管理模块
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging


logger = logging.getLogger(__name__)


class PromptManager:
    """Prompt模板管理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化Prompt管理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.prompt_config = config.get("prompts", {})
        self.language = self.prompt_config.get("language", "chinese")
        self.style = self.prompt_config.get("style", "professional")
        self.use_cot = self.prompt_config.get("use_cot", True)
        self.num_examples = self.prompt_config.get("num_examples", 3)

        # 加载自定义Prompts
        custom_dir = self.prompt_config.get("custom_prompts_dir", "prompts/")
        self.custom_prompts = self._load_custom_prompts(custom_dir)

        logger.info(f"Prompt管理器初始化完成: {self.language}/{self.style}")

    def _load_custom_prompts(self, custom_dir: str) -> Dict[str, str]:
        """加载自定义Prompt文件"""
        prompts = {}
        prompt_path = Path(custom_dir)

        if prompt_path.exists():
            for file in prompt_path.glob("*.txt"):
                prompt_name = file.stem
                with open(file, "r", encoding="utf-8") as f:
                    prompts[prompt_name] = f.read()
                logger.info(f"加载自定义Prompt: {prompt_name}")

        return prompts

    def get_system_prompt(self) -> str:
        """获取系统角色Prompt"""
        if self.language == "chinese":
            return """你是一个专业的PDF文档分析专家，擅长识别和提取文档中的标题结构。

你的能力包括:
1. 准确识别PDF文档中的各级标题
2. 理解标题的语义和层级关系
3. 区分标题与普通正文
4. 构建完整的标题树结构

你的工作原则:
- 基于上下文理解，而不仅仅依赖格式
- 保持标题的完整性和准确性
- 正确判断层级关系
- 对不确定的情况给出置信度评估
"""
        else:
            return """You are a professional PDF document analyst, skilled at identifying and extracting heading structures from documents.

Your capabilities include:
1. Accurately identify headings at all levels in PDF documents
2. Understand semantic and hierarchical relationships of headings
3. Distinguish headings from regular body text
4. Build complete heading tree structures

Your working principles:
- Base analysis on contextual understanding, not just formatting
- Maintain completeness and accuracy of headings
- Correctly determine hierarchical relationships
- Provide confidence assessments for uncertain cases
"""

    def get_heading_identification_prompt(
        self, text_block: str, context: Optional[str] = None
    ) -> str:
        """
        获取标题识别Prompt

        Args:
            text_block: 待分析的文本块
            context: 上下文（前后文）

        Returns:
            完整的Prompt
        """
        if self.language == "chinese":
            prompt = f"""任务: 判断以下文本是否为标题

文本: "{text_block}"
"""
            if context:
                prompt += f"\n上下文:\n{context}\n"

            if self.use_cot:
                prompt += """
请按照以下步骤进行分析:
1. 观察文本特征（长度、格式、编号等）
2. 分析语义内容（是否为概括性描述）
3. 考虑上下文关系
4. 给出最终判断

输出格式:
{
    "is_heading": true/false,
    "confidence": 0.0-1.0,
    "level_guess": 1-6 (如果是标题),
    "reasoning": "你的分析过程"
}
"""
            else:
                prompt += """
输出格式:
{
    "is_heading": true/false,
    "confidence": 0.0-1.0,
    "level_guess": 1-6 (如果是标题)
}
"""
        else:
            # English version
            prompt = f"""Task: Determine if the following text is a heading

Text: "{text_block}"
"""
            if context:
                prompt += f"\nContext:\n{context}\n"

            prompt += """
Output format:
{
    "is_heading": true/false,
    "confidence": 0.0-1.0,
    "level_guess": 1-6 (if is heading)
}
"""

        return prompt

    def get_level_determination_prompt(self, headings: List[Dict[str, Any]]) -> str:
        """
        获取层级判定Prompt

        Args:
            headings: 已识别的标题列表

        Returns:
            完整的Prompt
        """
        if self.language == "chinese":
            prompt = """任务: 为以下标题确定准确的层级（1-6级）

标题列表:
"""
            for i, heading in enumerate(headings, 1):
                prompt += f"{i}. {heading.get('text', '')}\n"

            prompt += """
分析要点:
1. 标题的编号模式（如1, 1.1, 1.1.1）
2. 标题的语义范围（越概括层级越高）
3. 标题之间的逻辑关系
4. 文档的整体结构

输出格式:
{
    "headings": [
        {
            "text": "标题文本",
            "level": 1-6,
            "reasoning": "层级判定理由"
        },
        ...
    ]
}
"""
        else:
            # English version
            prompt = """Task: Determine accurate levels (1-6) for the following headings

Headings:
"""
            for i, heading in enumerate(headings, 1):
                prompt += f"{i}. {heading.get('text', '')}\n"

            prompt += """
Output format:
{
    "headings": [
        {
            "text": "heading text",
            "level": 1-6,
            "reasoning": "reason for level determination"
        },
        ...
    ]
}
"""

        return prompt

    def get_relationship_building_prompt(self, headings: List[Dict[str, Any]]) -> str:
        """
        获取关系构建Prompt

        Args:
            headings: 带层级的标题列表

        Returns:
            完整的Prompt
        """
        if self.language == "chinese":
            prompt = """任务: 构建标题之间的父子关系

标题列表（按出现顺序）:
"""
            for i, heading in enumerate(headings):
                prompt += f"{i}. [L{heading['level']}] {heading['text']}\n"

            prompt += """
规则:
1. 子标题紧跟在父标题之后
2. 子标题的层级必须比父标题高（数字更大）
3. 同级标题是兄弟关系

输出格式:
{
    "tree": [
        {
            "id": 0,
            "text": "标题文本",
            "level": 1,
            "children": [1, 2]  # 子标题的ID列表
        },
        ...
    ]
}
"""
        else:
            # English version (similar structure)
            prompt = """Task: Build parent-child relationships between headings

Headings (in order):
"""
            for i, heading in enumerate(headings):
                prompt += f"{i}. [L{heading['level']}] {heading['text']}\n"

            prompt += """
Output format:
{
    "tree": [
        {
            "id": 0,
            "text": "heading text",
            "level": 1,
            "children": [1, 2]
        },
        ...
    ]
}
"""

        return prompt

    def get_reflection_prompt(self, result: Dict[str, Any]) -> str:
        """
        获取反思验证Prompt

        Args:
            result: 当前提取结果

        Returns:
            完整的Prompt
        """
        if self.language == "chinese":
            prompt = f"""任务: 反思和验证标题提取结果

当前提取的标题结构:
{result}

请检查:
1. 是否有遗漏的标题？
2. 层级关系是否合理？
3. 是否有误判的标题？
4. 标题是否完整？

输出格式:
{{
    "is_complete": true/false,
    "missing_headings": ["可能遗漏的标题"],
    "incorrect_headings": ["可能误判的标题"],
    "suggestions": "改进建议",
    "confidence": 0.0-1.0
}}
"""
        else:
            # English version
            prompt = f"""Task: Reflect on and validate heading extraction results

Current heading structure:
{result}

Check:
1. Are there any missing headings?
2. Are the hierarchy relationships reasonable?
3. Are there any incorrectly identified headings?
4. Are the headings complete?

Output format:
{{
    "is_complete": true/false,
    "missing_headings": ["possibly missing headings"],
    "incorrect_headings": ["possibly incorrect headings"],
    "suggestions": "improvement suggestions",
    "confidence": 0.0-1.0
}}
"""

        return prompt

    def get_few_shot_examples(self) -> List[Dict[str, Any]]:
        """获取Few-shot示例"""
        if self.language == "chinese":
            examples = [
                {
                    "input": "1. 引言",
                    "output": {
                        "is_heading": True,
                        "level": 1,
                        "reasoning": "有明确编号1.，内容简洁概括，是一级标题",
                    },
                },
                {
                    "input": "1.1 研究背景",
                    "output": {
                        "is_heading": True,
                        "level": 2,
                        "reasoning": "编号1.1表示是1的子标题，为二级标题",
                    },
                },
                {
                    "input": "本文研究了机器学习在自然语言处理中的应用，通过实验验证了模型的有效性。",
                    "output": {
                        "is_heading": False,
                        "reasoning": "文本较长，是完整的句子描述，不是标题",
                    },
                },
            ]
        else:
            examples = [
                {
                    "input": "1. Introduction",
                    "output": {
                        "is_heading": True,
                        "level": 1,
                        "reasoning": "Clear numbering 1., concise content, first-level heading",
                    },
                },
                {
                    "input": "1.1 Background",
                    "output": {
                        "is_heading": True,
                        "level": 2,
                        "reasoning": "Numbering 1.1 indicates sub-heading of 1, second-level heading",
                    },
                },
            ]

        return examples[: self.num_examples]
