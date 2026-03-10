"""
OCR-based PDF parser for documents with encoding issues.

This module provides fallback OCR parsing using PyMuPDF (fitz) for rendering
and PaddleOCR for text recognition. Used when direct text extraction fails
due to embedded fonts with custom encoding.
"""

import re
import tempfile
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class OCRConfig:
    """Configuration for OCR parsing."""
    enabled: bool = True
    language: str = "ch"  # ch, en, ml (multilingual)
    dpi: int = 150  # Resolution for PDF rendering
    batch_size: int = 5  # Pages per batch for OCR
    confidence_threshold: float = 0.7  # Minimum confidence to accept text


@dataclass
class OCROptions:
    """Runtime options for OCR parsing."""
    force_ocr: bool = False  # Force OCR even if text seems valid
    skip_pages: int = 0  # Skip first N pages (e.g., covers)
    max_pages: Optional[int] = None  # Maximum pages to process


def detect_encoding_issues(text: str, threshold: float = 0.3) -> bool:
    """
    Detect if text has encoding issues (garbled characters).

    This function checks for common signs of encoding problems:
    1. High ratio of replacement characters (�)
    2. High ratio of non-printable ASCII characters in what should be text
    3. Presence of garbled Chinese patterns (consecutive high-byte chars that don't form valid UTF-8)

    Args:
        text: The text to check
        threshold: Ratio threshold above which text is considered garbled (0.0-1.0)

    Returns:
        True if encoding issues are detected, False otherwise
    """
    if not text or len(text.strip()) < 50:
        return False

    # Count problematic patterns
    total_chars = len(text)
    if total_chars == 0:
        return False

    # Pattern 1: Replacement characters
    replacement_count = text.count('\ufffd')

    # Pattern 2: Check for common garbled Chinese patterns
    # When PDF fonts are embedded with custom encoding, Chinese characters
    # often appear as sequences like "����" or mixed with printable chars
    # We look for high ratio of non-space, non-alphanumeric, non-punctuation chars

    # Count characters that are likely garbled
    # Valid UTF-8 Chinese characters are in specific ranges
    # Garbled text often has characters outside these ranges

    valid_printable = 0
    potentially_garbled = 0

    for char in text:
        if char.isspace():
            continue
        if char.isascii():
            if char.isalnum() or char in '.,;:!?\'"()-[]{}<>@#$%^&*+=/\\|_~`':
                valid_printable += 1
            else:
                # Non-printable ASCII in text content is suspicious
                potentially_garbled += 1
        else:
            # Non-ASCII character - check if it's valid Chinese
            code = ord(char)
            # Common Chinese Unicode ranges:
            # CJK Unified Ideographs: 4E00-9FFF
            # CJK Extension A: 3400-4DBF
            # CJK Extension B: 20000-2A6DF (rare)
            # CJK Symbols and Punctuation: 3000-303F
            # But garbled text often has chars outside these ranges
            if (0x4E00 <= code <= 0x9FFF or
                0x3400 <= code <= 0x4DBF or
                0x3000 <= code <= 0x303F or
                0xFF00 <= code <= 0xFFEF or  # Halfwidth and Fullwidth Forms
                code == 0x3000):  # Chinese space
                valid_printable += 1
            else:
                potentially_garbled += 1

    # Calculate garbled ratio
    total_non_space = valid_printable + potentially_garbled
    if total_non_space == 0:
        return False

    garbled_ratio = potentially_garbled / total_non_space

    # Also check replacement character ratio
    replacement_ratio = replacement_count / total_chars

    # If either ratio is high, we have encoding issues
    if garbled_ratio > threshold:
        return True
    if replacement_ratio > 0.1:  # 10% replacement chars is very bad
        return True

    # Additional check: look for patterns like "����" (4+ consecutive replacement chars)
    if re.search(r'\ufffd{4,}', text):
        return True

    return False


def has_chinese_content(text: str) -> bool:
    """
    Check if text contains Chinese characters.

    Args:
        text: Text to check

    Returns:
        True if Chinese characters are detected
    """
    if not text:
        return False

    for char in text:
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF:  # CJK Unified Ideographs
            return True
        if 0x3400 <= code <= 0x4DBF:  # CJK Extension A
            return True

    return False


class OCRParser:
    """
    PDF parser using PyMuPDF rendering and PaddleOCR.

    This class handles:
    1. Rendering PDF pages to images
    2. Running PaddleOCR on each page
    3. Combining results into structured text
    """

    def __init__(self, config: Optional[OCRConfig] = None):
        """
        Initialize OCR parser.

        Args:
            config: OCR configuration options
        """
        self.config = config or OCRConfig()
        self._fitz = None
        self._ocr = None

    def _get_fitz(self):
        """Lazy import of PyMuPDF."""
        if self._fitz is None:
            try:
                import fitz
                self._fitz = fitz
            except ImportError:
                raise ImportError(
                    "PyMuPDF (fitz) is required for OCR parsing. "
                    "Install with: pip install PyMuPDF"
                )
        return self._fitz

    def _get_ocr(self):
        """Lazy initialization of PaddleOCR."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                # PaddleOCR 3.x doesn't support show_log parameter
                self._ocr = PaddleOCR(
                    use_textline_orientation=True,
                    lang=self.config.language,
                )
            except ImportError:
                raise ImportError(
                    "PaddleOCR is required for OCR parsing. "
                    "Install with: pip install paddleocr paddlepaddle"
                )
        return self._ocr

    def parse_pdf(
        self,
        file_path: Path,
        options: Optional[OCROptions] = None
    ) -> str:
        """
        Parse a PDF file using OCR.

        Args:
            file_path: Path to the PDF file
            options: Runtime OCR options

        Returns:
            Extracted text content
        """
        options = options or OCROptions()
        fitz = self._get_fitz()
        ocr = self._get_ocr()

        # Open PDF
        doc = fitz.open(str(file_path))
        total_pages = len(doc)

        # Determine page range
        start_page = options.skip_pages
        end_page = total_pages
        if options.max_pages:
            end_page = min(start_page + options.max_pages, total_pages)

        logger.info(f"OCR parsing pages {start_page} to {end_page-1} of {total_pages}")

        all_text = []

        try:
            for page_num in range(start_page, end_page):
                page = doc[page_num]
                text = self._process_page(page, page_num, ocr)
                if text:
                    all_text.append(f"\n--- Page {page_num + 1} ---\n")
                    all_text.append(text)
        finally:
            doc.close()

        return '\n'.join(all_text)

    def _process_page(self, page, page_num: int, ocr) -> str:
        """
        Process a single page with OCR.

        Args:
            page: PyMuPDF page object
            page_num: Page number for logging
            ocr: PaddleOCR instance

        Returns:
            Extracted text from the page
        """
        fitz = self._get_fitz()

        # Render page to image
        mat = fitz.Matrix(self.config.dpi / 72, self.config.dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        # Convert to numpy array for PaddleOCR
        import numpy as np
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )

        # Convert RGBA to RGB if needed
        if pix.n == 4:
            img = img[:, :, :3]

        # Run OCR
        try:
            result = ocr.ocr(img)
        except Exception as e:
            logger.warning(f"OCR failed on page {page_num}: {e}")
            return ""

        # Extract text from results
        texts = []
        if result and len(result) > 0:
            r = result[0]
            rec_texts = r.get('rec_texts', [])
            rec_scores = r.get('rec_scores', [])

            for text, score in zip(rec_texts, rec_scores):
                if score >= self.config.confidence_threshold:
                    texts.append(text)

        return '\n'.join(texts)

    def parse_pdf_batch(
        self,
        file_path: Path,
        options: Optional[OCROptions] = None,
        progress_callback=None
    ) -> str:
        """
        Parse a PDF file using OCR with batch processing.

        Args:
            file_path: Path to the PDF file
            options: Runtime OCR options
            progress_callback: Optional callback for progress updates

        Returns:
            Extracted text content
        """
        options = options or OCROptions()
        fitz = self._get_fitz()
        ocr = self._get_ocr()

        # Open PDF
        doc = fitz.open(str(file_path))
        total_pages = len(doc)

        # Determine page range
        start_page = options.skip_pages
        end_page = total_pages
        if options.max_pages:
            end_page = min(start_page + options.max_pages, total_pages)

        all_text = []

        try:
            # Process in batches
            batch_size = self.config.batch_size
            for batch_start in range(start_page, end_page, batch_size):
                batch_end = min(batch_start + batch_size, end_page)

                # Render batch to images
                batch_images = []
                for page_num in range(batch_start, batch_end):
                    page = doc[page_num]
                    mat = fitz.Matrix(self.config.dpi / 72, self.config.dpi / 72)
                    pix = page.get_pixmap(matrix=mat)

                    import numpy as np
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                        pix.height, pix.width, pix.n
                    )
                    if pix.n == 4:
                        img = img[:, :, :3]
                    batch_images.append((page_num, img))

                # Process batch
                for page_num, img in batch_images:
                    text = self._process_page_image(img, page_num, ocr)
                    if text:
                        all_text.append(f"\n--- Page {page_num + 1} ---\n")
                        all_text.append(text)

                    if progress_callback:
                        progress_callback(page_num + 1, total_pages)

        finally:
            doc.close()

        return '\n'.join(all_text)

    def _process_page_image(self, img, page_num: int, ocr) -> str:
        """Process a page image with OCR."""
        try:
            result = ocr.ocr(img)
        except Exception as e:
            logger.warning(f"OCR failed on page {page_num}: {e}")
            return ""

        texts = []
        if result and len(result) > 0:
            r = result[0]
            rec_texts = r.get('rec_texts', [])
            rec_scores = r.get('rec_scores', [])

            for text, score in zip(rec_texts, rec_scores):
                if score >= self.config.confidence_threshold:
                    texts.append(text)

        return '\n'.join(texts)


def parse_with_ocr_fallback(
    file_path: Path,
    initial_text: str,
    ocr_config: Optional[OCRConfig] = None,
    ocr_options: Optional[OCROptions] = None,
    force_ocr: bool = False
) -> tuple[str, bool]:
    """
    Parse PDF with automatic OCR fallback.

    This function first checks if the initial text extraction has encoding
    issues, and if so, falls back to OCR parsing.

    Args:
        file_path: Path to the PDF file
        initial_text: Text extracted by markitdown/pdfminer
        ocr_config: OCR configuration
        ocr_options: OCR runtime options
        force_ocr: Force OCR even if text seems valid

    Returns:
        Tuple of (text, used_ocr) where used_ocr indicates if OCR was used
    """
    # Check if we need OCR
    needs_ocr = force_ocr or detect_encoding_issues(initial_text)

    if not needs_ocr:
        return initial_text, False

    logger.info("Detected encoding issues, falling back to OCR...")

    # Use OCR
    parser = OCRParser(ocr_config)
    ocr_text = parser.parse_pdf(file_path, ocr_options)

    return ocr_text, True