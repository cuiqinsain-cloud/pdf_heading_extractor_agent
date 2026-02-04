# Usage Examples

This document provides practical examples of using the PDF Heading Extractor skill.

## Example 1: Basic Extraction

**Scenario**: Extract all headings from a technical document.

```bash
python scripts/extract_headings.py technical_manual.pdf
```

**Output**:
```
🔧 Initializing PDF Heading Extractor Agent...
📄 Processing: technical_manual.pdf

Phase 1: 文档分析...
  ✓ PDF信息: 150页
  ✓ 提取文本块: 8234个
  ✓ LLM文档分析完成

Phase 2: 标题识别...
  ✓ 使用PDF书签: 89个
  ✓ 书签数量充足，跳过LLM分析

Phase 3: 层级判定...
  ✓ 书签已包含层级信息，直接使用

Phase 4: 关系构建...
  ✓ 页码范围信息已添加
  ✓ 关系构建完成: 12个顶级标题, 共89个标题

✅ 提取完成！
   📊 总标题数: 89
   📑 顶级标题: 12
   📏 最大层级: 4
   📁 输出文件: output/technical_manual_headings.json
```

## Example 2: Financial Report Analysis

**Scenario**: Extract only financial statements from an annual report.

```bash
python scripts/extract_headings.py annual_report_2024.pdf --filter-financial
```

**Result**: Extracts only:
- Balance Sheet sections
- Income Statement sections
- Cash Flow Statement sections
- Notes to Financial Statements (with all sub-items)

**Use case**: When you only need financial data, not the entire report structure.

## Example 3: Fast Mode

**Scenario**: Quick extraction without validation (faster processing).

```bash
python scripts/extract_headings.py large_document.pdf --no-reflection
```

**Speed improvement**: ~30% faster by skipping the reflection phase.

**When to use**: For large documents or when speed is critical.

## Example 4: Search for Specific Headings

**Scenario**: Find all headings related to "revenue" in a financial report.

```bash
# First, extract headings
python scripts/extract_headings.py annual_report.pdf --filter-financial

# Then search
python scripts/query_headings.py output/annual_report_headings.json --search revenue
```

**Output**:
```
找到 3 个匹配的标题:

  • 营业收入 (页 45)
    • 主营业务收入 (页 45)
    • 其他业务收入 (页 46)
```

## Example 5: Get Page Range for a Section

**Scenario**: Find which pages contain the "Cash Flow Statement" section.

```bash
python scripts/query_headings.py output/annual_report_headings.json \
  --search "现金流量表" --show-range
```

**Output**:
```
找到 1 个匹配的标题:

• 合并现金流量表 (页 85-86)
```

**Interpretation**: The Cash Flow Statement spans pages 85-86.

## Example 6: Analyze Document Structure

**Scenario**: Check if a PDF has bookmarks before extraction.

```bash
python scripts/analyze_structure.py document.pdf --show-bookmarks
```

**Output**:
```
📄 PDF 文档分析
============================================================
文档: document.pdf
总页数: 208
文本块: 17315

📑 书签信息
────────────────────────────────────────────────────────────
✓ 包含书签: 721 个

层级分布:
  Level 1: 21 个
  Level 2: 156 个
  Level 3: 423 个
  Level 4: 98 个
  Level 5: 23 个
```

**Insight**: This PDF has excellent bookmark structure (721 bookmarks), so extraction will be fast and accurate.

## Example 7: Filter by Heading Level

**Scenario**: Show only top-level (chapter) headings.

```bash
python scripts/query_headings.py output/document_headings.json --level 1
```

**Output**:
```
找到 21 个匹配的标题:

• 第一节 释义 (页 4)
• 第二节 公司简介和主要财务指标 (页 8)
• 第三节 管理层讨论与分析 (页 15)
...
```

## Example 8: Find Headings on Specific Page

**Scenario**: What sections are on page 120?

```bash
python scripts/query_headings.py output/report_headings.json --page 120
```

**Output**:
```
找到 3 个匹配的标题:

• 七、 合并财务报表项目注释 (页 120)
  • 1、 货币资金 (页 120)
  • 2、 交易性金融资产 (页 120)
```

## Example 9: JSON Output for Programmatic Use

**Scenario**: Get results in JSON format for further processing.

```bash
python scripts/query_headings.py output/report_headings.json \
  --search "资产" --format json
```

**Output**: JSON array of matching headings, suitable for piping to other tools.

## Example 10: Document Statistics

**Scenario**: Get overview statistics without filtering.

```bash
python scripts/query_headings.py output/report_headings.json --stats
```

**Output**:
```
📊 文档统计:
   文档: annual_report.pdf
   总页数: 208
   总标题数: 254
   顶级标题: 4
   最大层级: 5

   数据来源:
     • bookmark: 254
```

## Common Workflows

### Workflow 1: Analyze → Extract → Query

```bash
# Step 1: Check document structure
python scripts/analyze_structure.py document.pdf

# Step 2: Extract headings
python scripts/extract_headings.py document.pdf --no-reflection

# Step 3: Query specific sections
python scripts/query_headings.py output/document_headings.json \
  --search "your_topic"
```

### Workflow 2: Financial Report Deep Dive

```bash
# Extract financial statements only
python scripts/extract_headings.py annual_report.pdf --filter-financial

# Find specific financial items
python scripts/query_headings.py output/annual_report_headings.json \
  --search "应收账款" --show-range

# Get all level-3 items (detailed line items)
python scripts/query_headings.py output/annual_report_headings.json \
  --level 3 --show-range
```

## Tips

1. **Use `--filter-financial` for annual reports** - Reduces noise and focuses on financial data
2. **Use `--no-reflection` for speed** - Saves ~30% processing time
3. **Check bookmarks first** - Use `analyze_structure.py` to verify bookmark availability
4. **Combine filters** - You can use `--search`, `--level`, and `--page` together
5. **Use `--show-range`** - Essential for understanding section boundaries
