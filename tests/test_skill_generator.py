# tests/test_skill_generator.py
import pytest
from pathlib import Path
from scripts.skill_generator import SkillGenerator, GeneratedSkill
from scripts.ai_analyzer import Workflow, WorkflowStep


def test_determine_structure():
    """Test structure determination based on content."""
    generator = SkillGenerator()

    # Minimal
    assert generator.determine_structure(page_count=10, code_blocks=2) == "minimal"

    # Standard
    assert generator.determine_structure(page_count=50, code_blocks=10) == "standard"

    # Complete
    assert generator.determine_structure(page_count=150, code_blocks=30) == "complete"


def test_generate_skill_minimal():
    """Test generating a minimal skill."""
    generator = SkillGenerator()

    workflow = Workflow(
        name="Setup",
        trigger="When starting",
        steps=[
            WorkflowStep(name="Install", description="Run installer", commands=["pip install x"])
        ]
    )

    skill = generator.generate(
        skill_name="test-skill",
        workflows=[workflow],
        code_assessment={"complexity": "simple", "block_count": 2, "languages": ["bash"]},
        structure="minimal",
        source_file="test.pdf"
    )

    assert skill.name == "test-skill"
    assert len(skill.files) >= 1
    assert "SKILL.md" in skill.files


def test_generate_skill_standard():
    """Test generating a standard skill."""
    generator = SkillGenerator()

    workflow = Workflow(
        name="Installation",
        trigger="When installing the tool",
        steps=[
            WorkflowStep(name="Download", description="Download package"),
            WorkflowStep(name="Install", description="Run installer", commands=["npm install"])
        ]
    )

    skill = generator.generate(
        skill_name="my-tool",
        workflows=[workflow],
        code_assessment={"complexity": "medium", "block_count": 5, "languages": ["bash", "javascript"]},
        structure="standard",
        source_file="guide.pdf"
    )

    assert skill.name == "my-tool"
    assert "scripts/validate.sh" in skill.files or "scripts/setup.sh" in skill.files


def test_write_skill(tmp_path):
    """Test writing skill files to disk."""
    generator = SkillGenerator()

    workflow = Workflow(
        name="Basic",
        trigger="Always",
        steps=[WorkflowStep(name="Step1", description="First step")]
    )

    skill = generator.generate(
        skill_name="output-skill",
        workflows=[workflow],
        code_assessment={"complexity": "simple"},
        structure="minimal",
        source_file="input.pdf"
    )

    output_dir = tmp_path / "output-skill"
    generator.write_skill(skill, output_dir)

    assert output_dir.exists()
    assert (output_dir / "SKILL.md").exists()