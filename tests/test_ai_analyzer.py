# tests/test_ai_analyzer.py
import pytest
from unittest.mock import Mock, patch
from scripts.ai_analyzer import AIAnalyzer, Workflow, WorkflowStep, DocumentAnalysis


def test_workflow_creation():
    """Test creating a workflow object."""
    step = WorkflowStep(
        name="Setup",
        description="Initialize the project",
        commands=["npm install", "npm run setup"],
        validation="Check if node_modules exists"
    )
    workflow = Workflow(
        name="Setup Project",
        trigger="When starting a new project",
        steps=[step],
        complexity="simple"
    )
    assert workflow.name == "Setup Project"
    assert len(workflow.steps) == 1


def test_analyze_document_overview():
    """Test document overview analysis."""
    with patch('scripts.ai_analyzer.AIAnalyzer._call_llm') as mock_llm:
        mock_llm.return_value = {
            "document_type": "technical_manual",
            "audience": "developers",
            "topics": ["setup", "configuration", "usage"],
            "complexity": "medium"
        }

        analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")
        result = analyzer.analyze_overview("Sample document content")

        assert result["document_type"] == "technical_manual"
        assert "developers" in result["audience"]


def test_extract_workflows():
    """Test workflow extraction."""
    with patch('scripts.ai_analyzer.AIAnalyzer._call_llm') as mock_llm:
        mock_llm.return_value = {
            "workflows": [
                {
                    "name": "Installation",
                    "trigger": "When setting up the tool",
                    "steps": [
                        {"name": "Download", "description": "Download the package"},
                        {"name": "Install", "description": "Run installer"}
                    ]
                }
            ]
        }

        analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")
        result = analyzer.extract_workflows("Installation guide content")

        assert len(result) == 1
        assert result[0].name == "Installation"


def test_assess_code_complexity():
    """Test code complexity assessment."""
    analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")

    # Simple code
    simple_code = [{"language": "bash", "code": "echo 'hello'"}]
    result = analyzer.assess_code_complexity(simple_code)
    assert result == "simple"

    # Medium complexity code
    medium_code = [
        {"language": "python", "code": "class Complex:\n    def __init__(self):\n        ..."},
        {"language": "python", "code": "def advanced():\n    ..."}
    ]
    result = analyzer.assess_code_complexity(medium_code)
    assert result == "medium"

    # Complex code - multiple classes, functions, async, imports
    complex_code = [
        {"language": "python", "code": "import asyncio\nimport logging\n\nclass DataProcessor:\n    async def process(self, data):\n        if data:\n            for item in data:\n                await self._handle(item)\n"},
        {"language": "python", "code": "class Handler:\n    def __init__(self):\n        self.logger = logging.getLogger(__name__)\n    async def _handle(self, item):\n        try:\n            await self._process_item(item)\n        except Exception as e:\n            self.logger.error(e)"},
        {"language": "python", "code": "async def main():\n    processor = DataProcessor()\n    await processor.process([1, 2, 3])"}
    ]
    result = analyzer.assess_code_complexity(complex_code)
    assert result == "complex"


def test_generate_validation_rules():
    """Test validation rule generation."""
    with patch('scripts.ai_analyzer.AIAnalyzer._call_llm') as mock_llm:
        mock_llm.return_value = {
            "validation_rules": [
                {"step": "Setup", "type": "command", "command": "test -f package.json"},
                {"step": "Install", "type": "output_check", "expected": "installed successfully"}
            ]
        }

        analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")
        workflow = Workflow(name="Test", trigger="When needed", steps=[])
        result = analyzer.generate_validation_rules(workflow, "medium")

        assert len(result) == 2
        assert result[0]["step"] == "Setup"


def test_analyze_document():
    """Test the main analyze_document method that orchestrates all 4 stages."""
    with patch('scripts.ai_analyzer.AIAnalyzer.analyze_overview') as mock_overview, \
         patch('scripts.ai_analyzer.AIAnalyzer.extract_workflows') as mock_workflows, \
         patch('scripts.ai_analyzer.AIAnalyzer.generate_validation_rules') as mock_validation:

        # Mock Stage 1: Document overview
        mock_overview.return_value = {
            "document_type": "tutorial",
            "audience": "developers",
            "topics": ["setup", "configuration"],
            "complexity": "medium"
        }

        # Mock Stage 2: Workflow extraction
        mock_workflows.return_value = [
            Workflow(
                name="Setup Project",
                trigger="When starting a new project",
                steps=[
                    WorkflowStep(name="Install", description="Install dependencies", commands=["npm install"]),
                    WorkflowStep(name="Configure", description="Set up configuration", commands=["npm run setup"])
                ],
                complexity="medium"
            )
        ]

        # Mock Stage 4: Validation rules
        mock_validation.return_value = [
            {"step": "Install", "type": "file_check", "file": "node_modules"},
            {"step": "Configure", "type": "command", "command": "test -f config.json"}
        ]

        # Create analyzer and run full analysis
        analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")
        parsed_doc = {
            "text_content": "Sample tutorial content about setup and configuration.",
            "code_blocks": [{"language": "bash", "code": "npm install\nnpm run setup"}]
        }

        result = analyzer.analyze_document(parsed_doc)

        # Verify the result
        assert isinstance(result, DocumentAnalysis)
        assert result.document_type == "tutorial"
        assert result.audience == "developers"
        assert "setup" in result.topics
        assert result.complexity == "medium"
        assert len(result.workflows) == 1
        assert result.workflows[0].name == "Setup Project"
        assert len(result.validation_rules) == 2

        # Verify all stages were called
        mock_overview.assert_called_once()
        mock_workflows.assert_called_once()
        mock_validation.assert_called_once()


def test_analyze_document_complexity_escalation():
    """Test that analyze_document uses the higher complexity between document and code."""
    with patch('scripts.ai_analyzer.AIAnalyzer.analyze_overview') as mock_overview, \
         patch('scripts.ai_analyzer.AIAnalyzer.extract_workflows') as mock_workflows, \
         patch('scripts.ai_analyzer.AIAnalyzer.generate_validation_rules') as mock_validation:

        # Mock document says "simple" but code is actually "complex"
        mock_overview.return_value = {
            "document_type": "reference",
            "audience": "advanced_users",
            "topics": ["api", "internals"],
            "complexity": "simple"
        }

        mock_workflows.return_value = []
        mock_validation.return_value = []

        analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")

        # Code with complex patterns
        parsed_doc = {
            "text_content": "Reference documentation.",
            "code_blocks": [
                {"language": "python", "code": "import asyncio\n\nclass ComplexProcessor:\n    async def process(self):\n        for item in self.items:\n            await self._handle(item)"},
                {"language": "python", "code": "def another_function():\n    pass"}
            ]
        }

        result = analyzer.analyze_document(parsed_doc)

        # Complexity should be "complex" (from code), not "simple" (from document)
        assert result.complexity == "complex"


def test_analyze_document_empty_input():
    """Test analyze_document handles empty input gracefully."""
    with patch('scripts.ai_analyzer.AIAnalyzer.analyze_overview') as mock_overview, \
         patch('scripts.ai_analyzer.AIAnalyzer.extract_workflows') as mock_workflows, \
         patch('scripts.ai_analyzer.AIAnalyzer.generate_validation_rules') as mock_validation:

        mock_overview.return_value = {
            "document_type": "unknown",
            "audience": "general",
            "topics": [],
            "complexity": "medium"
        }
        mock_workflows.return_value = []
        mock_validation.return_value = []

        analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")
        result = analyzer.analyze_document({})

        assert result.document_type == "unknown"
        assert result.audience == "general"
        assert result.topics == []
        assert result.complexity == "medium"
        assert result.workflows == []
        assert result.validation_rules == []


def test_call_llm_connection_error():
    """Test _call_llm handles connection errors properly."""
    from scripts.ai_analyzer import AIAnalyzer

    analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")

    with patch.object(analyzer, '_get_client') as mock_client:
        mock_client.return_value.messages.create.side_effect = Exception("Connection timeout")

        with pytest.raises(ConnectionError) as exc_info:
            analyzer._call_llm("test prompt")

        assert "API connection failed" in str(exc_info.value)


def test_call_llm_rate_limit_error():
    """Test _call_llm handles rate limit errors properly."""
    from scripts.ai_analyzer import AIAnalyzer

    analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")

    with patch.object(analyzer, '_get_client') as mock_client:
        mock_client.return_value.messages.create.side_effect = Exception("Rate limit exceeded (429)")

        with pytest.raises(RuntimeError) as exc_info:
            analyzer._call_llm("test prompt")

        assert "rate limit" in str(exc_info.value).lower()


def test_call_llm_auth_error():
    """Test _call_llm handles authentication errors properly."""
    from scripts.ai_analyzer import AIAnalyzer

    analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")

    with patch.object(analyzer, '_get_client') as mock_client:
        mock_client.return_value.messages.create.side_effect = Exception("Unauthorized (401)")

        with pytest.raises(PermissionError) as exc_info:
            analyzer._call_llm("test prompt")

        assert "authentication failed" in str(exc_info.value).lower()


def test_call_llm_openai_connection_error():
    """Test _call_llm handles connection errors for OpenAI provider."""
    from scripts.ai_analyzer import AIAnalyzer

    analyzer = AIAnalyzer(provider="openai", model="gpt-4")

    with patch.object(analyzer, '_get_client') as mock_client:
        mock_client.return_value.chat.completions.create.side_effect = Exception("Network connection failed")

        with pytest.raises(ConnectionError) as exc_info:
            analyzer._call_llm("test prompt")

        assert "API connection failed" in str(exc_info.value)


def test_call_llm_other_error():
    """Test _call_llm re-raises other exceptions."""
    from scripts.ai_analyzer import AIAnalyzer

    analyzer = AIAnalyzer(provider="anthropic", model="claude-sonnet-4-6")

    with patch.object(analyzer, '_get_client') as mock_client:
        mock_client.return_value.messages.create.side_effect = ValueError("Some other error")

        with pytest.raises(ValueError) as exc_info:
            analyzer._call_llm("test prompt")

        assert "Some other error" in str(exc_info.value)