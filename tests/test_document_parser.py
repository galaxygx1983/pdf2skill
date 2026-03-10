"""
Tests for the document_parser module.

This module tests the DocumentParser class which handles parsing
PDF and EPUB files into structured content using markitdown.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from scripts.document_parser import DocumentParser, ParsedDocument


class TestDocumentParser:
    """Tests for DocumentParser class."""

    def test_parse_pdf(self):
        """Test parsing a PDF file."""
        parser = DocumentParser()
        # Use a fixture PDF file
        result = parser.parse(Path("tests/fixtures/sample.pdf"))
        assert isinstance(result, ParsedDocument)
        assert result.text_content
        assert result.file_type == "pdf"

    def test_extract_sections(self):
        """Test section extraction from parsed document."""
        parser = DocumentParser()
        text = """# Introduction
Some intro text.

## Getting Started
Getting started content.

# Chapter 1
Chapter 1 content."""

        sections = parser.extract_sections(text)
        assert len(sections) == 3
        assert sections[0].title == "Introduction"
        assert sections[1].title == "Getting Started"

    def test_extract_code_blocks(self):
        """Test code block extraction."""
        parser = DocumentParser()
        text = """Some text.

```python
def hello():
    print("Hello")
```

More text.

```bash
echo "test"
```"""

        code_blocks = parser.extract_code_blocks(text)
        assert len(code_blocks) == 2
        assert code_blocks[0].language == "python"
        assert code_blocks[1].language == "bash"

    def test_extract_tables(self):
        """Test table extraction."""
        parser = DocumentParser()
        text = """| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |"""

        tables = parser.extract_tables(text)
        assert len(tables) == 1
        assert tables[0].headers == ["Name", "Value"]

    def test_unsupported_format(self):
        """Test error handling for unsupported formats."""
        parser = DocumentParser()
        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse(Path("test.unknown"))

    def test_parse_epub(self):
        """Test parsing an EPUB file."""
        parser = DocumentParser()
        # Use a fixture EPUB file
        result = parser.parse(Path("tests/fixtures/sample.epub"))
        assert isinstance(result, ParsedDocument)
        assert result.text_content
        assert result.file_type == "epub"

    def test_file_not_found(self):
        """Test error handling for missing files."""
        parser = DocumentParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("tests/fixtures/nonexistent.pdf"))

    def test_metadata_extraction(self):
        """Test that metadata is extracted from documents."""
        parser = DocumentParser()
        result = parser.parse(Path("tests/fixtures/sample.pdf"))
        # Metadata may be empty for some PDFs, so just check it exists
        assert hasattr(result, 'metadata')
        assert isinstance(result.metadata, dict)

    def test_use_docintel_parameter_passed_to_markitdown(self):
        """Test that use_docintel and docintel_endpoint are passed to MarkItDown."""
        with patch('scripts.document_parser.MarkItDown') as mock_markitdown_class:
            mock_instance = MagicMock()
            mock_markitdown_class.return_value = mock_instance

            # Test with docintel enabled
            parser = DocumentParser(use_docintel=True, docintel_endpoint="https://example.azure.com")
            _ = parser.markitdown  # Trigger lazy initialization

            # Verify MarkItDown was called with docintel_endpoint
            mock_markitdown_class.assert_called_once_with(docintel_endpoint="https://example.azure.com")

    def test_use_docintel_false_creates_default_markitdown(self):
        """Test that default MarkItDown is created when use_docintel is False."""
        with patch('scripts.document_parser.MarkItDown') as mock_markitdown_class:
            mock_instance = MagicMock()
            mock_markitdown_class.return_value = mock_instance

            # Test without docintel
            parser = DocumentParser(use_docintel=False)
            _ = parser.markitdown  # Trigger lazy initialization

            # Verify MarkItDown was called without arguments
            mock_markitdown_class.assert_called_once_with()

    def test_use_docintel_missing_endpoint_creates_default_markitdown(self):
        """Test that default MarkItDown is created when use_docintel is True but endpoint is missing."""
        with patch('scripts.document_parser.MarkItDown') as mock_markitdown_class:
            mock_instance = MagicMock()
            mock_markitdown_class.return_value = mock_instance

            # Test with use_docintel=True but no endpoint
            parser = DocumentParser(use_docintel=True, docintel_endpoint=None)
            _ = parser.markitdown  # Trigger lazy initialization

            # Verify MarkItDown was called without arguments (fallback to default)
            mock_markitdown_class.assert_called_once_with()