---
name: pdf-heading-extractor
description: "Extract multi-level heading structures from PDF documents with page range information. Use when users need to: (1) Extract headings or table of contents from PDFs, (2) Analyze PDF document structure, (3) Get page ranges for specific sections, (4) Filter financial statement headings from annual reports, (5) Query heading hierarchies, (6) Find specific sections in documents, or (7) Understand document organization. Supports PDFs with bookmarks (100% accuracy, fast) and bookmark-less PDFs (LLM-based extraction). Automatically calculates page ranges showing where each section starts and ends."
---

# PDF Heading Extractor

Extract multi-level heading structures from PDF documents, including page range information for each section.

## Quick Start

Extract all headings from a PDF:

```bash
python scripts/extract_headings.py <pdf_path>
```

Output: JSON file in `output/` directory with complete heading tree and page ranges.

## Core Features

1. **Smart extraction**: Prioritizes PDF bookmarks (100% accuracy), falls back to LLM analysis when needed
2. **Page ranges**: Automatically calculates start/end pages for each section
3. **Financial filtering**: Option to extract only financial statement headings
4. **Tree structure**: Maintains complete parent-child relationships
5. **Fast processing**: 1-2 minutes for 200-page documents

## When to Use This Skill

Use this skill when users ask to:
- "Extract the table of contents from this PDF"
- "What sections are in this annual report?"
- "Show me the page range for the financial statements"
- "List all headings in this document"
- "Find the cash flow statement section"
- "What's the structure of this document?"
- "Which pages contain the revenue section?"

## Available Scripts

### 1. Extract Headings (`extract_headings.py`)

Main extraction script.

**Basic usage:**
```bash
python scripts/extract_headings.py document.pdf
```

**Options:**
- `--filter-financial`: Extract only financial statement headings (recommended for annual reports)
- `--no-reflection`: Disable validation phase for faster processing (~30% speed improvement)
- `--output-dir DIR`: Specify output directory (default: output/)
- `--config FILE`: Use custom config file (default: config.yaml)
- `--verbose`: Show detailed logs

**Examples:**
```bash
# Financial report (recommended)
python scripts/extract_headings.py annual_report.pdf --filter-financial

# Fast mode
python scripts/extract_headings.py large_doc.pdf --no-reflection

# Verbose output
python scripts/extract_headings.py document.pdf --verbose
```

### 2. Query Headings (`query_headings.py`)

Search and filter extracted headings.

**Usage:**
```bash
python scripts/query_headings.py output/document_headings.json [options]
```

**Options:**
- `--search KEYWORD`: Search for headings containing keyword
- `--level LEVEL`: Filter by heading level (1-5)
- `--page PAGE`: Find headings on specific page
- `--show-range`: Display page ranges
- `--show-children`: Show child heading counts
- `--format json`: Output as JSON
- `--stats`: Show document statistics

**Examples:**
```bash
# Search for "revenue"
python scripts/query_headings.py output/report_headings.json --search revenue

# Show all top-level headings
python scripts/query_headings.py output/report_headings.json --level 1

# Find headings on page 50 with ranges
python scripts/query_headings.py output/report_headings.json --page 50 --show-range

# Get statistics
python scripts/query_headings.py output/report_headings.json --stats
```

### 3. Analyze Structure (`analyze_structure.py`)

Analyze PDF document structure before extraction.

**Usage:**
```bash
python scripts/analyze_structure.py document.pdf [options]
```

**Options:**
- `--show-bookmarks`: Display bookmark details
- `--show-fonts`: Show font statistics
- `--output json`: Output as JSON

**Use case**: Check if PDF has bookmarks to determine extraction speed and accuracy.

## Output Format

See [references/output-format.md](references/output-format.md) for complete schema.

**Key fields in output JSON:**
- `text`: Heading text
- `page`: Starting page number
- `level`: Hierarchy level (1-5)
- `next_sibling_page`: Next same-level heading's page (NEW)
- `page_range`: {start, end} pages for this section (NEW)
- `children`: Child heading IDs

**Example:**
```json
{
  "text": "5、 应收账款",
  "page": 122,
  "level": 3,
  "next_sibling_page": 125,
  "page_range": {
    "start": 122,
    "end": 124
  },
  "children": [332, 333, 334]
}
```

This heading covers pages 122-124 (next sibling starts on page 125).

## Common Workflows

### Workflow 1: Quick Extraction

```bash
# Extract headings
python scripts/extract_headings.py document.pdf --no-reflection

# View results
cat output/document_headings.json
```

### Workflow 2: Financial Report Analysis

```bash
# Extract financial statements only
python scripts/extract_headings.py annual_report.pdf --filter-financial

# Find specific items
python scripts/query_headings.py output/annual_report_headings.json \
  --search "应收账款" --show-range
```

### Workflow 3: Document Structure Analysis

```bash
# Check document structure first
python scripts/analyze_structure.py document.pdf --show-bookmarks

# Then extract based on findings
python scripts/extract_headings.py document.pdf
```

## Performance

- **Speed**: 1-2 minutes for 200-page documents
- **Accuracy**: 100% for bookmarked PDFs, ~95% for LLM extraction
- **Cost**: 1 LLM call for bookmarked PDFs (extremely low cost)
- **LLM calls**: Typically 1-3 calls per document

## Requirements

**Environment:**
- Python 3.8+
- Virtual environment recommended

**Dependencies:**
- anthropic (Anthropic SDK)
- PyMuPDF (PDF processing)
- pydantic (data validation)
- rich (terminal output)
- pyyaml (config parsing)

**Configuration:**
- Environment variable: `LLM_API_KEY` (required)
- Config file: `config.yaml` in project root

**Setup:**
```bash
# Activate virtual environment
source venv/bin/activate

# Verify dependencies
pip list | grep -E "anthropic|PyMuPDF|pydantic"

# Set API key
export LLM_API_KEY=your_api_key_here
```

## Examples

See [references/examples.md](references/examples.md) for detailed usage examples including:
- Basic extraction
- Financial report analysis
- Fast mode processing
- Searching and filtering
- Page range queries
- Document structure analysis

## Troubleshooting

**Issue**: "No bookmarks found"
- **Solution**: The tool will automatically use LLM extraction (slower but accurate)

**Issue**: "API key not found"
- **Solution**: Set `LLM_API_KEY` environment variable

**Issue**: "Config file not found"
- **Solution**: Ensure `config.yaml` exists in project root, or specify with `--config`

**Issue**: "Memory error on large PDFs"
- **Solution**: Use `--no-reflection` flag or split the PDF

**Issue**: "Slow processing"
- **Solution**: Use `--no-reflection` for ~30% speed improvement

## Technical Details

**Data Sources:**
1. **PDF Bookmarks** (preferred): 100% accurate, instant extraction
2. **LLM Analysis** (fallback): ~95% accurate, requires API calls

**Processing Phases:**
1. Document analysis (1 LLM call)
2. Heading identification (uses bookmarks if available)
3. Level determination (from bookmarks or LLM)
4. Relationship building (constructs tree + calculates page ranges)
5. Reflection/validation (optional, can be disabled)

**Page Range Calculation:**
- Finds next same-level heading
- Calculates section span
- Handles edge cases (same-page headings, document end)

## Notes

- Always use `--filter-financial` for annual reports to reduce noise
- Check bookmarks first with `analyze_structure.py` to estimate processing time
- Use `--no-reflection` for production workflows (faster, still accurate)
- Page ranges are automatically calculated for all headings
- Output is always saved to `output/` directory with `_headings.json` suffix
