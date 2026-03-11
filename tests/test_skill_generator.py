# tests/test_skill_generator.py
import pytest
from pathlib import Path
from scripts.skill_generator import SkillGenerator, GeneratedSkill
from scripts.ai_analyzer import Workflow, WorkflowStep, QAPair


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
            WorkflowStep(
                name="Install", description="Run installer", commands=["pip install x"]
            )
        ],
    )

    skill = generator.generate(
        skill_name="test-skill",
        workflows=[workflow],
        code_assessment={
            "complexity": "simple",
            "block_count": 2,
            "languages": ["bash"],
        },
        structure="minimal",
        source_file="test.pdf",
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
            WorkflowStep(
                name="Install", description="Run installer", commands=["npm install"]
            ),
        ],
    )

    skill = generator.generate(
        skill_name="my-tool",
        workflows=[workflow],
        code_assessment={
            "complexity": "medium",
            "block_count": 5,
            "languages": ["bash", "javascript"],
        },
        structure="standard",
        source_file="guide.pdf",
    )

    assert skill.name == "my-tool"
    assert "scripts/validate.sh" in skill.files or "scripts/setup.sh" in skill.files


def test_write_skill(tmp_path):
    """Test writing skill files to disk."""
    generator = SkillGenerator()

    workflow = Workflow(
        name="Basic",
        trigger="Always",
        steps=[WorkflowStep(name="Step1", description="First step")],
    )

    skill = generator.generate(
        skill_name="output-skill",
        workflows=[workflow],
        code_assessment={"complexity": "simple"},
        structure="minimal",
        source_file="input.pdf",
    )

    output_dir = tmp_path / "output-skill"
    generator.write_skill(skill, output_dir)

    assert output_dir.exists()
    assert (output_dir / "SKILL.md").exists()


def test_generate_qa_skill_minimal():
    """Test generating a Q&A skill in minimal structure."""
    generator = SkillGenerator()

    qa_pairs = [
        QAPair(
            question="How do I install?",
            answer="Run pip install",
            category="setup",
            source_section="Installation",
        ),
        QAPair(
            question="What is the config format?",
            answer="YAML format",
            category="configuration",
            source_section="Configuration",
        ),
    ]

    skill = generator.generate(
        skill_name="qa-test-skill",
        workflows=[],
        code_assessment={"complexity": "simple", "block_count": 0, "languages": []},
        structure="minimal",
        source_file="faq.pdf",
        qa_pairs=qa_pairs,
        mode="qa",
    )

    assert skill.name == "qa-test-skill"
    assert "SKILL.md" in skill.files
    assert skill.metadata["mode"] == "qa"
    assert skill.metadata["qa_count"] == 2
    assert "setup" in skill.metadata["qa_categories"]
    assert "configuration" in skill.metadata["qa_categories"]
    # Check that Q&A content is in the SKILL.md
    assert "How do I install?" in skill.files["SKILL.md"]
    assert "Run pip install" in skill.files["SKILL.md"]


def test_generate_qa_skill_standard():
    """Test generating a Q&A skill in standard structure."""
    generator = SkillGenerator()

    qa_pairs = [
        QAPair(question="How do I install?", answer="Run pip install", category="setup")
    ]

    skill = generator.generate(
        skill_name="qa-standard-skill",
        workflows=[],
        code_assessment={"complexity": "medium", "block_count": 0, "languages": []},
        structure="standard",
        source_file="guide.pdf",
        qa_pairs=qa_pairs,
        mode="qa",
    )

    assert skill.name == "qa-standard-skill"
    assert "SKILL.md" in skill.files
    assert "scripts/search_qa.sh" in skill.files
    assert "scripts/export_qa.sh" in skill.files
    assert "references/qa_index.md" in skill.files
    assert "references/categories.md" in skill.files


def test_generate_qa_skill_complete():
    """Test generating a Q&A skill in complete structure."""
    generator = SkillGenerator()

    qa_pairs = [
        QAPair(question="How do I install?", answer="Run pip install", category="setup")
    ]

    skill = generator.generate(
        skill_name="qa-complete-skill",
        workflows=[],
        code_assessment={"complexity": "complex", "block_count": 0, "languages": []},
        structure="complete",
        source_file="complex-guide.pdf",
        qa_pairs=qa_pairs,
        mode="qa",
    )

    assert skill.name == "qa-complete-skill"
    assert "SKILL.md" in skill.files
    assert "scripts/search_qa.sh" in skill.files
    assert "scripts/export_qa.sh" in skill.files
    assert "references/qa_index.md" in skill.files
    assert "references/categories.md" in skill.files
    assert "templates/qa_template.md" in skill.files
    assert "templates/qa_template.json" in skill.files
