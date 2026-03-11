"""
Skill Generator Module for pdf2skill.

Generates executable AI skills from analyzed document content.
Supports three structure types: minimal, standard, and complete.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.ai_analyzer import Workflow, WorkflowStep, QAPair


@dataclass
class GeneratedSkill:
    """Represents a generated skill with its files and metadata."""

    name: str
    files: Dict[str, str]  # relative_path -> content
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "files": self.files,
            "metadata": self.metadata,
        }


class SkillGenerator:
    """
    Generates executable AI skills from document analysis results.

    Supports three output structures based on complexity:
    - minimal: SKILL.md only (for simple documents, <20 pages, <5 code blocks)
    - standard: SKILL.md + scripts + references (for medium complexity)
    - complete: Full structure with templates (for complex documents)
    """

    # Thresholds for structure determination
    MINIMAL_MAX_PAGES = 20
    MINIMAL_MAX_CODE_BLOCKS = 5
    STANDARD_MAX_PAGES = 100
    STANDARD_MAX_CODE_BLOCKS = 20

    def __init__(self):
        """Initialize the skill generator."""
        pass

    def determine_structure(
        self, page_count: int, code_blocks: int, force: Optional[str] = None
    ) -> str:
        """
        Determine the appropriate output structure based on document complexity.

        Args:
            page_count: Number of pages in the document
            code_blocks: Number of code blocks in the document
            force: Force a specific structure ("minimal", "standard", "complete")

        Returns:
            Structure type: "minimal", "standard", or "complete"
        """
        if force:
            valid_structures = ("minimal", "standard", "complete")
            if force not in valid_structures:
                raise ValueError(
                    f"Invalid structure '{force}'. Must be one of {valid_structures}"
                )
            return force

        # Minimal: small documents with few code blocks
        if (
            page_count <= self.MINIMAL_MAX_PAGES
            and code_blocks <= self.MINIMAL_MAX_CODE_BLOCKS
        ):
            return "minimal"

        # Complete: large documents with many code blocks
        if (
            page_count > self.STANDARD_MAX_PAGES
            or code_blocks > self.STANDARD_MAX_CODE_BLOCKS
        ):
            return "complete"

        # Standard: medium complexity documents
        return "standard"

    def generate(
        self,
        skill_name: str,
        workflows: List[Workflow],
        code_assessment: Dict[str, Any],
        structure: str,
        source_file: str,
        overview: Optional[Dict[str, Any]] = None,
        validation_rules: Optional[List[Dict[str, Any]]] = None,
        qa_pairs: Optional[List[QAPair]] = None,
        mode: str = "workflow",
    ) -> GeneratedSkill:
        """
        Generate a skill from analyzed document content.

        Args:
            skill_name: Name for the generated skill
            workflows: List of extracted workflows
            code_assessment: Code complexity assessment
            structure: Output structure type ("minimal", "standard", "complete")
            source_file: Original source file name
            overview: Document overview analysis
            validation_rules: Validation rules for workflows
            qa_pairs: List of Q&A pairs for QA mode
            mode: Generation mode - "workflow" or "qa"

        Returns:
            GeneratedSkill with files and metadata
        """
        # Normalize structure name
        structure = structure.lower()
        qa_pairs = qa_pairs or []

        # Generate SKILL.md based on mode
        if mode == "qa":
            skill_md = self._generate_qa_skill_md(
                skill_name=skill_name,
                qa_pairs=qa_pairs,
                code_assessment=code_assessment,
                structure=structure,
                source_file=source_file,
                overview=overview,
            )
        else:
            skill_md = self._generate_skill_md(
                skill_name=skill_name,
                workflows=workflows,
                code_assessment=code_assessment,
                structure=structure,
                source_file=source_file,
                overview=overview,
            )

        files = {"SKILL.md": skill_md}

        # Generate additional files based on structure
        if structure in ("standard", "complete"):
            if mode == "qa":
                scripts = self._generate_qa_scripts(qa_pairs=qa_pairs)
                files.update(scripts)

                references = self._generate_qa_references(
                    source_file=source_file,
                    overview=overview,
                    qa_pairs=qa_pairs,
                )
                files.update(references)
            else:
                scripts = self._generate_scripts(
                    workflows=workflows,
                    code_assessment=code_assessment,
                )
                files.update(scripts)

                references = self._generate_references(
                    source_file=source_file,
                    overview=overview,
                )
                files.update(references)

        if structure == "complete":
            if mode == "qa":
                templates = self._generate_qa_templates(qa_pairs=qa_pairs)
                files.update(templates)
            else:
                templates = self._generate_templates(
                    workflows=workflows,
                    code_assessment=code_assessment,
                )
                files.update(templates)

        # Build metadata
        metadata = {
            "source_file": source_file,
            "structure": structure,
            "mode": mode,
            "complexity": code_assessment.get("complexity", "unknown"),
        }

        if mode == "qa":
            metadata["qa_count"] = len(qa_pairs)
            # Group by category
            categories = {}
            for qa in qa_pairs:
                categories[qa.category] = categories.get(qa.category, 0) + 1
            metadata["qa_categories"] = categories
        else:
            metadata["workflow_count"] = len(workflows)

        if overview:
            metadata["document_type"] = overview.get("document_type", "unknown")
            metadata["audience"] = overview.get("audience", "general")
            metadata["topics"] = overview.get("topics", [])

        return GeneratedSkill(name=skill_name, files=files, metadata=metadata)

    def _generate_skill_md(
        self,
        skill_name: str,
        workflows: List[Workflow],
        code_assessment: Dict[str, Any],
        structure: str,
        source_file: str,
        overview: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate SKILL.md content."""
        lines = [
            f"# {skill_name}",
            "",
            f"Generated from: {source_file}",
            "",
            "## Overview",
            "",
        ]

        if overview:
            lines.append(
                f"**Document Type:** {overview.get('document_type', 'Unknown')}"
            )
            lines.append(f"**Audience:** {overview.get('audience', 'General')}")
            topics = overview.get("topics", [])
            if topics:
                lines.append(f"**Topics:** {', '.join(topics)}")
            lines.append("")

        lines.extend(
            [
                f"**Complexity:** {code_assessment.get('complexity', 'unknown')}",
                "",
                "## Workflows",
                "",
            ]
        )

        # Add each workflow
        for workflow in workflows:
            lines.extend(
                [f"### {workflow.name}", "", f"**Trigger:** {workflow.trigger}", ""]
            )

            for i, step in enumerate(workflow.steps, 1):
                lines.append(f"{i}. **{step.name}** - {step.description}")
                if step.commands:
                    lines.append("   ```")
                    for cmd in step.commands:
                        lines.append(f"   {cmd}")
                    lines.append("   ```")
                    lines.append("")

            lines.append("")

        # Add complexity information
        lines.extend(
            [
                "## Code Assessment",
                "",
                f"- **Complexity:** {code_assessment.get('complexity', 'unknown')}",
                f"- **Code Blocks:** {code_assessment.get('block_count', 0)}",
            ]
        )

        languages = code_assessment.get("languages", [])
        if languages:
            lines.append(f"- **Languages:** {', '.join(languages)}")

        lines.append("")

        # Add structure-specific notes
        if structure == "minimal":
            lines.extend(
                [
                    "## Notes",
                    "",
                    "This skill uses a minimal structure. For more detailed workflows,",
                    "consider regenerating with `--structure standard` or `--structure complete`.",
                    "",
                ]
            )
        elif structure == "standard":
            lines.extend(
                [
                    "## Additional Files",
                    "",
                    "- `scripts/` - Automation scripts for workflows",
                    "- `references/` - Reference documentation",
                    "",
                ]
            )
        elif structure == "complete":
            lines.extend(
                [
                    "## Additional Files",
                    "",
                    "- `scripts/` - Automation scripts for workflows",
                    "- `references/` - Reference documentation",
                    "- `templates/` - Template files for customization",
                    "",
                ]
            )

        return "\n".join(lines)

    def _generate_qa_skill_md(
        self,
        skill_name: str,
        qa_pairs: List[QAPair],
        code_assessment: Dict[str, Any],
        structure: str,
        source_file: str,
        overview: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate SKILL.md content for Q&A mode."""
        lines = [
            f"# {skill_name}",
            "",
            f"Generated from: {source_file}",
            "",
            "## Overview",
            "",
            "This skill provides question-answer pairs extracted from documentation.",
            "Use it to quickly find answers to common questions.",
            "",
        ]

        if overview:
            lines.append(
                f"**Document Type:** {overview.get('document_type', 'Unknown')}"
            )
            lines.append(f"**Audience:** {overview.get('audience', 'General')}")
            topics = overview.get("topics", [])
            if topics:
                lines.append(f"**Topics:** {', '.join(topics)}")
            lines.append("")

        # Add Q&A summary
        lines.extend(
            [
                "## Q&A Summary",
                "",
                f"**Total Q&A Pairs:** {len(qa_pairs)}",
                "",
            ]
        )

        # Group by category
        if qa_pairs:
            categories: Dict[str, List[QAPair]] = {}
            for qa in qa_pairs:
                cat = qa.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(qa)

            lines.append("**Categories:**")
            for cat, qas in sorted(categories.items()):
                lines.append(f"- {cat.capitalize()}: {len(qas)} questions")
            lines.append("")

            # Add all Q&A pairs
            lines.extend(
                [
                    "## Questions & Answers",
                    "",
                ]
            )

            for cat, qas in sorted(categories.items()):
                lines.append(f"### {cat.capitalize()}")
                lines.append("")
                for i, qa in enumerate(qas, 1):
                    lines.append(f"**Q{i}.** {qa.question}")
                    lines.append("")
                    lines.append(f"{qa.answer}")
                    lines.append("")
                    if qa.source_section:
                        lines.append(f"*Source: {qa.source_section}*")
                        lines.append("")

        # Add complexity information
        lines.extend(
            [
                "## Document Assessment",
                "",
                f"- **Complexity:** {code_assessment.get('complexity', 'unknown')}",
                f"- **Code Blocks:** {code_assessment.get('block_count', 0)}",
            ]
        )

        languages = code_assessment.get("languages", [])
        if languages:
            lines.append(f"- **Languages:** {', '.join(languages)}")

        lines.append("")

        # Add structure-specific notes
        if structure == "minimal":
            lines.extend(
                [
                    "## Notes",
                    "",
                    "This skill uses a minimal structure. For more detailed Q&A organization,",
                    "consider regenerating with `--structure standard` or `--structure complete`.",
                    "",
                ]
            )
        elif structure == "standard":
            lines.extend(
                [
                    "## Additional Files",
                    "",
                    "- `scripts/` - Utility scripts for Q&A processing",
                    "- `references/` - Reference documentation and Q&A index",
                    "",
                ]
            )
        elif structure == "complete":
            lines.extend(
                [
                    "## Additional Files",
                    "",
                    "- `scripts/` - Utility scripts for Q&A processing",
                    "- `references/` - Reference documentation and Q&A index",
                    "- `templates/` - Template files for adding new Q&A pairs",
                    "",
                ]
            )

        return "\n".join(lines)

    def _generate_scripts(
        self, workflows: List[Workflow], code_assessment: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate script files for workflows."""
        files = {}

        # Generate validation script
        validate_script = self._generate_validate_script(workflows)
        files["scripts/validate.sh"] = validate_script

        # Generate setup script for workflows with commands
        setup_script = self._generate_setup_script(workflows, code_assessment)
        if setup_script:
            files["scripts/setup.sh"] = setup_script

        return files

    def _generate_validate_script(self, workflows: List[Workflow]) -> str:
        """Generate a validation script for workflows."""
        lines = [
            "#!/bin/bash",
            "# Validation script generated by pdf2skill",
            "",
            "set -e",
            "",
            "echo 'Running validation checks...'",
            "",
        ]

        check_num = 1
        for workflow in workflows:
            lines.append(f"# Workflow: {workflow.name}")
            for step in workflow.steps:
                if step.validation:
                    lines.append(f"echo 'Check {check_num}: {step.name}'")
                    lines.append(f"{step.validation}")
                    lines.append("echo '✓ Passed'")
                    lines.append("")
                    check_num += 1

        if check_num == 1:
            # No validation rules, add a placeholder
            lines.append("# No specific validation rules defined")
            lines.append("echo 'No validation checks configured.'")
            lines.append(
                "echo 'Add validation rules to your workflows for automatic checks.'"
            )

        lines.append("echo 'Validation complete.'")
        return "\n".join(lines)

    def _generate_setup_script(
        self, workflows: List[Workflow], code_assessment: Dict[str, Any]
    ) -> Optional[str]:
        """Generate a setup script for workflows with installation commands."""
        install_commands = []

        for workflow in workflows:
            for step in workflow.steps:
                if step.commands:
                    for cmd in step.commands:
                        # Detect installation commands
                        cmd_lower = cmd.lower()
                        if any(
                            kw in cmd_lower
                            for kw in [
                                "install",
                                "setup",
                                "init",
                                "pip",
                                "npm",
                                "yarn",
                                "brew",
                                "apt",
                                "dnf",
                            ]
                        ):
                            install_commands.append(cmd)

        if not install_commands:
            return None

        lines = [
            "#!/bin/bash",
            "# Setup script generated by pdf2skill",
            "",
            "set -e",
            "",
            "echo 'Running setup...'",
            "",
        ]

        for cmd in install_commands:
            lines.append(f"echo 'Executing: {cmd}'")
            lines.append(cmd)
            lines.append("")

        lines.append("echo 'Setup complete.'")
        return "\n".join(lines)

    def _generate_qa_scripts(self, qa_pairs: List[QAPair]) -> Dict[str, str]:
        """Generate script files for Q&A mode."""
        files = {}

        # Generate search script
        search_script = self._generate_qa_search_script(qa_pairs)
        files["scripts/search_qa.sh"] = search_script

        # Generate export script
        export_script = self._generate_qa_export_script()
        files["scripts/export_qa.sh"] = export_script

        return files

    def _generate_qa_search_script(self, qa_pairs: List[QAPair]) -> str:
        """Generate a search script for Q&A pairs."""
        lines = [
            "#!/bin/bash",
            "# Q&A Search script generated by pdf2skill",
            "",
            "# Usage: ./search_qa.sh <keyword>",
            "",
            'KEYWORD="$1"',
            "",
            'if [ -z "$KEYWORD" ]; then',
            '    echo "Usage: $0 <keyword>"',
            '    echo "Example: $0 installation"',
            "    exit 1",
            "fi",
            "",
            'echo "Searching Q&A for: $KEYWORD"',
            'echo ""',
        ]

        # Add search logic using grep on the SKILL.md
        lines.extend(
            [
                "# Search in SKILL.md",
                'grep -i -A 5 -B 2 "$KEYWORD" ../SKILL.md || echo "No matches found"',
                "",
            ]
        )

        return "\n".join(lines)

    def _generate_qa_export_script(self) -> str:
        """Generate an export script for Q&A pairs."""
        return """#!/bin/bash
# Q&A Export script generated by pdf2skill

# Usage: ./export_qa.sh [format]
# Formats: json, csv, markdown (default: json)

FORMAT="${1:-json}"
SKILL_MD="../SKILL.md"

echo "Exporting Q&A pairs to $FORMAT format..."

# This is a template script
# Implement actual export logic based on your needs

case "$FORMAT" in
    json)
        echo "Exporting to JSON..."
        # Add JSON export logic here
        ;;
    csv)
        echo "Exporting to CSV..."
        # Add CSV export logic here
        ;;
    markdown)
        echo "Exporting to Markdown..."
        # Add Markdown export logic here
        ;;
    *)
        echo "Unknown format: $FORMAT"
        echo "Supported formats: json, csv, markdown"
        exit 1
        ;;
esac

echo "Export complete."
"""

    def _generate_references(
        self, source_file: str, overview: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Generate reference files."""
        files = {}

        # Generate a reference index
        lines = ["# References", "", f"Source: {source_file}", ""]

        if overview:
            topics = overview.get("topics", [])
            if topics:
                lines.append("## Topics Covered")
                lines.append("")
                for topic in topics:
                    lines.append(f"- {topic}")
                lines.append("")

        lines.extend(
            [
                "## External Links",
                "",
                "<!-- Add relevant external documentation links here -->",
                "",
            ]
        )

        files["references/README.md"] = "\n".join(lines)
        return files

    def _generate_qa_references(
        self,
        source_file: str,
        overview: Optional[Dict[str, Any]] = None,
        qa_pairs: Optional[List[QAPair]] = None,
    ) -> Dict[str, str]:
        """Generate reference files for Q&A mode."""
        files = {}
        qa_pairs = qa_pairs or []

        # Generate Q&A index
        lines = [
            "# Q&A Index",
            "",
            f"Source: {source_file}",
            "",
        ]

        if overview:
            topics = overview.get("topics", [])
            if topics:
                lines.append("## Topics Covered")
                lines.append("")
                for topic in topics:
                    lines.append(f"- {topic}")
                lines.append("")

        # Add Q&A summary
        if qa_pairs:
            lines.extend(
                [
                    "## Q&A Summary",
                    "",
                    f"**Total Questions:** {len(qa_pairs)}",
                    "",
                ]
            )

            # Group by category
            categories: Dict[str, List[QAPair]] = {}
            for qa in qa_pairs:
                cat = qa.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(qa)

            lines.append("### By Category")
            lines.append("")
            for cat, qas in sorted(categories.items()):
                lines.append(f"#### {cat.capitalize()} ({len(qas)})")
                lines.append("")
                for qa in qas:
                    lines.append(f"- {qa.question}")
                lines.append("")

        files["references/qa_index.md"] = "\n".join(lines)

        # Generate category reference
        if qa_pairs:
            categories_list = list(set(qa.category for qa in qa_pairs))
            lines = [
                "# Categories",
                "",
                "This document describes the Q&A categories used in this skill.",
                "",
            ]

            category_descriptions = {
                "setup": "Questions about installation and initial configuration",
                "usage": "Questions about how to use features or functionality",
                "troubleshooting": "Questions about solving problems and errors",
                "concept": "Questions about concepts, theory, and architecture",
                "configuration": "Questions about configuration options and settings",
                "general": "General questions that don't fit other categories",
            }

            for cat in sorted(categories_list):
                desc = category_descriptions.get(cat, "General questions")
                lines.append(f"## {cat.capitalize()}")
                lines.append("")
                lines.append(desc)
                lines.append("")

            files["references/categories.md"] = "\n".join(lines)

        return files

    def _generate_templates(
        self, workflows: List[Workflow], code_assessment: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate template files for complete structure."""
        files = {}

        # Generate a workflow template
        lines = [
            "# Workflow Template",
            "",
            "Use this template to create new workflows:",
            "",
            "```yaml",
            "name: Workflow Name",
            "trigger: When this workflow should be used",
            "steps:",
            "  - name: Step 1",
            "    description: Description of step 1",
            "    commands:",
            "      - command1",
            "      - command2",
            "    validation: Optional validation command",
            "```",
            "",
        ]

        files["templates/workflow_template.md"] = "\n".join(lines)

        # Generate a code template based on languages detected
        languages = code_assessment.get("languages", [])

        if "python" in languages or not languages:
            files["templates/code_template.py"] = self._generate_python_template()
        if "javascript" in languages or "typescript" in languages:
            files["templates/code_template.js"] = self._generate_js_template()
        if "bash" in languages or "shell" in languages:
            files["templates/code_template.sh"] = self._generate_bash_template()

        return files

    def _generate_qa_templates(self, qa_pairs: List[QAPair]) -> Dict[str, str]:
        """Generate template files for Q&A mode."""
        files = {}

        # Generate Q&A template
        lines = [
            "# Q&A Template",
            "",
            "Use this template to add new Q&A pairs:",
            "",
            "```yaml",
            "qa_pair:",
            '  question: "Your question here?"',
            "  answer: |",
            "    Your detailed answer here.",
            "    Can span multiple lines.",
            "  category: general  # Options: setup, usage, troubleshooting, concept, configuration, general",
            '  source_section: "Section name from source document"',
            "```",
            "",
            "## Categories",
            "",
            "- **setup**: Installation and initial configuration questions",
            "- **usage**: How-to and feature usage questions",
            "- **troubleshooting**: Problem-solving and error resolution",
            "- **concept**: Architecture, theory, and concept explanations",
            "- **configuration**: Settings and configuration options",
            "- **general**: General questions that don't fit above",
            "",
        ]

        files["templates/qa_template.md"] = "\n".join(lines)

        # Generate JSON template
        json_template = """{
  "qa_pairs": [
    {
      "question": "Example question?",
      "answer": "Example answer with details.",
      "category": "general",
      "source_section": "Introduction"
    }
  ]
}
"""
        files["templates/qa_template.json"] = json_template

        return files

    def _generate_python_template(self) -> str:
        """Generate a Python code template."""
        return """#!/usr/bin/env python3
\"\"\"
Python template generated by pdf2skill.
Customize this template for your specific use case.
\"\"\"

def main():
    \"\"\"Main function.\"\"\"
    pass


if __name__ == "__main__":
    main()
"""

    def _generate_js_template(self) -> str:
        """Generate a JavaScript code template."""
        return """/**
 * JavaScript template generated by pdf2skill.
 * Customize this template for your specific use case.
 */

async function main() {
    // Add your code here
}

main().catch(console.error);
"""

    def _generate_bash_template(self) -> str:
        """Generate a Bash code template."""
        return """#!/bin/bash
# Bash template generated by pdf2skill
# Customize this template for your specific use case

set -e

main() {
    # Add your code here
    echo "Hello from pdf2skill"
}

main "$@"
"""

    def write_skill(self, skill: GeneratedSkill, output_dir: Path) -> Path:
        """
        Write a generated skill to disk.

        Args:
            skill: GeneratedSkill to write
            output_dir: Directory to write the skill to

        Returns:
            Path to the written skill directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for relative_path, content in skill.files.items():
            file_path = output_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        return output_path
