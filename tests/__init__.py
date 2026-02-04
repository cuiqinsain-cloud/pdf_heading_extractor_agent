"""
测试文件
"""

import pytest
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agent import PDFHeadingExtractorAgent
from src.heading_detector import HeadingDetector


class TestPDFHeadingExtractorAgent:
    """测试Agent主类"""

    def test_agent_initialization(self):
        """测试Agent初始化"""
        config_path = Path(__file__).parent.parent / "config.yaml"
        agent = PDFHeadingExtractorAgent(config_path=str(config_path))

        assert agent is not None
        assert agent.parser is not None
        assert agent.detector is not None
        assert agent.formatter is not None

    def test_load_config(self):
        """测试配置加载"""
        config_path = Path(__file__).parent.parent / "config.yaml"
        agent = PDFHeadingExtractorAgent(config_path=str(config_path))

        assert "parser" in agent.config
        assert "detector" in agent.config
        assert "output" in agent.config


class TestHeadingDetector:
    """测试标题检测器"""

    def test_detect_numbering(self):
        """测试编号检测"""
        config = {
            "detector": {
                "numbering": {
                    "patterns": [
                        r"^\d+\.",
                        r"^\d+\.\d+\.?",
                        r"^\d+\.\d+\.\d+\.?",
                        r"^第[一二三四五六七八九十百]+章",
                    ]
                }
            }
        }

        detector = HeadingDetector(config)

        # 测试不同的编号模式
        test_cases = [
            ("1. 引言", "1.", 1),
            ("1.1 背景", "1.1", 2),
            ("1.1.1 研究动机", "1.1.1", 3),
            ("第一章 概述", "第一章", 1),
        ]

        for text, expected_numbering, expected_level in test_cases:
            numbering, level = detector._detect_numbering(text)
            assert numbering == expected_numbering, f"Failed for: {text}"
            assert level == expected_level, f"Level mismatch for: {text}"

    def test_infer_level_from_numbering(self):
        """测试从编号推断层级"""
        config = {"detector": {}}
        detector = HeadingDetector(config)

        test_cases = [
            ("1.", 1),
            ("1.1", 2),
            ("1.1.1", 3),
            ("1.1.1.1", 4),
            ("第一章", 1),
        ]

        for numbering, expected_level in test_cases:
            level = detector._infer_level_from_numbering(numbering)
            assert level == expected_level, f"Failed for: {numbering}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
