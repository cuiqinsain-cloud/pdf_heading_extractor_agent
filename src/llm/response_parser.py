"""
LLM响应解析模块
"""

import json
import logging
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class ResponseParser:
    """LLM响应解析器"""

    @staticmethod
    def parse_heading_identification(response: str) -> Dict[str, Any]:
        """
        解析标题识别响应

        Args:
            response: LLM响应文本

        Returns:
            解析后的结构化数据
        """
        try:
            data = json.loads(response)
            return {
                "is_heading": data.get("is_heading", False),
                "confidence": data.get("confidence", 0.0),
                "level_guess": data.get("level_guess", 0),
                "reasoning": data.get("reasoning", ""),
            }
        except json.JSONDecodeError as e:
            logger.error(f"解析标题识别响应失败: {e}")
            return {"is_heading": False, "confidence": 0.0}

    @staticmethod
    def parse_level_determination(response: str) -> List[Dict[str, Any]]:
        """
        解析层级判定响应

        Args:
            response: LLM响应文本

        Returns:
            标题列表
        """
        try:
            data = json.loads(response)
            return data.get("headings", [])
        except json.JSONDecodeError as e:
            logger.error(f"解析层级判定响应失败: {e}")
            return []

    @staticmethod
    def parse_relationship_building(response: str) -> List[Dict[str, Any]]:
        """
        解析关系构建响应

        Args:
            response: LLM响应文本

        Returns:
            标题树结构
        """
        try:
            data = json.loads(response)
            return data.get("tree", [])
        except json.JSONDecodeError as e:
            logger.error(f"解析关系构建响应失败: {e}")
            return []

    @staticmethod
    def parse_reflection(response: str) -> Dict[str, Any]:
        """
        解析反思验证响应

        Args:
            response: LLM响应文本

        Returns:
            反思结果
        """
        try:
            data = json.loads(response)
            return {
                "is_complete": data.get("is_complete", True),
                "missing_headings": data.get("missing_headings", []),
                "incorrect_headings": data.get("incorrect_headings", []),
                "suggestions": data.get("suggestions", ""),
                "confidence": data.get("confidence", 1.0),
            }
        except json.JSONDecodeError as e:
            logger.error(f"解析反思响应失败: {e}")
            return {"is_complete": True, "confidence": 0.5}

    @staticmethod
    def extract_json_from_text(text: str) -> Optional[Dict]:
        """
        从文本中提取JSON（处理markdown代码块等情况）

        Args:
            text: 包含JSON的文本

        Returns:
            解析后的字典，失败返回None
        """
        try:
            # 尝试直接解析
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # 尝试提取markdown代码块中的JSON
        if "```json" in text:
            json_start = text.find("```json") + 7
            json_end = text.find("```", json_start)
            if json_end != -1:
                json_text = text[json_start:json_end].strip()
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass

        # 尝试提取普通代码块中的JSON
        if "```" in text:
            json_start = text.find("```") + 3
            json_end = text.find("```", json_start)
            if json_end != -1:
                json_text = text[json_start:json_end].strip()
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass

        logger.warning(f"无法从文本中提取有效的JSON: {text[:100]}...")
        return None
