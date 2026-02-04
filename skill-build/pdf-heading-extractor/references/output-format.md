# Output Format Reference

This document describes the JSON output format for extracted PDF headings.

## JSON Structure

```json
{
  "document": "filename.pdf",
  "total_pages": 208,
  "statistics": {
    "total_headings": 254,
    "top_level_headings": 4,
    "max_depth": 5,
    "by_source": {
      "bookmark": 254
    }
  },
  "headings": [...]
}
```

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `document` | string | Original PDF filename |
| `total_pages` | integer | Total number of pages in PDF |
| `statistics` | object | Summary statistics |
| `headings` | array | Array of heading objects |

## Statistics Object

| Field | Type | Description |
|-------|------|-------------|
| `total_headings` | integer | Total number of extracted headings |
| `top_level_headings` | integer | Number of level-1 headings |
| `max_depth` | integer | Maximum heading level (1-5) |
| `by_source` | object | Count by data source (bookmark/llm) |

## Heading Object

Each heading in the `headings` array contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique heading identifier |
| `text` | string | Heading text content |
| `page` | integer | Page number where heading appears |
| `level` | integer | Heading level (1=top, 5=deepest) |
| `confidence` | float | Confidence score (0.0-1.0) |
| `source` | string | Data source: "bookmark" or "llm" |
| `children` | array | Array of child heading IDs |
| `next_sibling_page` | integer\|null | Page number of next same-level heading |
| `page_range` | object | Page range for this section |

### Page Range Object

The `page_range` object indicates the span of pages covered by this heading:

```json
{
  "start": 122,
  "end": 124
}
```

- `start`: First page of this section (same as `page`)
- `end`: Last page before next sibling heading (or `null` if no next sibling)

**Note**: When multiple headings appear on the same page, `end` may equal `start`.

## Example Heading

```json
{
  "id": 331,
  "text": "5、 应收账款",
  "page": 122,
  "level": 3,
  "confidence": 1.0,
  "source": "bookmark",
  "children": [332, 333, 334, 335, 336],
  "next_sibling_page": 125,
  "page_range": {
    "start": 122,
    "end": 124
  }
}
```

This heading:
- Appears on page 122
- Is a level-3 heading
- Has 5 child headings (IDs 332-336)
- Covers pages 122-124 (next sibling starts on page 125)
- Was extracted from PDF bookmarks (100% confidence)

## Data Sources

### Bookmark Source

- `source`: "bookmark"
- `confidence`: 1.0
- Most accurate, extracted directly from PDF metadata
- Preserves original hierarchy

### LLM Source

- `source`: "llm"
- `confidence`: 0.5-0.95 (varies)
- Used when bookmarks are insufficient
- Based on semantic analysis

## Hierarchy Representation

Headings form a tree structure using `children` arrays:

```
Level 1: Chapter (id: 1)
  Level 2: Section (id: 2)
    Level 3: Subsection (id: 3)
    Level 3: Subsection (id: 4)
  Level 2: Section (id: 5)
```

Represented as:
```json
[
  {"id": 1, "level": 1, "children": [2, 5]},
  {"id": 2, "level": 2, "children": [3, 4]},
  {"id": 3, "level": 3, "children": []},
  {"id": 4, "level": 3, "children": []},
  {"id": 5, "level": 2, "children": []}
]
```

## Filtering

When using `--filter-financial`, only headings matching financial statement keywords are included, along with all their descendants. The tree structure is preserved.

Common filtered headings:
- 合并资产负债表 (Consolidated Balance Sheet)
- 合并利润表 (Consolidated Income Statement)
- 合并现金流量表 (Consolidated Cash Flow Statement)
- 合并财务报表项目注释 (Notes to Financial Statements)
