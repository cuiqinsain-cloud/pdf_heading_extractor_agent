#!/usr/bin/env python3
"""
Query extracted headings from JSON output.

Usage:
    python query_headings.py <json_file> [options]

Options:
    --search KEYWORD      Search for headings containing keyword
    --level LEVEL         Filter by heading level (1-5)
    --page PAGE           Find headings on specific page
    --show-range          Show page ranges for all headings
    --show-children       Show child headings
    --format FORMAT       Output format: text (default), json

Examples:
    # Search for headings containing "revenue"
    python query_headings.py output/report_headings.json --search revenue

    # Show all level 1 headings
    python query_headings.py output/report_headings.json --level 1

    # Find headings on page 50
    python query_headings.py output/report_headings.json --page 50

    # Show page ranges
    python query_headings.py output/report_headings.json --show-range
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any


def load_headings(json_file: str) -> Dict[str, Any]:
    """Load headings from JSON file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_headings(headings: List[Dict], args) -> List[Dict]:
    """Apply filters to headings."""
    results = headings

    if args.search:
        keyword = args.search.lower()
        results = [h for h in results if keyword in h['text'].lower()]

    if args.level:
        results = [h for h in results if h['level'] == args.level]

    if args.page:
        results = [h for h in results if h['page'] == args.page]

    return results


def format_heading(h: Dict, show_range: bool = False, show_children: bool = False,
                   heading_map: Dict = None) -> str:
    """Format a single heading for display."""
    indent = "  " * (h['level'] - 1)
    text = h['text']
    page = h['page']

    output = f"{indent}• {text} (页 {page}"

    if show_range and h.get('page_range'):
        pr = h['page_range']
        end = pr['end'] if pr['end'] is not None else '?'
        output += f"-{end}"

    output += ")"

    if show_children and h.get('children') and heading_map:
        child_count = len(h['children'])
        output += f" [{child_count} 个子标题]"

    return output


def display_results(results: List[Dict], args, all_headings: List[Dict]):
    """Display query results."""
    if not results:
        print("\n未找到匹配的标题")
        return

    # Build heading map for children lookup
    heading_map = {h['id']: h for h in all_headings}

    print(f"\n找到 {len(results)} 个匹配的标题:\n")

    if args.format == 'json':
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for h in results:
            print(format_heading(h, args.show_range, args.show_children, heading_map))


def show_statistics(data: Dict):
    """Display document statistics."""
    stats = data.get('statistics', {})

    print(f"\n📊 文档统计:")
    print(f"   文档: {data.get('document', 'N/A')}")
    print(f"   总页数: {data.get('total_pages', 0)}")
    print(f"   总标题数: {stats.get('total_headings', 0)}")
    print(f"   顶级标题: {stats.get('top_level_headings', 0)}")
    print(f"   最大层级: {stats.get('max_depth', 0)}")

    by_source = stats.get('by_source', {})
    if by_source:
        print(f"\n   数据来源:")
        for source, count in by_source.items():
            print(f"     • {source}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Query extracted PDF headings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("json_file", help="Path to headings JSON file")
    parser.add_argument("--search", help="Search for headings containing keyword")
    parser.add_argument("--level", type=int, choices=[1, 2, 3, 4, 5],
                       help="Filter by heading level (1-5)")
    parser.add_argument("--page", type=int, help="Find headings on specific page")
    parser.add_argument("--show-range", action="store_true",
                       help="Show page ranges for headings")
    parser.add_argument("--show-children", action="store_true",
                       help="Show child heading counts")
    parser.add_argument("--format", choices=['text', 'json'], default='text',
                       help="Output format (default: text)")
    parser.add_argument("--stats", action="store_true",
                       help="Show document statistics")

    args = parser.parse_args()

    # Validate JSON file
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"❌ Error: JSON file not found: {args.json_file}")
        return 1

    try:
        # Load data
        data = load_headings(args.json_file)
        headings = data.get('headings', [])

        if not headings:
            print("⚠️  Warning: No headings found in JSON file")
            return 0

        # Show statistics if requested
        if args.stats:
            show_statistics(data)
            if not any([args.search, args.level, args.page]):
                return 0

        # Apply filters
        results = filter_headings(headings, args)

        # Display results
        display_results(results, args, headings)

        return 0

    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON file: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
