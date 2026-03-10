"""
Tests for pdf2skill entry point script.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import sys

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestParseArgs:
    """Tests for parse_args function."""

    def test_basic_invocation(self):
        """Test basic CLI invocation with minimal arguments."""
        with patch('sys.argv', ['pdf2skill', 'input.pdf']):
            from scripts.pdf2skill import parse_args
            args = parse_args()
            assert args.input_file == 'input.pdf'
            assert args.output == '.'
            assert args.structure == 'auto'
            assert args.verbose is False

    def test_with_output_dir(self):
        """Test CLI with output directory."""
        with patch('sys.argv', ['pdf2skill', 'input.pdf', '-o', './output']):
            from scripts.pdf2skill import parse_args
            args = parse_args()
            assert args.input_file == 'input.pdf'
            assert args.output == './output'

    def test_with_model(self):
        """Test CLI with model specification."""
        with patch('sys.argv', ['pdf2skill', 'input.pdf', '--model', 'gpt-4o']):
            from scripts.pdf2skill import parse_args
            args = parse_args()
            assert args.model == 'gpt-4o'

    def test_with_provider(self):
        """Test CLI with provider specification."""
        with patch('sys.argv', ['pdf2skill', 'input.pdf', '--provider', 'openai']):
            from scripts.pdf2skill import parse_args
            args = parse_args()
            assert args.provider == 'openai'

    def test_with_structure(self):
        """Test CLI with structure specification."""
        with patch('sys.argv', ['pdf2skill', 'input.pdf', '--structure', 'complete']):
            from scripts.pdf2skill import parse_args
            args = parse_args()
            assert args.structure == 'complete'

    def test_with_name(self):
        """Test CLI with skill name specification."""
        with patch('sys.argv', ['pdf2skill', 'input.pdf', '--name', 'my-skill']):
            from scripts.pdf2skill import parse_args
            args = parse_args()
            assert args.name == 'my-skill'

    def test_with_config_file(self):
        """Test CLI with config file specification."""
        with patch('sys.argv', ['pdf2skill', 'input.pdf', '--config', 'config.yaml']):
            from scripts.pdf2skill import parse_args
            args = parse_args()
            assert args.config == 'config.yaml'

    def test_with_verbose(self):
        """Test CLI with verbose flag."""
        with patch('sys.argv', ['pdf2skill', 'input.pdf', '-v']):
            from scripts.pdf2skill import parse_args
            args = parse_args()
            assert args.verbose is True


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_default_config(self):
        """Test loading configuration with defaults."""
        from scripts.pdf2skill import load_config

        # Create mock args
        args = Mock()
        args.config = None
        args.provider = None
        args.model = None
        args.output = '.'
        args.structure = 'auto'

        with patch.object(sys.modules['scripts.config'].Config, 'from_env') as mock_from_env:
            mock_from_env.return_value = Mock(
                llm=Mock(provider='anthropic', model='claude-sonnet-4-6', base_url=None, api_key=None),
                output_dir=Path('.'),
                structure='auto'
            )

            config = load_config(args)
            assert config is not None

    def test_load_config_with_model_override(self):
        """Test configuration with model override from CLI."""
        from scripts.config import Config, LLMConfig
        from scripts.pdf2skill import load_config

        args = Mock()
        args.config = None
        args.provider = 'openai'
        args.model = 'gpt-4o'
        args.output = './output'
        args.structure = 'standard'

        # Use actual Config objects for proper merge behavior
        base_config = Config(
            llm=LLMConfig(provider='anthropic', model='claude-sonnet-4-6', base_url=None, api_key='test-key'),
            output_dir=Path('.'),
            structure='auto'
        )

        with patch.object(Config, 'from_env', return_value=base_config):
            config = load_config(args)
            assert config.llm.provider == 'openai'
            assert config.llm.model == 'gpt-4o'


class TestProcessDocument:
    """Tests for process_document function."""

    def test_file_not_found_error(self):
        """Test error handling for non-existent input file."""
        from scripts.pdf2skill import process_document

        with pytest.raises(FileNotFoundError) as exc_info:
            process_document(
                input_path=Path('/nonexistent/file.pdf'),
                output_dir=Path('.'),
                config=Mock(llm=Mock(provider='anthropic', model='claude-sonnet-4-6')),
                skill_name='test',
                verbose=False
            )
        assert "not found" in str(exc_info.value).lower()

    def test_unsupported_format_error(self, tmp_path):
        """Test error handling for unsupported file format."""
        from scripts.pdf2skill import process_document

        # Create a text file (not PDF or EPUB)
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is not a PDF")

        with pytest.raises(ValueError) as exc_info:
            process_document(
                input_path=test_file,
                output_dir=tmp_path,
                config=Mock(llm=Mock(provider='anthropic', model='claude-sonnet-4-6')),
                skill_name='test',
                verbose=False
            )
        assert "unsupported" in str(exc_info.value).lower()

    def test_successful_processing(self, tmp_path):
        """Test successful document processing."""
        from scripts.pdf2skill import process_document
        from scripts.document_parser import ParsedDocument, Section, CodeBlock
        from scripts.skill_generator import GeneratedSkill

        # Create a minimal test PDF
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\ntest\n%%EOF")

        # Mock the parser
        mock_parsed_doc = ParsedDocument(
            file_path=test_pdf,
            file_type='pdf',
            text_content='Test content for analysis.',
            sections=[
                Section(title='Introduction', level=1, content='This is an intro.'),
            ],
            code_blocks=[
                CodeBlock(language='python', code='print("hello")'),
            ],
            tables=[],
            metadata={}
        )

        # Mock the analysis result
        mock_analysis = Mock(
            document_type='tutorial',
            audience='developers',
            topics=['python', 'testing'],
            complexity='simple',
            workflows=[],
            validation_rules=[]
        )

        # Create actual GeneratedSkill object for return value
        expected_skill = GeneratedSkill(
            name='test-skill',
            files={'SKILL.md': '# Test Skill\n\nContent...'},
            metadata={'complexity': 'simple'}
        )

        with patch('scripts.pdf2skill.DocumentParser') as MockParser:
            with patch('scripts.pdf2skill.AIAnalyzer') as MockAnalyzer:
                with patch('scripts.pdf2skill.SkillGenerator') as MockGenerator:
                    # Setup parser mock
                    parser_instance = MockParser.return_value
                    parser_instance.parse.return_value = mock_parsed_doc

                    # Setup analyzer mock
                    analyzer_instance = MockAnalyzer.return_value
                    analyzer_instance.analyze_document.return_value = mock_analysis

                    # Setup generator mock
                    generator_instance = MockGenerator.return_value
                    generator_instance.generate.return_value = expected_skill
                    generator_instance.write_skill.return_value = tmp_path / 'output'
                    generator_instance.determine_structure.return_value = 'minimal'

                    # Process the document
                    result = process_document(
                        input_path=test_pdf,
                        output_dir=tmp_path / 'output',
                        config=Mock(
                            llm=Mock(provider='anthropic', model='claude-sonnet-4-6'),
                            structure='auto'
                        ),
                        skill_name='test-skill',
                        verbose=False
                    )

                    # Verify the result
                    assert result is not None
                    assert result.name == 'test-skill'
                    parser_instance.parse.assert_called_once()
                    analyzer_instance.analyze_document.assert_called_once()


class TestMain:
    """Tests for main function."""

    def test_main_success(self, tmp_path):
        """Test successful main execution."""
        from scripts.pdf2skill import main

        # Create a minimal test PDF
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\ntest\n%%EOF")

        # Create mock for the entire processing pipeline
        mock_skill = Mock(
            name='test',
            files={'SKILL.md': 'content'},
            metadata={}
        )

        with patch('scripts.pdf2skill.process_document') as mock_process:
            with patch('sys.argv', ['pdf2skill', str(test_pdf), '-o', str(tmp_path)]):
                mock_process.return_value = mock_skill
                result = main()
                assert result == 0
                mock_process.assert_called_once()

    def test_main_file_not_found(self):
        """Test main with non-existent file."""
        from scripts.pdf2skill import main

        with patch('sys.argv', ['pdf2skill', '/nonexistent/file.pdf']):
            result = main()
            assert result == 1

    def test_main_with_verbose(self, tmp_path):
        """Test main with verbose output."""
        from scripts.pdf2skill import main

        # Create a minimal test PDF
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\ntest\n%%EOF")

        mock_skill = Mock(
            name='test',
            files={'SKILL.md': 'content'},
            metadata={}
        )

        with patch('scripts.pdf2skill.process_document') as mock_process:
            with patch('sys.argv', ['pdf2skill', str(test_pdf), '-v', '-o', str(tmp_path)]):
                mock_process.return_value = mock_skill
                result = main()
                assert result == 0
                # Verify verbose was passed
                call_kwargs = mock_process.call_args[1]
                assert call_kwargs['verbose'] is True


class TestIntegration:
    """Integration tests for the complete pipeline."""

    @pytest.mark.integration
    def test_full_pipeline_minimal(self, tmp_path):
        """Test full pipeline with minimal structure output."""
        # This test requires actual modules to work together
        # It's marked as integration test and may be skipped in unit test runs
        pytest.skip("Integration test - requires full module setup")

    @pytest.mark.integration
    def test_full_pipeline_standard(self, tmp_path):
        """Test full pipeline with standard structure output."""
        pytest.skip("Integration test - requires full module setup")

    @pytest.mark.integration
    def test_full_pipeline_complete(self, tmp_path):
        """Test full pipeline with complete structure output."""
        pytest.skip("Integration test - requires full module setup")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_epub_file_extension(self, tmp_path):
        """Test that EPUB files are accepted."""
        from scripts.pdf2skill import process_document
        from scripts.skill_generator import GeneratedSkill

        # Create a minimal EPUB-like file
        test_epub = tmp_path / "test.epub"
        test_epub.write_bytes(b"PK\x03\x04" + b"\x00" * 20)  # ZIP header

        expected_skill = GeneratedSkill(
            name='test',
            files={'SKILL.md': 'content'},
            metadata={}
        )

        with patch('scripts.pdf2skill.DocumentParser') as MockParser:
            with patch('scripts.pdf2skill.AIAnalyzer') as MockAnalyzer:
                with patch('scripts.pdf2skill.SkillGenerator') as MockGenerator:
                    parser_instance = MockParser.return_value
                    parser_instance.parse.return_value = Mock(
                        file_path=test_epub,
                        file_type='epub',
                        text_content='content',
                        sections=[],
                        code_blocks=[],
                        tables=[],
                        metadata={}
                    )

                    analyzer_instance = MockAnalyzer.return_value
                    analyzer_instance.analyze_document.return_value = Mock(
                        document_type='book',
                        audience='general',
                        topics=[],
                        complexity='medium',
                        workflows=[],
                        validation_rules=[]
                    )

                    generator_instance = MockGenerator.return_value
                    generator_instance.generate.return_value = expected_skill
                    generator_instance.write_skill.return_value = tmp_path
                    generator_instance.determine_structure.return_value = 'standard'

                    config = Mock(
                        llm=Mock(provider='anthropic', model='claude-sonnet-4-6'),
                        structure='standard'
                    )

                    result = process_document(
                        input_path=test_epub,
                        output_dir=tmp_path,
                        config=config,
                        verbose=False
                    )

                    assert result is not None
                    assert result.name == 'test'

    def test_derive_skill_name_from_filename(self, tmp_path):
        """Test that skill name is derived from filename when not provided."""
        from scripts.pdf2skill import process_document

        test_pdf = tmp_path / "My_Book_Title.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\ntest\n%%EOF")

        mock_skill = Mock(name='My_Book_Title', files={}, metadata={})

        with patch('scripts.pdf2skill.DocumentParser') as MockParser:
            with patch('scripts.pdf2skill.AIAnalyzer') as MockAnalyzer:
                with patch('scripts.pdf2skill.SkillGenerator') as MockGenerator:
                    parser_instance = MockParser.return_value
                    parser_instance.parse.return_value = Mock(
                        file_path=test_pdf,
                        file_type='pdf',
                        text_content='content',
                        sections=[],
                        code_blocks=[],
                        tables=[],
                        metadata={}
                    )

                    analyzer_instance = MockAnalyzer.return_value
                    analyzer_instance.analyze_document.return_value = Mock(
                        document_type='book',
                        audience='general',
                        topics=[],
                        complexity='simple',
                        workflows=[],
                        validation_rules=[]
                    )

                    generator_instance = MockGenerator.return_value
                    generator_instance.generate.return_value = mock_skill
                    generator_instance.write_skill.return_value = tmp_path
                    generator_instance.determine_structure.return_value = 'minimal'

                    config = Mock(
                        llm=Mock(provider='anthropic', model='claude-sonnet-4-6'),
                        structure='auto'
                    )

                    # Call without skill_name
                    result = process_document(
                        input_path=test_pdf,
                        output_dir=tmp_path,
                        config=config,
                        verbose=False
                    )

                    # Check that generate was called with the derived name
                    call_args = generator_instance.generate.call_args
                    assert call_args[1]['skill_name'] == 'My_Book_Title'