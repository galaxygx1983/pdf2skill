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