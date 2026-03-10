# Output Structure Templates

This file documents the three output structure levels.

## Minimal Structure

For documents < 20 pages with simple code:

```
skill-name/
├── SKILL.md
└── scripts/
    └── validate.sh
```

## Standard Structure

For documents 20-100 pages with code examples:

```
skill-name/
├── SKILL.md
├── scripts/
│   ├── setup.sh
│   └── validate.sh
└── references/
    └── prompts.md
```

## Complete Structure

For documents > 100 pages with complex logic:

```
skill-name/
├── SKILL.md
├── scripts/
│   ├── setup.sh
│   └── validate.sh
├── references/
│   ├── prompts.md
│   └── structures.md
└── templates/
    └── minimal/
        └── SKILL.md.template
```

## Structure Selection Logic

| Condition | Structure |
|-----------|-----------|
| Pages < 20, code blocks < 5 | Minimal |
| Pages < 100, code blocks < 20 | Standard |
| Pages >= 100 or code blocks >= 20 | Complete |