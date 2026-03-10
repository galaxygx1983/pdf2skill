"""
AI Analyzer Module for pdf2skill.

Implements 4-stage LLM processing:
1. Document overview analysis
2. Workflow extraction
3. Code complexity assessment
4. Validation rule generation
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""

    name: str
    description: str
    commands: List[str] = field(default_factory=list)
    validation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "commands": self.commands,
            "validation": self.validation,
        }


@dataclass
class Workflow:
    """Represents an executable workflow extracted from documentation."""

    name: str
    trigger: str
    steps: List[WorkflowStep]
    complexity: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "trigger": self.trigger,
            "steps": [s.to_dict() for s in self.steps],
            "complexity": self.complexity,
        }


@dataclass
class DocumentAnalysis:
    """Complete analysis result for a document."""

    document_type: str
    audience: str
    topics: List[str]
    complexity: str
    workflows: List[Workflow]
    validation_rules: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "document_type": self.document_type,
            "audience": self.audience,
            "topics": self.topics,
            "complexity": self.complexity,
            "workflows": [w.to_dict() for w in self.workflows],
            "validation_rules": self.validation_rules,
        }


class AIAnalyzer:
    """
    AI-powered document analyzer using LLM for intelligent extraction.

    Supports multiple providers: anthropic, openai, openai-compatible
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = "claude-sonnet-4-6",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the AI analyzer.

        Args:
            provider: LLM provider (anthropic, openai, openai-compatible)
            model: Model identifier
            api_key: API key (defaults to environment variable)
            base_url: Base URL for openai-compatible providers
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self._client = None

    def _get_client(self) -> Any:
        """Lazy initialization of LLM client."""
        if self._client is not None:
            return self._client

        if self.provider == "anthropic":
            import anthropic

            api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
            self._client = anthropic.Anthropic(api_key=api_key)

        elif self.provider in ("openai", "openai-compatible"):
            import openai

            api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
            if self.provider == "openai-compatible" and self.base_url:
                self._client = openai.OpenAI(api_key=api_key, base_url=self.base_url)
            else:
                self._client = openai.OpenAI(api_key=api_key)

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        return self._client

    def _call_llm(self, prompt: str, system: str = "You are a helpful assistant.") -> Dict[str, Any]:
        """
        Call the LLM and return parsed JSON response.

        Args:
            prompt: User prompt
            system: System prompt

        Returns:
            Parsed JSON response as dictionary

        Raises:
            ConnectionError: When API connection fails
            RuntimeError: When rate limit is hit
            PermissionError: When authentication fails
            ValueError: When response cannot be parsed
        """
        client = self._get_client()

        try:
            if self.provider == "anthropic":
                response = client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text

            else:  # openai or openai-compatible
                response = client.chat.completions.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                )
                content = response.choices[0].message.content

        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e).lower()

            # Handle API connection errors
            if "connection" in error_message or "timeout" in error_message or "network" in error_message:
                raise ConnectionError(f"API connection failed: {e}") from e

            # Handle rate limit errors
            if "rate" in error_message or "limit" in error_message or "429" in error_message:
                raise RuntimeError(f"API rate limit exceeded: {e}") from e

            # Handle authentication errors
            if "auth" in error_message or "unauthorized" in error_message or "401" in error_message or "403" in error_message:
                raise PermissionError(f"API authentication failed: {e}") from e

            # Re-raise other exceptions
            raise

        # Parse JSON from response
        # Handle potential markdown code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from mixed content
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Failed to parse LLM response as JSON: {content[:200]}")

    def analyze_overview(self, text_content: str) -> Dict[str, Any]:
        """
        Stage 1: Analyze document overview.

        Args:
            text_content: Document text content

        Returns:
            Dictionary with document_type, audience, topics, complexity
        """
        system = """You are an expert document analyst. Analyze documents and return JSON responses."""

        prompt = f"""Analyze the following document and provide:
1. document_type: The type of document (e.g., technical_manual, tutorial, reference, guide)
2. audience: Target audience (e.g., developers, administrators, end_users)
3. topics: List of main topics covered
4. complexity: Overall complexity level (simple, medium, complex)

Return ONLY a JSON object with these fields.

Document content:
{text_content[:10000]}
"""
        return self._call_llm(prompt, system)

    def extract_workflows(self, text_content: str) -> List[Workflow]:
        """
        Stage 2: Extract executable workflows from document.

        Args:
            text_content: Document text content

        Returns:
            List of Workflow objects
        """
        system = """You are an expert at extracting executable workflows from technical documentation.
Return JSON responses with workflow structures."""

        prompt = f"""Extract all executable workflows from this document. For each workflow provide:
- name: Workflow name
- trigger: When this workflow should be used
- steps: List of steps, each with name and description

Return ONLY a JSON object with a "workflows" array.

Document content:
{text_content[:15000]}
"""
        result = self._call_llm(prompt, system)

        workflows = []
        for wf_data in result.get("workflows", []):
            steps = []
            for step_data in wf_data.get("steps", []):
                steps.append(
                    WorkflowStep(
                        name=step_data.get("name", ""),
                        description=step_data.get("description", ""),
                        commands=step_data.get("commands", []),
                        validation=step_data.get("validation"),
                    )
                )

            workflows.append(
                Workflow(
                    name=wf_data.get("name", ""),
                    trigger=wf_data.get("trigger", ""),
                    steps=steps,
                    complexity=wf_data.get("complexity", "medium"),
                )
            )

        return workflows

    def assess_code_complexity(self, code_blocks: List[Dict[str, str]]) -> str:
        """
        Stage 3: Assess complexity of code blocks.

        Uses heuristic analysis without LLM for efficiency.

        Args:
            code_blocks: List of dicts with 'language' and 'code' keys

        Returns:
            Complexity level: "simple", "medium", or "complex"
        """
        if not code_blocks:
            return "simple"

        total_lines = 0
        complexity_indicators = 0

        for block in code_blocks:
            code = block.get("code", "")
            lines = code.strip().split("\n")
            total_lines += len(lines)

            # Count complexity indicators
            # Class definitions
            complexity_indicators += code.count("class ")
            # Function/method definitions
            complexity_indicators += code.count("def ") + code.count("function ")
            # Control structures
            complexity_indicators += (
                code.count("if ")
                + code.count("for ")
                + code.count("while ")
                + code.count("try ")
            )
            # Async/await
            complexity_indicators += code.count("async ") + code.count("await ")
            # Imports/requires (indicates dependencies)
            complexity_indicators += code.count("import ") + code.count("require(")

        # Calculate complexity score
        avg_lines_per_block = total_lines / max(len(code_blocks), 1)
        complexity_score = complexity_indicators + (avg_lines_per_block * 0.3)

        # Factor in number of blocks
        block_factor = min(len(code_blocks), 3)

        # Determine complexity level
        # More blocks or more indicators = higher complexity
        if complexity_score < 3 and total_lines < 15 and len(code_blocks) <= 1:
            return "simple"
        elif complexity_score < 8 and total_lines < 50:
            return "medium"
        else:
            return "complex"

    def generate_validation_rules(
        self, workflow: Workflow, complexity: str
    ) -> List[Dict[str, Any]]:
        """
        Stage 4: Generate validation rules for workflow steps.

        Args:
            workflow: Workflow to generate validation for
            complexity: Workflow complexity level

        Returns:
            List of validation rule dictionaries
        """
        system = """You are an expert at creating validation rules for technical workflows.
Return JSON responses with validation rule structures."""

        workflow_json = json.dumps(workflow.to_dict(), indent=2)

        prompt = f"""Generate validation rules for this workflow:
{workflow_json}

Complexity level: {complexity}

For each step, create validation rules that verify the step was successful.
Types of validation:
- command: Run a command and check exit code
- output_check: Verify expected output text
- file_check: Verify file exists
- env_check: Verify environment variable

Return ONLY a JSON object with a "validation_rules" array.
Each rule should have: step, type, and relevant parameters (command, expected, file, etc.)
"""
        result = self._call_llm(prompt, system)
        return result.get("validation_rules", [])

    def analyze_document(self, parsed_doc: Dict[str, Any]) -> DocumentAnalysis:
        """
        Perform full document analysis through all 4 stages.

        Args:
            parsed_doc: Parsed document with 'text_content' and 'code_blocks'

        Returns:
            Complete DocumentAnalysis
        """
        text_content = parsed_doc.get("text_content", "")
        code_blocks = parsed_doc.get("code_blocks", [])

        # Stage 1: Document overview
        overview = self.analyze_overview(text_content)

        # Stage 2: Extract workflows
        workflows = self.extract_workflows(text_content)

        # Stage 3: Assess code complexity
        complexity = self.assess_code_complexity(code_blocks)

        # Use the higher of document complexity and code complexity
        complexity_levels = {"simple": 1, "medium": 2, "complex": 3}
        doc_complexity = overview.get("complexity", "medium")
        final_complexity = max(
            [complexity, doc_complexity],
            key=lambda c: complexity_levels.get(c, 2),
        )

        # Stage 4: Generate validation rules for each workflow
        all_validation_rules = []
        for workflow in workflows:
            rules = self.generate_validation_rules(workflow, final_complexity)
            all_validation_rules.extend(rules)

        return DocumentAnalysis(
            document_type=overview.get("document_type", "unknown"),
            audience=overview.get("audience", "general"),
            topics=overview.get("topics", []),
            complexity=final_complexity,
            workflows=workflows,
            validation_rules=all_validation_rules,
        )
