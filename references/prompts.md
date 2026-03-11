# Prompt Templates

This file contains the prompt templates used for LLM processing in pdf2skill.

## Stage 1: Document Overview

Analyze the document and extract:
- Document type (technical_manual, tutorial, api_reference, etc.)
- Target audience
- Main topics covered
- Overall complexity level
- Brief summary

```json
{
  "document_type": "technical_manual",
  "audience": "developers",
  "topics": ["setup", "configuration", "usage"],
  "complexity": "medium",
  "summary": "A comprehensive guide for..."
}
```

## Stage 2: Workflow Extraction

Extract all workflows/procedures with:
- Workflow name and trigger condition
- Steps with names and descriptions
- Commands to execute (if any)
- Prerequisites (if any)

```json
{
  "workflows": [
    {
      "name": "Installation",
      "trigger": "When setting up the tool",
      "steps": [
        {"name": "Download", "description": "Download the package", "commands": []},
        {"name": "Install", "description": "Run installer", "commands": ["npm install"]}
      ],
      "complexity": "simple",
      "prerequisites": ["Node.js 18+"]
    }
  ]
}
```

## Stage 3: Code Assessment

Evaluate code complexity:
- Number of code blocks
- Programming languages used
- Complexity level (simple/medium/complex)

```json
{
  "code_assessment": {
    "total_blocks": 12,
    "languages": ["bash", "python", "javascript"],
    "complexity": "medium"
  }
}
```

## Stage 4: Validation Rules

Generate validation rules for each workflow step:
- Type: command, output_check, file_check, manual_check
- Specific validation details

```json
{
  "validation_rules": [
    {
      "step": "Setup",
      "type": "command",
      "command": "test -f package.json"
    }
  ]
}
```

## Stage 5: Q&A Extraction (QA Mode)

Extract question-answer pairs from the document:
- Question: Clear, natural language question
- Answer: Comprehensive but concise answer
- Category: setup, usage, troubleshooting, concept, configuration, general
- Source section: Which section of the document this came from

```json
{
  "qa_pairs": [
    {
      "question": "How do I install the tool?",
      "answer": "Run `npm install -g tool-name` to install globally, or `npm install tool-name` for local installation.",
      "category": "setup",
      "source_section": "Installation"
    },
    {
      "question": "What should I do if I get error XYZ?",
      "answer": "This error typically occurs when... To fix it, try the following steps...",
      "category": "troubleshooting",
      "source_section": "Troubleshooting"
    }
  ]
}
```

### Categories

- **setup**: Installation and initial configuration questions
- **usage**: How-to and feature usage questions  
- **troubleshooting**: Problem-solving and error resolution
- **concept**: Architecture, theory, and concept explanations
- **configuration**: Settings and configuration options
- **general**: General questions that don't fit other categories

### Extraction Guidelines

1. Look for explicit Q&A patterns:
   - "Q: ... A: ..." format
   - "Question: ... Answer: ..." format
   - Numbered questions (1., 2., etc.)
   - FAQ sections

2. Identify implicit Q&A pairs:
   - Problem/solution pairs in troubleshooting sections
   - "How to" statements that can be converted to questions
   - Common user questions based on content

3. Ensure quality:
   - Questions should be clear and specific
   - Answers should be complete but concise
   - Include relevant code examples if present
   - Categorize appropriately for easy navigation