"""
Multi-IDE Packaging Tests

Verifies that packaging stubs exist for all supported AI IDEs/tools,
ensuring the skill is discoverable regardless of which IDE a user opens
the AIAdvisor/ folder with.
"""

from pathlib import Path

import pytest

ADVISOR_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class TestIdePackagingStubs:
    """Verify each IDE has a configuration/instructions file."""

    IDE_CONFIGS = [
        (".kiro/skills/solr-to-opensearch", "Kiro"),
        ("CLAUDE.md", "Claude Code"),
        (".cursorrules", "Cursor"),
        (".github/copilot-instructions.md", "GitHub Copilot"),
        ("GEMINI.md", "Gemini"),
    ]

    @pytest.mark.parametrize("path,ide_name", IDE_CONFIGS, ids=lambda x: x if isinstance(x, str) else None)
    def test_ide_config_exists(self, path, ide_name):
        full_path = ADVISOR_ROOT / path
        assert full_path.exists(), \
            f"{ide_name} config not found at AIAdvisor/{path}"

    @pytest.mark.parametrize("path,ide_name", [
        ("CLAUDE.md", "Claude Code"),
        (".cursorrules", "Cursor"),
        (".github/copilot-instructions.md", "GitHub Copilot"),
        ("GEMINI.md", "Gemini"),
    ])
    def test_ide_config_references_skill(self, path, ide_name):
        """Each IDE config should point users to the SKILL.md location."""
        content = (ADVISOR_ROOT / path).read_text()
        assert "SKILL.md" in content or "skill" in content.lower(), \
            f"{ide_name} config at {path} doesn't reference the skill"

    @pytest.mark.parametrize("path,ide_name", [
        ("CLAUDE.md", "Claude Code"),
        (".cursorrules", "Cursor"),
        (".github/copilot-instructions.md", "GitHub Copilot"),
        ("GEMINI.md", "Gemini"),
    ])
    def test_ide_config_mentions_accuracy(self, path, ide_name):
        """Each IDE config should mention the accuracy-first rule."""
        content = (ADVISOR_ROOT / path).read_text().lower()
        assert "accuracy" in content, \
            f"{ide_name} config at {path} doesn't mention accuracy rule"
