---
name: pdf2skill
description: PDF/EPUB技术文档转AI Skill转换工具(pdf2skill)。当用户需要将PDF技术手册/教程/文档转换为可执行AI技能、从PDF提取工作流(workflow extraction)和操作步骤、将EPUB电子书转换为Claude Skill、处理中文PDF文档(自动OCR识别)、批量转换多个PDF文档、生成SKILL.md文件和脚本目录结构、使用LLM分析文档内容并提取流程、将技术文档转换为可复用的AI助手、处理扫描版PDF(OCR fallback)、提取Q&A问答对生成知识库技能、转换API文档/开发指南/操作手册为Skill、从文档提取验证规则(validation rules)、自适应复杂度评估生成不同层级技能结构等相关任务时立即使用。支持Workflow模式(工作流提取)和Q&A模式(问答对提取)，自动处理乱码和编码问题。
trigger:
  - PDF转Skill
  - EPUB转Skill
  - 文档转Skill
  - PDF转换
  - 提取工作流
  - 技术文档转换
  - 教程转AI技能
  - 手册转Skill
  - PDF OCR
  - 批量转换
  - 生成SKILL.md
  - 文档解析
  - 工作流提取
  - Q&A提取
  - 知识库转换
  - 扫描PDF处理
  - 中文PDF转换
  - API文档转换
  - 操作手册转换
  - pdf2skill
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