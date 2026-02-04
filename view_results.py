import json
import sys

def print_tree(headings, heading_map, indent=0):
    """递归打印标题树"""
    for h in headings:
        prefix = "  " * indent
        level_marker = "■" * h.get("level", 1)
        print(f"{prefix}{level_marker} {h['text'][:80]} (页{h['page']})")

        # 打印子标题
        children_ids = h.get("children", [])
        if children_ids:
            children = [heading_map[cid] for cid in children_ids if cid in heading_map]
            print_tree(children, heading_map, indent + 1)

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "output/海天味业：海天味业2024年年度报告_headings.json"

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n{'='*80}")
    print(f"文档: {data['document']}")
    print(f"总页数: {data['total_pages']}")
    print(f"标题总数: {len(data['headings'])}")
    print(f"{'='*80}\n")

    # 构建ID到标题的映射
    heading_map = {h["id"]: h for h in data["headings"]}

    # 找出顶级标题（没有父节点的）
    all_children = set()
    for h in data["headings"]:
        all_children.update(h.get("children", []))

    top_level = [h for h in data["headings"] if h["id"] not in all_children]

    print(f"顶级标题数: {len(top_level)}\n")
    print_tree(top_level, heading_map)
