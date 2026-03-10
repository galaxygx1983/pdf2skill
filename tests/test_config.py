# tests/test_config.py
import os
import pytest
import yaml
from pathlib import Path
from scripts.config import Config, LLMConfig


def test_default_config():
    """Test default configuration values."""
    config = Config()
    assert config.llm.provider == "anthropic"
    assert config.llm.model == "claude-sonnet-4-6"
    assert config.output_dir == Path(".")


def test_config_from_env():
    """Test configuration from environment variables."""
    os.environ["PDF2SKILL_LLM_PROVIDER"] = "openai"
    os.environ["PDF2SKILL_LLM_MODEL"] = "gpt-4o"
    config = Config.from_env()
    assert config.llm.provider == "openai"
    assert config.llm.model == "gpt-4o"
    del os.environ["PDF2SKILL_LLM_PROVIDER"]
    del os.environ["PDF2SKILL_LLM_MODEL"]


def test_config_from_file(tmp_path):
    """Test configuration from YAML file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
llm:
  provider: openai-compatible
  base_url: https://api.example.com/v1
  model: custom-model
output_dir: ./output
""")
    config = Config.from_file(config_file)
    assert config.llm.provider == "openai-compatible"
    assert config.llm.model == "custom-model"
    assert config.output_dir == Path("./output")


def test_llm_config_api_key():
    """Test API key handling."""
    os.environ["PDF2SKILL_LLM_API_KEY"] = "test-key"
    llm_config = LLMConfig(provider="anthropic", model="claude-sonnet-4-6")
    assert llm_config.api_key == "test-key"
    del os.environ["PDF2SKILL_LLM_API_KEY"]


def test_merge_config():
    """Test merging two configurations."""
    config1 = Config(
        llm=LLMConfig(provider="anthropic", model="claude-sonnet-4-6"),
        output_dir=Path("./default"),
        structure="standard",
    )
    config2 = Config(
        llm=LLMConfig(provider="openai", model="gpt-4o", base_url="https://api.openai.com"),
        output_dir=Path("./custom"),
        structure="complete",
    )

    merged = config1.merge(config2)

    # Other config takes precedence for non-default values
    assert merged.llm.provider == "openai"
    assert merged.llm.model == "gpt-4o"
    assert merged.llm.base_url == "https://api.openai.com"
    assert merged.output_dir == Path("./custom")
    assert merged.structure == "complete"


def test_merge_config_with_defaults():
    """Test merging when other config has default values."""
    config1 = Config(
        llm=LLMConfig(provider="openai", model="gpt-4o"),
        output_dir=Path("./existing"),
        structure="complete",
    )
    # config2 has default values
    config2 = Config()

    merged = config1.merge(config2)

    # config1 values should be preserved when config2 has defaults
    assert merged.llm.provider == "openai"
    assert merged.llm.model == "gpt-4o"
    assert merged.output_dir == Path("./existing")
    assert merged.structure == "complete"


def test_config_from_nonexistent_file():
    """Test configuration from non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError) as exc_info:
        Config.from_file(Path("/nonexistent/config.yaml"))
    assert "Configuration file not found" in str(exc_info.value)


def test_config_from_malformed_yaml(tmp_path):
    """Test configuration from malformed YAML file raises YAMLError."""
    config_file = tmp_path / "malformed.yaml"
    # Use unclosed bracket which causes a YAMLError
    config_file.write_text("llm: [\n  provider: test\n")
    with pytest.raises(yaml.YAMLError) as exc_info:
        Config.from_file(config_file)
    assert "Malformed YAML" in str(exc_info.value)


def test_config_from_empty_file(tmp_path):
    """Test configuration from empty YAML file uses defaults."""
    import yaml

    config_file = tmp_path / "empty.yaml"
    config_file.write_text("")

    config = Config.from_file(config_file)

    # Should use default values
    assert config.llm.provider == "anthropic"
    assert config.llm.model == "claude-sonnet-4-6"
    assert config.output_dir == Path(".")
    assert config.structure == "auto"