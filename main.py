"""
PDF标题提取Agent - 主入口 (LLM驱动版本)
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import PDFHeadingExtractorAgent


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PDF多级标题提取Agent (基于LLM)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提取PDF标题
  python main.py document.pdf

  # 使用自定义配置
  python main.py document.pdf --config custom_config.yaml

  # 禁用反思验证（加快速度）
  python main.py document.pdf --no-reflection

  # 查看详细日志
  python main.py document.pdf --verbose
        """,
    )

    parser.add_argument(
        "pdf_file",
        help="PDF文件路径",
    )

    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="配置文件路径（默认: config.yaml）",
    )

    parser.add_argument(
        "--no-reflection",
        action="store_true",
        help="禁用反思验证阶段",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="显示详细日志",
    )

    parser.add_argument(
        "--show-reasoning",
        action="store_true",
        help="显示Agent的推理过程",
    )

    args = parser.parse_args()

    try:
        print("=" * 60)
        print("PDF多级标题提取Agent (LLM驱动)")
        print("=" * 60)

        # 检查PDF文件
        if not Path(args.pdf_file).exists():
            print(f"\n错误: PDF文件不存在: {args.pdf_file}")
            sys.exit(1)

        # 初始化Agent
        print(f"\n正在初始化Agent...")
        agent = PDFHeadingExtractorAgent(config_path=args.config)

        # 覆盖配置
        if args.no_reflection:
            agent.enable_reflection = False
            print("  → 已禁用反思验证")

        if args.verbose:
            import logging

            logging.getLogger().setLevel(logging.DEBUG)

        # 执行提取
        print(f"\n开始处理: {args.pdf_file}")
        headings = agent.extract_headings(args.pdf_file)

        # 显示推理过程
        if args.show_reasoning:
            print("\n" + "=" * 60)
            print("Agent推理过程:")
            print("=" * 60)
            reasoning = agent.get_reasoning_trace()
            for key, value in reasoning.items():
                print(f"\n【{key}】")
                print(value)

        print("\n" + "=" * 60)
        print(f"✓ 完成! 提取了 {len(headings)} 个顶级标题")
        print("=" * 60)

        # 工具使用统计
        usage = agent.get_tool_usage()
        print(f"\n工具使用情况:")
        print(f"  - LLM调用: {usage['llm_calls']} 次")
        print(f"  - PDF阅读器: {usage['pdf_reader']} 次")
        print(f"  - 文本提取器: {usage['text_extractor']} 次")
        print(f"  - 结构分析器: {usage['structure_analyzer']} 次")

    except FileNotFoundError as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
