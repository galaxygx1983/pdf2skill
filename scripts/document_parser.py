"""
Document parser module for pdf2skill.

This module provides functionality to parse PDF and EPUB files into structured
content using the markitdown library, with support for section extraction,
code block detection, and table parsing.

For PDFs with encoding issues (embedded fonts with custom encoding),
automatic OCR fallback using PyMuPDF + PaddleOCR is provided.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from markitdown import MarkItDown

from scripts.ocr_parser import (
    OCRConfig,
    OCROptions,
    OCRParser,
    detect_encoding_issues,
    parse_with_ocr_fallback,
)

logger = logging.getLogger(__name__)


@dataclass
class CodeBlock:
    """Represents a code block extracted from document content."""
    language: str
    code: str
    line_number: Optional[int] = None


@dataclass
class Table:
    """Represents a table extracted from document content."""
    headers: list[str]
    rows: list[list[str]]
    line_number: Optional[int] = None


@dataclass
class Section:
    """Represents a section/chapter in the document."""
    title: str
    level: int
    content: str
    line_number: Optional[int] = None


@dataclass
class ParsedDocument:
    """Represents a parsed document with all its components."""
    file_path: Path
    file_type: str
    text_content: str
    sections: list[Section] = field(default_factory=list)
    code_blocks: list[CodeBlock] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    used_ocr: bool = False  # Whether OCR was used for extraction
    ocr_fallback_reason: Optional[str] = None  # Reason for OCR fallback


class DocumentParser:
    """
    Parser for PDF and EPUB documents using markitdown.

    This class handles converting documents to markdown and extracting
    structured components like sections, code blocks, and tables.

    For PDFs with encoding issues (common with Chinese PDFs using embedded
    fonts), automatic OCR fallback using PyMuPDF + PaddleOCR is provided.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".epub"}

    def __init__(
        self,
        use_docintel: bool = False,
        docintel_endpoint: Optional[str] = None,
        ocr_config: Optional[OCRConfig] = None,
        force_ocr: bool = False,
    ):
        """
        Initialize the DocumentParser.

        Args:
            use_docintel: Whether to use Azure Document Intelligence for parsing.
                         Requires Azure credentials to be configured.
            docintel_endpoint: Optional Azure Document Intelligence endpoint URL.
                              If not provided, will use the AZURE_DOCINTEL_ENDPOINT
                              environment variable.
            ocr_config: Configuration for OCR fallback parsing.
            force_ocr: Force OCR parsing even if text seems valid.
        """
        self._use_docintel = use_docintel
        self._docintel_endpoint = docintel_endpoint
        self._markitdown: Optional[MarkItDown] = None
        self._ocr_config = ocr_config or OCRConfig()
        self._force_ocr = force_ocr

    @property
    def markitdown(self) -> MarkItDown:
        """Lazy initialization of MarkItDown instance."""
        if self._markitdown is None:
            if self._use_docintel and self._docintel_endpoint:
                self._markitdown = MarkItDown(docintel_endpoint=self._docintel_endpoint)
            else:
                self._markitdown = MarkItDown()
        return self._markitdown

    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a document file and return structured content.

        For PDF files, this method first attempts direct text extraction.
        If encoding issues are detected (common with Chinese PDFs using
        embedded fonts), it automatically falls back to OCR parsing.

        Args:
            file_path: Path to the document file.

        Returns:
            ParsedDocument containing the parsed content and extracted components.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is not supported.
        """
        # Validate file extension first (before checking existence)
        extension = file_path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Convert file to markdown using markitdown
        result = self.markitdown.convert(str(file_path))

        # Get text content
        text_content = result.text_content if hasattr(result, 'text_content') else str(result)

        # Track OCR usage
        used_ocr = False
        ocr_fallback_reason = None

        # Check for encoding issues and fallback to OCR for PDFs
        if extension == ".pdf" and self._ocr_config.enabled:
            if self._force_ocr:
                logger.info("Force OCR mode enabled, using OCR parsing")
                ocr_fallback_reason = "forced"
                used_ocr = True
            elif detect_encoding_issues(text_content):
                logger.info("Detected encoding issues in extracted text, falling back to OCR")
                ocr_fallback_reason = "encoding_issues"
                used_ocr = True

            if used_ocr:
                try:
                    text_content, _ = parse_with_ocr_fallback(
                        file_path=file_path,
                        initial_text=text_content,
                        ocr_config=self._ocr_config,
                        force_ocr=True
                    )
                except Exception as e:
                    logger.warning(f"OCR fallback failed: {e}. Using original extraction.")
                    used_ocr = False
                    ocr_fallback_reason = None

        # Extract file type (without the dot)
        file_type = extension[1:]

        # Extract structured components
        sections = self.extract_sections(text_content)
        code_blocks = self.extract_code_blocks(text_content)
        tables = self.extract_tables(text_content)

        # Extract metadata if available
        metadata = {}
        if hasattr(result, 'metadata') and result.metadata:
            metadata = dict(result.metadata)

        # Add OCR info to metadata
        metadata['used_ocr'] = used_ocr
        if ocr_fallback_reason:
            metadata['ocr_fallback_reason'] = ocr_fallback_reason

        return ParsedDocument(
            file_path=file_path,
            file_type=file_type,
            text_content=text_content,
            sections=sections,
            code_blocks=code_blocks,
            tables=tables,
            metadata=metadata,
            used_ocr=used_ocr,
            ocr_fallback_reason=ocr_fallback_reason,
        )

    def extract_sections(self, text: str) -> list[Section]:
        """
        Extract sections from markdown text based on headings.

        Args:
            text: Markdown text content.

        Returns:
            List of Section objects representing the document structure.
        """
        sections = []
        lines = text.split('\n')

        # Pattern to match markdown headings
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

        current_section = None
        content_lines = []

        for line_num, line in enumerate(lines, 1):
            match = heading_pattern.match(line)
            if match:
                # Save previous section if exists
                if current_section is not None:
                    current_section.content = '\n'.join(content_lines).strip()
                    sections.append(current_section)

                # Start new section
                level = len(match.group(1))
                title = match.group(2).strip()
                current_section = Section(
                    title=title,
                    level=level,
                    content='',
                    line_number=line_num
                )
                content_lines = []
            else:
                if current_section is not None:
                    content_lines.append(line)

        # Don't forget the last section
        if current_section is not None:
            current_section.content = '\n'.join(content_lines).strip()
            sections.append(current_section)

        return sections

    def extract_code_blocks(self, text: str) -> list[CodeBlock]:
        """
        Extract code blocks from markdown text.

        Args:
            text: Markdown text content.

        Returns:
            List of CodeBlock objects found in the text.
        """
        code_blocks = []

        # Pattern to match fenced code blocks with optional language
        pattern = re.compile(
            r'```(\w*)\n(.*?)```',
            re.DOTALL
        )

        # Find all code blocks with their positions
        for match in pattern.finditer(text):
            language = match.group(1) or 'text'
            code = match.group(2)

            # Calculate line number
            line_number = text[:match.start()].count('\n') + 1

            code_blocks.append(CodeBlock(
                language=language,
                code=code.strip(),
                line_number=line_number
            ))

        return code_blocks

    def extract_tables(self, text: str) -> list[Table]:
        """
        Extract markdown tables from text.

        Args:
            text: Markdown text content.

        Returns:
            List of Table objects found in the text.
        """
        tables = []
        lines = text.split('\n')

        # Pattern to detect table separator rows
        separator_pattern = re.compile(r'^\|[\s\-:]+\|[\s\-:|]*$')

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this line looks like a table row
            if line.strip().startswith('|') and '|' in line[1:]:
                # Check if next line is a separator
                if i + 1 < len(lines) and separator_pattern.match(lines[i + 1].strip()):
                    # This is a table
                    headers = self._parse_table_row(line)
                    rows = []
                    line_number = i + 1

                    # Skip separator line
                    i += 2

                    # Parse data rows
                    while i < len(lines):
                        row_line = lines[i]
                        if row_line.strip().startswith('|') and '|' in row_line[1:]:
                            rows.append(self._parse_table_row(row_line))
                            i += 1
                        else:
                            break

                    tables.append(Table(
                        headers=headers,
                        rows=rows,
                        line_number=line_number
                    ))
                else:
                    i += 1
            else:
                i += 1

        return tables

    def _parse_table_row(self, line: str) -> list[str]:
        """
        Parse a single table row into cells.

        Args:
            line: A markdown table row line.

        Returns:
            List of cell values.
        """
        # Remove leading/trailing pipes and split
        cells = line.strip().strip('|').split('|')
        # Clean up each cell
        return [cell.strip() for cell in cells]