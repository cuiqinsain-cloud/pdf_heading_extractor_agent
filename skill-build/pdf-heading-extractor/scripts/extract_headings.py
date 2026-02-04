#!/usr/bin/env python3
"""
Extract multi-level headings from PDF documents.

Usage:
    python extract_headings.py <pdf_path> [options]

Options:
    --filter-financial    Extract only financial statement headings
    --no-reflection       Disable reflection phase (faster)
    --output-dir DIR      Output directory (default: output/)
    --config FILE         Config file (default: config.yaml)
    --verbose             Show detailed logs

Examples:
    # Basic extraction
    python extract_headings.py document.pdf

    # Extract financial statements only
    python extract_headings.py annual_report.pdf --filter-financial

    # Fast mode (no reflection)
    python extract_headings.py document.pdf --no-reflection
"""

import sys
import argparse
import json
from pathlib import Path

# Add parent directories to path for imports
skill_dir = Path(__file__).parent.parent
project_root = skill_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.agent import PDFHeadingExtractorAgent
except ImportError as e:
    print(f"Error: Cannot import PDFHeadingExtractorAgent. Make sure you're running from the correct directory.")
    print(f"Details: {e}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Extract multi-level headings from PDF documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--filter-financial", action="store_true",
                       help="Extract only financial statement headings (recommended for annual reports)")
    parser.add_argument("--no-reflection", action="store_true",
                       help="Disable reflection phase for faster processing")
    parser.add_argument("--output-dir", default="output",
                       help="Output directory (default: output/)")
    parser.add_argument("--config", default="config.yaml",
                       help="Config file path (default: config.yaml)")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed logs")

    args = parser.parse_args()

    # Validate PDF path
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        return 1

    # Validate config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Error: Config file not found: {args.config}")
        print(f"   Please ensure config.yaml exists in the project root")
        return 1

    try:
        # Initialize Agent
        print(f"🔧 Initializing PDF Heading Extractor Agent...")
        agent = PDFHeadingExtractorAgent(config_path=str(config_path))

        # Configure options
        if args.no_reflection:
            agent.enable_reflection = False
            if args.verbose:
                print("   → Reflection disabled (faster mode)")

        # Extract headings
        print(f"📄 Processing: {pdf_path.name}")
        headings = agent.extract_headings(str(pdf_path))

        # Get output file path
        output_file = agent.formatter.output_dir / f"{pdf_path.stem}_headings.json"

        # Load and display summary
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stats = data.get('statistics', {})

        print(f"\n✅ 提取完成！")
        print(f"   📊 总标题数: {stats.get('total_headings', 0)}")
        print(f"   📑 顶级标题: {stats.get('top_level_headings', 0)}")
        print(f"   📏 最大层级: {stats.get('max_depth', 0)}")
        print(f"   📁 输出文件: {output_file}")

        if args.verbose:
            by_source = stats.get('by_source', {})
            print(f"\n   数据来源:")
            for source, count in by_source.items():
                print(f"     • {source}: {count}")

        return 0

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
