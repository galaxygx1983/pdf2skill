---
name: pdf2skill
description: "Convert PDF/EPUB technical documents into executable AI skills with extracted workflows. Use when users need to transform technical manuals, tutorials, and documentation into reusable AI skills."
---

# PDF2Skill

Convert PDF/EPUB technical documents into executable AI skills.

## Overview

pdf2skill is a pipeline tool that:
1. Parses PDF/EPUB documents using markitdown
2. Extracts workflows and procedures using LLM analysis
3. Generates structured AI skills with adaptive complexity

**Two Generation Modes:**
- **Workflow Mode** (default): Extracts step-by-step procedures and commands
- **Q&A Mode**: Extracts question-answer pairs for quick reference

## Quick Start

### Basic Usage

```bash
python scripts/pdf2skill.py input.pdf -o ./output-skill
```

### With LLM Configuration

```bash
# Using Claude
python scripts/pdf2skill.py input.pdf --model claude-sonnet-4-6

# Using OpenAI
python scripts/pdf2skill.py input.pdf --provider openai --model gpt-4o

# Using custom OpenAI-compatible API
export PDF2SKILL_LLM_PROVIDER=openai-compatible
export PDF2SKILL_LLM_BASE_URL=https://api.example.com/v1
export PDF2SKILL_LLM_API_KEY=your-key
python scripts/pdf2skill.py input.pdf
```

### Batch Processing

```bash
python scripts/pdf2skill.py *.pdf -o ./skills-output/
```

### Q&A Mode (New!)

Generate skills with question-answer pairs instead of workflows:

```bash
# Extract Q&A pairs from documentation
python scripts/pdf2skill.py manual.pdf --mode qa -o ./qa-skill

# Q&A mode with verbose output
python scripts/pdf2skill.py faq.pdf --mode qa -v
```

## CLI Options

| Option | Description |
|--------|-------------|
| `input` | Input PDF/EPUB file(s) |
| `-o, --output` | Output directory (default: current) |
| `--model` | LLM model to use |
| `--provider` | LLM provider (anthropic/openai/openai-compatible) |
| `--structure` | Output structure (minimal/standard/complete/auto) |
| `--config` | Path to YAML configuration file |
| `--name` | Skill name (default: derived from filename) |
| `-v, --verbose` | Enable verbose output |
| `--force-ocr` | Force OCR parsing for PDFs |
| `--ocr-language` | OCR language: ch/en/ml (default: ch) |
| `--no-ocr` | Disable automatic OCR fallback |
| `--mode` | Generation mode: workflow/qa (default: workflow) |

## OCR Fallback for Chinese PDFs

pdf2skill automatically detects PDFs with encoding issues (common in Chinese PDFs with embedded fonts) and falls back to OCR parsing using PyMuPDF + PaddleOCR.

### When OCR is triggered:
- Text contains garbled characters (encoding issues)
- PDF uses embedded fonts with custom encoding
- `--force-ocr` flag is used

### OCR Usage Examples

```bash
# Automatic detection (default)
python scripts/pdf2skill.py chinese-book.pdf -o ./skill

# Force OCR for problematic PDFs
python scripts/pdf2skill.py input.pdf --force-ocr

# English PDF with OCR
python scripts/pdf2skill.py manual.pdf --ocr-language en

# Multilingual document
python scripts/pdf2skill.py doc.pdf --ocr-language ml

# Disable OCR fallback
python scripts/pdf2skill.py input.pdf --no-ocr
```

### OCR Dependencies

```bash
# Required for OCR
pip install PyMuPDF paddleocr paddlepaddle
```

## Architecture

```
+-------------------------------------+
|           pdf2skill Pipeline        |
+-------------------------------------+
|  1. Document Parsing Layer          |
|     +-- markitdown --> Markdown     |
|     +-- Structure extraction        |
+-------------------------------------+
|  2. AI Understanding Layer          |
|     +-- Document overview          |
|     +-- Workflow extraction         |
|     +-- Q&A extraction (QA mode)    |
|     +-- Code complexity assessment  |
|     +-- Validation rule generation  |
+-------------------------------------+
|  3. Skill Generation Layer          |
|     +-- Adaptive structure selection|
|     +-- SKILL.md generation         |
|     +-- scripts/ + references/     |
|     +-- Q&A templates (QA mode)     |
+-------------------------------------+
```

## Output Structures

### Minimal (Pages < 20, simple code)
```
skill-name/
+-- SKILL.md
+-- scripts/validate.sh
```

### Standard (Pages 20-100, code examples)
```
skill-name/
+-- SKILL.md
+-- scripts/
|   +-- setup.sh
|   +-- validate.sh
+-- references/
    +-- prompts.md
```

### Complete (Pages > 100, complex logic)
```
skill-name/
+-- SKILL.md
+-- scripts/
+-- references/
+-- templates/
```

## Q&A Mode Output Structure

### Minimal
```
skill-name/
+-- SKILL.md              # Contains all Q&A pairs organized by category
```

### Standard
```
skill-name/
+-- SKILL.md              # Main Q&A content
+-- scripts/
|   +-- search_qa.sh      # Search through Q&A pairs
|   +-- export_qa.sh      # Export Q&A to various formats
+-- references/
    +-- qa_index.md       # Index of all questions
    +-- categories.md     # Category descriptions
```

### Complete
```
skill-name/
+-- SKILL.md
+-- scripts/
+-- references/
+-- templates/
    +-- qa_template.md    # Template for adding new Q&A pairs
    +-- qa_template.json  # JSON template for Q&A
```

## Integration with Other Skills

| Skill | Integration |
|-------|-------------|
| `markitdown` | Core parsing engine for PDF/EPUB --> Markdown |
| `skill-creator` | Output format compliance validation |

## Error Handling

| Scenario | Handling |
|----------|----------|
| PDF unparseable | Suggest OCR fallback via markitdown |
| Password protected | Prompt for password |
| LLM API failure | Retry 3x with exponential backoff |
| Empty document | Warn and exit |
| No workflow found | Fallback to basic extraction |
| No Q&A pairs found | Generate empty Q&A structure with guidance |

## Python API

```python
from scripts.pdf2skill import process_document
from scripts.config import Config
from pathlib import Path

config = Config.from_env()

# Workflow mode (default)
result = process_document(
    input_path=Path("input.pdf"),
    output_dir=Path("./output"),
    config=config,
    mode="workflow",  # or "qa"
    verbose=True,
)

# Q&A mode
result = process_document(
    input_path=Path("faq.pdf"),
    output_dir=Path("./qa-output"),
    config=config,
    mode="qa",
    verbose=True,
)
```

## References

- [prompts.md](references/prompts.md) - LLM prompt templates
- [structures.md](references/structures.md) - Output structure details