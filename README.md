# PDF2Skill

Convert PDF/EPUB technical documents into executable AI skills.

## Overview

pdf2skill is a pipeline tool that:
1. Parses PDF/EPUB documents using markitdown
2. Extracts workflows and procedures using LLM analysis
3. Generates structured AI skills with adaptive complexity

**Key Features**:
- **Two Generation Modes**: Workflow mode (step-by-step procedures) and Q&A mode (question-answer pairs)
- **Automatic OCR fallback** for PDFs with encoding issues (common in Chinese PDFs with embedded fonts)

## Installation

```bash
# Core dependencies
pip install markitdown

# For OCR support (optional, for PDFs with encoding issues)
pip install PyMuPDF paddleocr paddlepaddle
```

## Quick Start

### Basic Usage

```bash
python scripts/pdf2skill.py input.pdf -o ./output-skill
```

### With OCR Fallback

```bash
# Force OCR for problematic PDFs
python scripts/pdf2skill.py chinese-book.pdf --force-ocr

# English PDF
python scripts/pdf2skill.py manual.pdf --ocr-language en

# Multilingual document
python scripts/pdf2skill.py doc.pdf --ocr-language ml
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

### Q&A Mode

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

## Architecture

```
+-------------------------------------+
|           pdf2skill Pipeline        |
+-------------------------------------+
|  1. Document Parsing Layer          |
|     +-- markitdown --> Markdown     |
|     +-- OCR fallback (PyMuPDF)      |
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

## OCR Fallback

pdf2skill automatically detects PDFs with encoding issues (common with Chinese PDFs using embedded fonts) and falls back to OCR parsing using PyMuPDF + PaddleOCR.

### When OCR is triggered:
- Text contains garbled characters (encoding issues)
- PDF uses embedded fonts with custom encoding
- `--force-ocr` flag is used

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

## Q&A Mode Output

When using `--mode qa`, the skill structure includes Q&A-specific files:

```
skill-name/
+-- SKILL.md              # All Q&A pairs organized by category
+-- scripts/
|   +-- search_qa.sh      # Search through Q&A pairs
|   +-- export_qa.sh      # Export Q&A to various formats
+-- references/
|   +-- qa_index.md       # Index of all questions
|   +-- categories.md     # Category descriptions
+-- templates/
    +-- qa_template.md    # Template for adding new Q&A pairs
    +-- qa_template.json  # JSON template for Q&A
```

## License

MIT License