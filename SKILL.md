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
|     +-- Code complexity assessment  |
|     +-- Validation rule generation  |
+-------------------------------------+
|  3. Skill Generation Layer          |
|     +-- Adaptive structure selection|
|     +-- SKILL.md generation         |
|     +-- scripts/ + references/     |
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

## Python API

```python
from scripts.pdf2skill import process_document
from scripts.config import Config
from pathlib import Path

config = Config.from_env()
result = process_document(
    input_path=Path("input.pdf"),
    output_dir=Path("./output"),
    config=config,
    verbose=True,
)
```

## References

- [prompts.md](references/prompts.md) - LLM prompt templates
- [structures.md](references/structures.md) - Output structure details