"""Configuration management for pdf2skill."""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import yaml


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    base_url: Optional[str] = None
    api_key: Optional[str] = None

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.environ.get("PDF2SKILL_LLM_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")


@dataclass
class Config:
    """Main configuration for pdf2skill."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    output_dir: Path = Path(".")
    structure: str = "auto"  # minimal, standard, complete, auto

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        llm_config = LLMConfig(
            provider=os.environ.get("PDF2SKILL_LLM_PROVIDER", "anthropic"),
            model=os.environ.get("PDF2SKILL_LLM_MODEL", "claude-sonnet-4-6"),
            base_url=os.environ.get("PDF2SKILL_LLM_BASE_URL"),
        )
        output_dir = Path(os.environ.get("PDF2SKILL_OUTPUT_DIR", "."))
        structure = os.environ.get("PDF2SKILL_STRUCTURE", "auto")
        return cls(llm=llm_config, output_dir=output_dir, structure=structure)

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """Load configuration from YAML file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            yaml.YAMLError: If the YAML file is malformed.
        """
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Malformed YAML in configuration file {path}: {e}") from e

        # Handle empty YAML file
        if data is None:
            data = {}

        llm_data = data.get("llm", {})
        llm_config = LLMConfig(
            provider=llm_data.get("provider", "anthropic"),
            model=llm_data.get("model", "claude-sonnet-4-6"),
            base_url=llm_data.get("base_url"),
        )

        return cls(
            llm=llm_config,
            output_dir=Path(data.get("output_dir", ".")),
            structure=data.get("structure", "auto"),
        )

    def merge(self, other: "Config") -> "Config":
        """Merge two configurations, with other taking precedence."""
        return Config(
            llm=LLMConfig(
                provider=other.llm.provider if other.llm.provider != "anthropic" else self.llm.provider,
                model=other.llm.model if other.llm.model != "claude-sonnet-4-6" else self.llm.model,
                base_url=other.llm.base_url or self.llm.base_url,
                api_key=other.llm.api_key or self.llm.api_key,
            ),
            output_dir=other.output_dir if other.output_dir != Path(".") else self.output_dir,
            structure=other.structure if other.structure != "auto" else self.structure,
        )