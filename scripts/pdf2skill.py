#!/usr/bin/env python3
"""
pdf2skill - Convert PDF/EPUB technical documents into executable AI skills

Usage:
    python pdf2skill.py <input_file> --output <output_directory>

Example:
    python pdf2skill.py book.pdf --output ./my-skill
    python pdf2skill.py manual.epub --output ./manual-skill
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Support both direct execution and module import
if __name__ == "__main__" and __package__ is None:
    # Add parent directory to path for direct script execution
    _script_dir = Path(__file__).resolve().parent
    _skill_dir = _script_dir.parent
    if str(_skill_dir) not in sys.path:
        sys.path.insert(0, str(_skill_dir))

from scripts.config import Config, LLMConfig
from scripts.document_parser import DocumentParser, ParsedDocument
from scripts.ai_analyzer import AIAnalyzer, DocumentAnalysis
from scripts.skill_generator import SkillGenerator, GeneratedSkill
from scripts.ocr_parser import OCRConfig


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Convert PDF/EPUB technical documents into executable AI skills"
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input PDF or EPUB file"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=".",
        help="Output directory for the generated skill (default: current directory)"
    )
    parser.add_argument(
        "--name", "-n",
        type=str,
        help="Name for the generated skill (default: derived from input file)"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        help="LLM model to use (e.g., claude-sonnet-4-6, gpt-4o)"
    )
    parser.add_argument(
        "--provider", "-p",
        type=str,
        choices=["anthropic", "openai", "openai-compatible"],
        help="LLM provider (anthropic, openai, openai-compatible)"
    )
    parser.add_argument(
        "--structure", "-s",
        type=str,
        choices=["minimal", "standard", "complete", "auto"],
        default="auto",
        help="Output structure type (default: auto)"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force OCR parsing for PDFs (useful for PDFs with encoding issues)"
    )
    parser.add_argument(
        "--ocr-language",
        type=str,
        default="ch",
        choices=["ch", "en", "ml"],
        help="OCR language: ch (Chinese), en (English), ml (multilingual). Default: ch"
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable automatic OCR fallback for PDFs with encoding issues"
    )

    return parser.parse_args()


def load_config(args: argparse.Namespace) -> Config:
    """
    Load configuration from environment, file, and CLI arguments.

    Priority: CLI args > config file > environment variables > defaults

    Args:
        args: Parsed CLI arguments

    Returns:
        Merged configuration object
    """
    # Start with environment configuration
    config = Config.from_env()

    # Load from config file if specified
    if args.config:
        config_path = Path(args.config)
        file_config = Config.from_file(config_path)
        config = config.merge(file_config)

    # Apply CLI arguments (highest priority)
    cli_llm = LLMConfig(
        provider=args.provider if args.provider else config.llm.provider,
        model=args.model if args.model else config.llm.model,
        base_url=config.llm.base_url,
        api_key=config.llm.api_key,
    )

    cli_config = Config(
        llm=cli_llm,
        output_dir=Path(args.output) if args.output else config.output_dir,
        structure=args.structure if args.structure else config.structure,
    )

    return config.merge(cli_config)


def process_document(
    input_path: Path,
    output_dir: Path,
    config: Config,
    skill_name: Optional[str] = None,
    verbose: bool = False,
    ocr_config: Optional[OCRConfig] = None,
    force_ocr: bool = False,
) -> Optional[GeneratedSkill]:
    """
    Process a single document and generate a skill.

    Args:
        input_path: Path to the input PDF/EPUB file
        output_dir: Output directory for generated skill
        config: Configuration object
        skill_name: Optional skill name (derived from filename if not provided)
        verbose: Enable verbose output
        ocr_config: OCR configuration for PDFs with encoding issues
        force_ocr: Force OCR parsing even if text seems valid

    Returns:
        GeneratedSkill object if successful, None otherwise

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If file format is not supported
    """
    # Validate input file
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Check file extension
    valid_extensions = {".pdf", ".epub"}
    if input_path.suffix.lower() not in valid_extensions:
        raise ValueError(
            f"Unsupported file format: {input_path.suffix}. "
            f"Supported formats: {', '.join(valid_extensions)}"
        )

    # Derive skill name from filename if not provided
    if skill_name is None:
        skill_name = input_path.stem

    if verbose:
        print(f"Input file: {input_path}")
        print(f"Output directory: {output_dir}")
        print(f"Skill name: {skill_name}")
        print(f"Structure: {config.structure}")
        print(f"Provider: {config.llm.provider}")
        print(f"Model: {config.llm.model}")
        if force_ocr:
            print(f"OCR: Forced")
        elif ocr_config and ocr_config.enabled:
            print(f"OCR: Auto-detect (language: {ocr_config.language})")

    # Step 1: Parse document
    if verbose:
        print("\n[1/4] Parsing document...")

    parser = DocumentParser(
        ocr_config=ocr_config,
        force_ocr=force_ocr,
    )
    parsed_doc = parser.parse(input_path)

    if verbose:
        print(f"  - Extracted {len(parsed_doc.sections)} sections")
        print(f"  - Found {len(parsed_doc.code_blocks)} code blocks")
        print(f"  - Found {len(parsed_doc.tables)} tables")
        if parsed_doc.used_ocr:
            print(f"  - OCR fallback used: {parsed_doc.ocr_fallback_reason}")

    # Step 2: Analyze with AI
    if verbose:
        print("\n[2/4] Analyzing document with AI...")

    analyzer = AIAnalyzer(
        provider=config.llm.provider,
        model=config.llm.model,
        api_key=config.llm.api_key,
        base_url=config.llm.base_url,
    )

    # Convert ParsedDocument to dict for analyzer
    parsed_dict = {
        "text_content": parsed_doc.text_content,
        "code_blocks": [
            {"language": cb.language, "code": cb.code}
            for cb in parsed_doc.code_blocks
        ],
    }

    analysis = analyzer.analyze_document(parsed_dict)

    if verbose:
        print(f"  - Document type: {analysis.document_type}")
        print(f"  - Audience: {analysis.audience}")
        print(f"  - Complexity: {analysis.complexity}")
        print(f"  - Workflows found: {len(analysis.workflows)}")

    # Step 3: Determine structure
    if verbose:
        print("\n[3/4] Determining output structure...")

    generator = SkillGenerator()

    # Estimate page count from content
    # Rough estimate: ~3000 characters per page
    estimated_pages = len(parsed_doc.text_content) // 3000
    code_block_count = len(parsed_doc.code_blocks)

    structure = generator.determine_structure(
        page_count=estimated_pages,
        code_blocks=code_block_count,
        force=config.structure if config.structure != "auto" else None
    )

    if verbose:
        print(f"  - Estimated pages: {estimated_pages}")
        print(f"  - Code blocks: {code_block_count}")
        print(f"  - Selected structure: {structure}")

    # Step 4: Generate skill
    if verbose:
        print("\n[4/4] Generating skill...")

    skill = generator.generate(
        skill_name=skill_name,
        workflows=analysis.workflows,
        code_assessment={
            "complexity": analysis.complexity,
            "block_count": code_block_count,
            "languages": list(set(cb.language for cb in parsed_doc.code_blocks)),
        },
        structure=structure,
        source_file=input_path.name,
        overview={
            "document_type": analysis.document_type,
            "audience": analysis.audience,
            "topics": analysis.topics,
        },
        validation_rules=analysis.validation_rules,
    )

    # Write skill to disk
    output_path = generator.write_skill(skill, output_dir)

    if verbose:
        print(f"\nSkill generated successfully!")
        print(f"Output: {output_path}")
        for file_path in skill.files:
            print(f"  - {file_path}")

    return skill


def main() -> int:
    """
    Main entry point for pdf2skill.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()

    try:
        # Load configuration
        config = load_config(args)

        # Resolve paths
        input_path = Path(args.input_file).resolve()
        output_path = Path(args.output).resolve()

        # Setup OCR config
        ocr_config = None
        if not args.no_ocr:
            ocr_config = OCRConfig(
                enabled=True,
                language=args.ocr_language,
            )

        # Process document
        process_document(
            input_path=input_path,
            output_dir=output_path,
            config=config,
            skill_name=args.name,
            verbose=args.verbose,
            ocr_config=ocr_config,
            force_ocr=args.force_ocr,
        )

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except PermissionError as e:
        print(f"Authentication error: {e}", file=sys.stderr)
        print("Please check your API key configuration.", file=sys.stderr)
        return 2

    except ConnectionError as e:
        print(f"Connection error: {e}", file=sys.stderr)
        print("Please check your network connection.", file=sys.stderr)
        return 3

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 4


if __name__ == "__main__":
    sys.exit(main())