"""
Kiro Packaging Smoke Tests

Verifies the .kiro/ directory is correctly structured for Kiro auto-discovery
of the Solr-to-OpenSearch migration advisor skill.

These tests validate packaging — not skill logic. They ensure that opening
the AIAdvisor/ folder in Kiro will result in the skill being found, steering
context being loaded, and the hook being registered.
"""

import json
import os
from pathlib import Path

import pytest

# AIAdvisor/ root — four levels up from this test file
ADVISOR_ROOT = Path(__file__).resolve().parent.parent.parent.parent
KIRO_DIR = ADVISOR_ROOT / ".kiro"
SKILL_DIR = ADVISOR_ROOT / "skills" / "solr-opensearch-migration-advisor"


class TestKiroDirectoryStructure:
    """Verify .kiro/ has the required subdirectories."""

    def test_kiro_dir_exists(self):
        assert KIRO_DIR.is_dir(), f".kiro directory missing at {KIRO_DIR}"

    @pytest.mark.parametrize("subdir", ["steering", "skills", "hooks", "settings"])
    def test_required_subdirs_exist(self, subdir):
        assert (KIRO_DIR / subdir).is_dir(), f".kiro/{subdir}/ missing"


class TestSkillSymlink:
    """Verify the skill symlink resolves correctly."""

    def test_symlink_exists(self):
        link = KIRO_DIR / "skills" / "solr-to-opensearch"
        assert link.is_symlink(), ".kiro/skills/solr-to-opensearch is not a symlink"

    def test_symlink_resolves_to_skill_dir(self):
        link = KIRO_DIR / "skills" / "solr-to-opensearch"
        target = link.resolve()
        assert target.is_dir(), f"symlink target {target} is not a directory"
        assert (target / "SKILL.md").is_file(), f"SKILL.md not found in {target}"


class TestSkillMdFrontmatter:
    """Verify SKILL.md has the required Agent Skills frontmatter."""

    @pytest.fixture
    def skill_md_content(self):
        return (SKILL_DIR / "SKILL.md").read_text()

    def test_has_yaml_frontmatter(self, skill_md_content):
        assert skill_md_content.startswith("---"), "SKILL.md must start with YAML frontmatter (---)"
        # Find closing delimiter
        second_delim = skill_md_content.index("---", 3)
        assert second_delim > 3, "SKILL.md frontmatter not closed"

    @pytest.mark.parametrize("field", ["name", "displayName", "description", "keywords"])
    def test_required_frontmatter_fields(self, skill_md_content, field):
        # Extract frontmatter block
        end = skill_md_content.index("---", 3)
        frontmatter = skill_md_content[3:end]
        assert f"\n{field}:" in frontmatter or frontmatter.startswith(f"{field}:"), \
            f"SKILL.md frontmatter missing '{field}' field"


class TestKiroSteering:
    """Verify .kiro/steering/ files exist and have inclusion frontmatter."""

    @pytest.mark.parametrize("filename", ["product.md", "tech.md", "structure.md"])
    def test_steering_file_exists(self, filename):
        assert (KIRO_DIR / "steering" / filename).is_file(), \
            f".kiro/steering/{filename} not found"

    @pytest.mark.parametrize("filename", ["product.md", "tech.md", "structure.md"])
    def test_steering_has_inclusion_frontmatter(self, filename):
        content = (KIRO_DIR / "steering" / filename).read_text()
        assert "inclusion:" in content, \
            f".kiro/steering/{filename} missing 'inclusion:' frontmatter"


class TestMcpConfig:
    """Verify .kiro/settings/mcp.json is valid and references the skill."""

    @pytest.fixture
    def mcp_config(self):
        mcp_path = KIRO_DIR / "settings" / "mcp.json"
        assert mcp_path.is_file(), "mcp.json not found"
        return json.loads(mcp_path.read_text())

    def test_mcp_json_is_valid(self, mcp_config):
        assert isinstance(mcp_config, dict)

    def test_mcp_references_skill_server(self, mcp_config):
        servers = mcp_config.get("mcpServers", {})
        assert "solr-to-opensearch" in servers, \
            "mcp.json missing 'solr-to-opensearch' server entry"

    def test_mcp_skill_server_has_command(self, mcp_config):
        server = mcp_config["mcpServers"]["solr-to-opensearch"]
        assert "command" in server, "solr-to-opensearch server missing 'command'"

    def test_mcp_script_path_exists(self, mcp_config):
        """Guard against stale paths after directory restructures."""
        server = mcp_config["mcpServers"]["solr-to-opensearch"]
        script_path = server["args"][0]
        # Kiro resolves relative paths from the project root (ADVISOR_ROOT)
        resolved = ADVISOR_ROOT / script_path
        assert resolved.is_file(), \
            f"MCP server script not found at {resolved} (from mcp.json args: {script_path})"


class TestKiroHook:
    """Verify the schema-assist hook is valid."""

    @pytest.fixture
    def hook_config(self):
        hook_path = KIRO_DIR / "hooks" / "schema-assist.kiro.hook"
        assert hook_path.is_file(), "schema-assist.kiro.hook not found"
        return json.loads(hook_path.read_text())

    def test_hook_is_valid_json(self, hook_config):
        assert isinstance(hook_config, dict)

    def test_hook_has_when_clause(self, hook_config):
        assert "when" in hook_config, "hook missing 'when' clause"
        assert "type" in hook_config["when"], "hook 'when' missing 'type'"
        assert "patterns" in hook_config["when"], "hook 'when' missing 'patterns'"

    def test_hook_has_then_clause(self, hook_config):
        assert "then" in hook_config, "hook missing 'then' clause"
        assert "type" in hook_config["then"], "hook 'then' missing 'type'"

    def test_hook_triggers_on_schema_files(self, hook_config):
        patterns = hook_config["when"]["patterns"]
        assert any("schema" in p for p in patterns), \
            f"hook patterns don't match schema files: {patterns}"


class TestSkillSteeringDocs:
    """Verify the skill's own steering documents are present."""

    def test_steering_directory_exists(self):
        """Verify the steering directory exists. Individual file content is out of scope."""
        assert (SKILL_DIR / "steering").is_dir(), "skill steering/ directory not found"

    def test_steering_directory_not_empty(self):
        """At least one steering doc must be present."""
        files = list((SKILL_DIR / "steering").glob("*.md"))
        assert len(files) > 0, "steering/ directory has no .md files"


class TestCoreScripts:
    """Verify core Python scripts exist and are importable."""

    REQUIRED_SCRIPTS = [
        "skill.py",
        "schema_converter.py",
        "query_converter.py",
        "report.py",
        "storage.py",
    ]

    @pytest.mark.parametrize("filename", REQUIRED_SCRIPTS)
    def test_script_exists(self, filename):
        assert (SKILL_DIR / "scripts" / filename).is_file(), \
            f"scripts/{filename} not found"
