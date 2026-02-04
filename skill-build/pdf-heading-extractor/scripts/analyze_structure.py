#!/usr/bin/env python3
"""
Analyze PDF document structure and heading distribution.

Usage:
    python analyze_structure.py <pdf_path> [options]

Options:
    --show-bookmarks      Show bookmark information
    --show-fonts          Show font statistics
    --output FORMAT       Output format: text (default), json

Examples:
    # Basic analysis
    python analyze_structure.py document.pdf

    # Show bookmark details
    python analyze_structure.py document.pdf --show-bookmarks

    # JSON output
    python analyze_structure.py document.pdf --output json
"""

import sys
import json
import argparse
from pathlib import Path
from collections import Counter

# Add parent directories to path
skill_dir = Path(__file__).parent.parent
project_root = skill_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.tools.pdf_reader import PDFReaderTool
    from src.tools.text_extractor import TextExtractorTool
except ImportError as e:
    print(f"Error: Cannot import required modules. Make sure you're running from the correct directory.")
    print(f"Details: {e}")
    sys.exit(1)


def analyze_pdf(pdf_path: str, args) -> dict:
    """Analyze PDF structure."""
    config = {}
    pdf_reader = PDFReaderTool(config)
    text_extractor = TextExtractorTool(config)

    # Read PDF info
    pdf_info = pdf_reader.read_pdf_info(pdf_path)

    # Extract text blocks for analysis
    text_blocks = text_extractor.extract_text_blocks(pdf_path)

    # Analyze bookmarks
    bookmarks = pdf_info.get('bookmarks', [])
    bookmark_levels = Counter(b['level'] for b in bookmarks) if bookmarks else {}

    # Analyze fonts
    font_sizes = [block.font_size for block in text_blocks if hasattr(block, 'font_size')]
    font_size_dist = Counter(font_sizes) if font_sizes else {}

    # Build analysis result
    analysis = {
        'document': Path(pdf_path).name,
        'total_pages': pdf_info.get('total_pages', 0),
        'has_bookmarks': len(bookmarks) > 0,
        'bookmark_count': len(bookmarks),
        'bookmark_levels': dict(bookmark_levels),
        'text_blocks': len(text_blocks),
        'font_sizes': dict(sorted(font_size_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
        'metadata': pdf_info.get('metadata', {})
    }

    if args.show_bookmarks and bookmarks:
        analysis['bookmarks'] = [
            {
                'text': b['text'],
                'page': b['page'],
                'level': b['level']
            }
            for b in bookmarks[:20]  # Show first 20
        ]

    return analysis


def display_analysis(analysis: dict, args):
    """Display analysis results."""
    if args.output == 'json':
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        return

    # Text format
    print(f"\n📄 PDF 文档分析")
    print(f"{'=' * 60}")
    print(f"文档: {analysis['document']}")
    print(f"总页数: {analysis['total_pages']}")
    print(f"文本块: {analysis['text_blocks']}")

    print(f"\n📑 书签信息")
    print(f"{'─' * 60}")
    if analysis['has_bookmarks']:
        print(f"✓ 包含书签: {analysis['bookmark_count']} 个")
        print(f"\n层级分布:")
        for level, count in sorted(analysis['bookmark_levels'].items()):
            print(f"  Level {level}: {count} 个")

        if args.show_bookmarks and 'bookmarks' in analysis:
            print(f"\n前 20 个书签:")
            for b in analysis['bookmarks']:
                indent = "  " * b['level']
                print(f"  {indent}• {b['text']} (页 {b['page']})")
    else:
        print("✗ 无书签（需要使用 LLM 提取）")

    if analysis['font_sizes']:
        print(f"\n🔤 字体大小分布 (Top 10)")
        print(f"{'─' * 60}")
        for size, count in list(analysis['font_sizes'].items())[:10]:
            print(f"  {size:.1f}pt: {count} 次")

    metadata = analysis.get('metadata', {})
    if metadata:
        print(f"\n📋 文档元数据")
        print(f"{'─' * 60}")
        for key, value in metadata.items():
            if value:
                print(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze PDF document structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--show-bookmarks", action="store_true",
                       help="Show bookmark details (first 20)")
    parser.add_argument("--show-fonts", action="store_true",
                       help="Show font statistics")
    parser.add_argument("--output", choices=['text', 'json'], default='text',
                       help="Output format (default: text)")

    args = parser.parse_args()

    # Validate PDF path
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        return 1

    try:
        print(f"🔍 Analyzing: {pdf_path.name}...")
        analysis = analyze_pdf(str(pdf_path), args)
        display_analysis(analysis, args)
        return 0

    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
