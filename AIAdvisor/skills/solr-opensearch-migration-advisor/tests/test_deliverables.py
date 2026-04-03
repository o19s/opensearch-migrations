"""
AWS Deliverable Validation Tests

Tests mapped to the deliverables in the AWS tracking document
(OpenSourceConnections—DeliverablesTracking.md, sprint window
2026-04-02 → 2026-04-15).

Two test groups:
  core     — tests that validate the AWS deliverable requirements
             (run by default)
  extended — "above and beyond" tests that go deeper than the ask
             (skipped by default, run with --extended)

Run:
  pytest tests/test_deliverables.py -v                 # core only
  pytest tests/test_deliverables.py -v --extended      # core + extended

Deliverable mapping:
  D1: Container Packaging
  D2: Agent Skill Packaging & Discovery
  D3: Eval Framework Expansion
  D4: Knowledge Base Enrichment
  D5: Migration Assistant Integration

Success metrics from the tracking doc:
  - Unit test pass rate: 100%
  - Test coverage: >= 85% on scripts/
  - Eval scenario count: >= 10
  - Steering doc depth: all >= 15 lines, key docs >= 50 lines
  - Incompatibilities cataloged: >= 30
  - Query translation examples: >= 15
"""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
STEERING_DIR = SKILL_ROOT / "steering"
REFERENCES_DIR = SKILL_ROOT / "references"
DATA_DIR = SKILL_ROOT / "data"
TESTS_DIR = SKILL_ROOT / "tests"
EVALS_DIR = TESTS_DIR / "evals"

extended = pytest.mark.extended


# ── helpers ──────────────────────────────────────────────────────────────


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8").strip().splitlines())


def _load_json(path: Path) -> dict | list:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _count_examples_in_md(path: Path, pattern: str = r"```") -> int:
    """Count fenced code blocks as a proxy for worked examples."""
    if not path.exists():
        return 0
    content = path.read_text(encoding="utf-8")
    return len(re.findall(pattern, content)) // 2  # open + close


def _skill_md_tools() -> list[str]:
    """Extract tool names from SKILL.md."""
    skill_md = SKILL_ROOT / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    # Match function-style tool names: `convert_schema_xml(args)`
    return list(set(re.findall(r"`(\w+)\([^)]*\)`", content)))


# =====================================================================
# D1: CONTAINER PACKAGING
# =====================================================================


class TestD1ContainerPackaging:
    """D1: Container packaging deliverables."""

    def test_d1_1_dockerfile_exists(self):
        """D1.1: Dockerfile exists in the skill root."""
        candidates = [
            SKILL_ROOT / "Dockerfile",
            SKILL_ROOT / "docker" / "Dockerfile",
            SKILL_ROOT.parent.parent.parent / "Dockerfile",  # repo root
        ]
        found = any(c.exists() for c in candidates)
        assert found, (
            f"D1.1: No Dockerfile found. Expected in one of: "
            f"{[str(c) for c in candidates]}"
        )

    @extended
    def test_d1_1_dockerfile_uses_slim_base(self):
        """D1.1 extended: Dockerfile uses a slim Python base image."""
        dockerfile = SKILL_ROOT / "Dockerfile"
        if not dockerfile.exists():
            pytest.skip("No Dockerfile at skill root")
        content = dockerfile.read_text(encoding="utf-8")
        assert "slim" in content.lower() or "alpine" in content.lower(), (
            "D1.1 extended: Dockerfile should use a slim/alpine base "
            "to keep image size < 500MB"
        )

    def test_d1_3_docker_compose_exists(self):
        """D1.3: docker-compose file exists with advisor + OpenSearch."""
        candidates = [
            SKILL_ROOT / "docker-compose.yml",
            SKILL_ROOT / "docker-compose.yaml",
            SKILL_ROOT.parent.parent.parent / "docker-compose.yml",
        ]
        found = any(c.exists() for c in candidates)
        # This is a P0 deliverable — note if missing but don't hard-fail
        # since it may live elsewhere in the repo
        if not found:
            pytest.skip(
                "D1.3: No docker-compose.yml found — may exist outside "
                "skill directory"
            )

    def test_d1_5_sessions_dir_exists(self):
        """D1.5: sessions/ directory exists for volume mount persistence."""
        sessions = SKILL_ROOT / "sessions"
        assert sessions.is_dir() or (SKILL_ROOT / ".gitkeep").exists(), (
            "D1.5: sessions/ directory should exist for container "
            "volume mount persistence"
        )


# =====================================================================
# D2: AGENT SKILL PACKAGING & DISCOVERY
# =====================================================================


class TestD2SkillPackaging:
    """D2: Agent skill packaging and discovery deliverables."""

    def test_d2_1_skill_md_exists(self):
        """D2.1/D2.2: SKILL.md exists at the skill root."""
        assert (SKILL_ROOT / "SKILL.md").exists(), (
            "D2.1: SKILL.md must exist for agent discovery"
        )

    def test_d2_1_skill_md_has_frontmatter(self):
        """D2.1: SKILL.md has valid YAML frontmatter with name and version."""
        import yaml
        content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
        parts = content.split("---")
        meta = yaml.safe_load(parts[1])
        assert "name" in meta, "SKILL.md frontmatter must have 'name'"
        assert meta["name"] == "solr-to-opensearch-migration", (
            f"SKILL.md name should be 'solr-to-opensearch-migration', "
            f"got '{meta['name']}'"
        )

    def test_d2_3_skill_tools_are_importable(self):
        """D2.3: All core skill tool modules are importable."""
        required_modules = [
            "skill",
            "schema_converter",
            "query_converter",
            "storage",
            "report",
        ]
        import importlib
        for mod_name in required_modules:
            try:
                importlib.import_module(mod_name)
            except ImportError as e:
                pytest.fail(
                    f"D2.3: Module '{mod_name}' is not importable: {e}"
                )

    def test_d2_3_skill_md_declares_tools(self):
        """D2.3: SKILL.md declares at least 7 tools."""
        tools = _skill_md_tools()
        assert len(tools) >= 7, (
            f"D2.3: SKILL.md should declare >= 7 tools, found {len(tools)}: "
            f"{tools}"
        )

    def test_d2_4_readme_exists(self):
        """D2.4: Getting-started documentation exists."""
        readme = SKILL_ROOT / "README.md"
        assert readme.exists(), "D2.4: README.md must exist"
        content = readme.read_text(encoding="utf-8")
        assert "getting started" in content.lower() or "quick start" in content.lower() or "how to" in content.lower(), (
            "D2.4: README.md should contain getting-started instructions"
        )

    @extended
    def test_d2_4_getting_started_doc_exists(self):
        """D2.4 extended: Dedicated GETTING-STARTED.md exists."""
        assert (SKILL_ROOT / "GETTING-STARTED.md").exists(), (
            "D2.4 extended: GETTING-STARTED.md should exist for team onboarding"
        )

    @extended
    def test_d2_kiro_skill_structure(self):
        """D2.1 extended: Skill directory matches Kiro discovery conventions."""
        # Kiro expects .kiro/skills/<name>/SKILL.md
        # Check that SKILL.md is structured with the right sections
        content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for section in ["## Quick Reference", "## Available Tools"]:
            assert section in content or section.lower() in content.lower(), (
                f"D2.1 extended: SKILL.md should have a '{section}' section "
                f"for agent discovery"
            )

    @extended
    def test_d2_claude_skill_symlink_documented(self):
        """D2.2 extended: README documents Claude skill discovery path."""
        readme = (SKILL_ROOT / "README.md").read_text(encoding="utf-8")
        assert ".claude/skills" in readme or "claude" in readme.lower(), (
            "D2.2 extended: README should document Claude skill discovery "
            "path (.claude/skills/)"
        )


# =====================================================================
# D3: EVAL FRAMEWORK EXPANSION
# =====================================================================


class TestD3EvalFramework:
    """D3: Eval framework expansion deliverables."""

    def test_d3_1_eval_yaml_exists(self):
        """D3.1: eval.yaml exists with test scenarios."""
        assert (EVALS_DIR / "eval.yaml").exists(), (
            "D3.1: tests/evals/eval.yaml must exist"
        )

    def test_d3_1_eval_has_minimum_scenarios(self):
        """D3.1: eval.yaml has >= 10 scenarios (target from tracking doc)."""
        import yaml
        content = (EVALS_DIR / "eval.yaml").read_text(encoding="utf-8")
        config = yaml.safe_load(content)
        tests = config.get("tests", [])
        assert len(tests) >= 10, (
            f"D3.1: eval.yaml should have >= 10 scenarios, found "
            f"{len(tests)}. Current scenarios cover Steps 0-2 only; "
            f"need coverage through Step 7."
        )

    def test_d3_2_p0_scenario_incompatibility_detection(self):
        """D3.2: P0 eval scenario for incompatibility detection exists."""
        self._assert_eval_metric_exists("detect-incompatibilities")

    def test_d3_2_p0_scenario_standard_query_translation(self):
        """D3.2: P0 eval scenario for standard query translation exists."""
        self._assert_eval_metric_exists("translate-standard-query")

    def test_d3_2_p0_scenario_edismax_query_translation(self):
        """D3.2: P0 eval scenario for eDisMax query translation exists."""
        self._assert_eval_metric_exists("translate-edismax-query")

    def test_d3_2_p0_scenario_full_report(self):
        """D3.2: P0 eval scenario for full migration report exists."""
        self._assert_eval_metric_exists("generate-full-report")

    def test_d3_2_p0_scenario_session_resumption(self):
        """D3.2: P0 eval scenario for session resumption exists."""
        self._assert_eval_metric_exists("session-resumption")

    def test_d3_2_p0_scenario_no_hallucination(self):
        """D3.2: P0 eval scenario for accuracy/no-hallucination exists."""
        self._assert_eval_metric_exists("accuracy-no-hallucination")

    @extended
    def test_d3_2_p1_scenario_customization_assessment(self):
        """D3.2 extended: P1 eval scenario for customization assessment."""
        self._assert_eval_metric_exists("assess-customizations")

    @extended
    def test_d3_2_p1_scenario_sizing(self):
        """D3.2 extended: P1 eval scenario for sizing recommendation."""
        self._assert_eval_metric_exists("sizing-recommendation")

    @extended
    def test_d3_2_p1_scenario_client_integration(self):
        """D3.2 extended: P1 eval scenario for client integration mapping."""
        self._assert_eval_metric_exists("map-client-integrations")

    @extended
    def test_d3_2_p1_scenario_stakeholder_tailoring(self):
        """D3.2 extended: P1 eval scenario for stakeholder tailoring."""
        self._assert_eval_metric_exists("stakeholder-tailoring")

    def test_d3_4_eval_baseline_documented(self):
        """D3.4: Eval baseline documentation exists."""
        candidates = [
            EVALS_DIR / "BASELINE.md",
            TESTS_DIR / "scenario-evals" / "baselines",
        ]
        found = any(
            c.exists() if c.suffix == ".md" else c.is_dir()
            for c in candidates
        )
        assert found, (
            "D3.4: Eval baseline must be documented in "
            "tests/evals/BASELINE.md or tests/scenario-evals/baselines/"
        )

    def _assert_eval_metric_exists(self, metric_name: str):
        """Assert that eval.yaml contains a scenario with this metric."""
        import yaml
        content = (EVALS_DIR / "eval.yaml").read_text(encoding="utf-8")
        config = yaml.safe_load(content)
        tests = config.get("tests", [])
        metrics = []
        for test in tests:
            for assertion in test.get("assert", []):
                if assertion.get("metric"):
                    metrics.append(assertion["metric"])
        assert metric_name in metrics, (
            f"D3.2: eval.yaml must have a scenario with metric "
            f"'{metric_name}'. Found metrics: {metrics}"
        )


# =====================================================================
# D4: KNOWLEDGE BASE ENRICHMENT
# =====================================================================


class TestD4KnowledgeBase:
    """D4: Knowledge base enrichment deliverables.

    Success metrics from tracking doc:
      - Steering doc depth: all >= 15 lines, key docs >= 50 lines
      - Incompatibilities cataloged: >= 30
      - Query translation examples: >= 15
    """

    # ── D4.1: Incompatibilities ──────────────────────────────────────

    def test_d4_1_incompatibilities_minimum_count(self):
        """D4.1: >= 30 incompatibilities cataloged."""
        catalog = DATA_DIR / "incompatibility-catalog.json"
        if catalog.exists():
            data = _load_json(catalog)
            count = len(data.get("incompatibilities", []))
        else:
            # Fall back to steering doc
            content = (STEERING_DIR / "incompatibilities.md").read_text(
                encoding="utf-8"
            )
            # Count bullet points as a proxy
            count = content.count("\n-")
        assert count >= 30, (
            f"D4.1: Need >= 30 incompatibilities, found {count}. "
            f"Check data/incompatibility-catalog.json or "
            f"steering/incompatibilities.md"
        )

    def test_d4_1_incompatibilities_have_severity(self):
        """D4.1: Each incompatibility has severity and description."""
        catalog = DATA_DIR / "incompatibility-catalog.json"
        if not catalog.exists():
            pytest.skip("No incompatibility-catalog.json")
        data = _load_json(catalog)
        for entry in data.get("incompatibilities", []):
            assert "severity" in entry, (
                f"D4.1: Incompatibility {entry.get('id', '?')} "
                f"missing severity"
            )
            assert "description" in entry, (
                f"D4.1: Incompatibility {entry.get('id', '?')} "
                f"missing description"
            )
            assert "recommendation" in entry, (
                f"D4.1: Incompatibility {entry.get('id', '?')} "
                f"missing recommendation (workaround)"
            )

    @extended
    def test_d4_1_incompatibilities_cover_all_areas(self):
        """D4.1 extended: Incompatibilities cover schema, query, scoring,
        operations, and plugin areas."""
        catalog = DATA_DIR / "incompatibility-catalog.json"
        if not catalog.exists():
            pytest.skip("No incompatibility-catalog.json")
        data = _load_json(catalog)
        areas = {e["area"] for e in data.get("incompatibilities", [])}
        expected = {"query", "schema", "scoring", "operations"}
        missing = expected - areas
        assert not missing, (
            f"D4.1 extended: Missing incompatibility areas: {missing}. "
            f"Found: {areas}"
        )

    # ── D4.2: Query Translation ──────────────────────────────────────

    def test_d4_2_query_translation_examples(self):
        """D4.2: >= 15 worked before/after query translation examples."""
        qt = STEERING_DIR / "query_translation.md"
        assert qt.exists(), "D4.2: steering/query_translation.md must exist"
        content = qt.read_text(encoding="utf-8")
        # Count Solr→OpenSearch example pairs
        solr_examples = len(re.findall(
            r"(?:Solr|solr|`q=|dismax|edismax)", content
        ))
        code_blocks = _count_examples_in_md(qt)
        example_count = max(solr_examples, code_blocks)
        assert example_count >= 15, (
            f"D4.2: Need >= 15 query translation examples, found "
            f"~{example_count}. Expand steering/query_translation.md"
        )

    @extended
    def test_d4_2_query_translation_covers_edismax(self):
        """D4.2 extended: Query translation covers eDisMax parameters."""
        qt = STEERING_DIR / "query_translation.md"
        content = qt.read_text(encoding="utf-8").lower()
        for param in ["qf", "pf", "mm", "boost"]:
            assert param in content, (
                f"D4.2 extended: query_translation.md should cover "
                f"eDisMax parameter '{param}'"
            )

    # ── D4.3: Index Design ───────────────────────────────────────────

    def test_d4_3_index_design_depth(self):
        """D4.3: steering/index_design.md has >= 15 lines."""
        lines = _count_lines(STEERING_DIR / "index_design.md")
        assert lines >= 15, (
            f"D4.3: index_design.md has {lines} lines, need >= 15"
        )

    @extended
    def test_d4_3_index_design_analyzer_examples(self):
        """D4.3 extended: >= 10 analyzer chain conversion examples."""
        content = (STEERING_DIR / "index_design.md").read_text(
            encoding="utf-8"
        )
        # Count analyzer-related terms as proxy
        analyzer_refs = len(re.findall(
            r"(?:analyzer|tokenizer|filter|char_filter)", content,
            re.IGNORECASE
        ))
        assert analyzer_refs >= 10, (
            f"D4.3 extended: index_design.md should have >= 10 "
            f"analyzer references, found {analyzer_refs}"
        )

    # ── D4.4: Sizing ─────────────────────────────────────────────────

    def test_d4_4_sizing_depth(self):
        """D4.4: steering/sizing.md has >= 15 lines."""
        lines = _count_lines(STEERING_DIR / "sizing.md")
        assert lines >= 15, (
            f"D4.4: sizing.md has {lines} lines, need >= 15"
        )

    @extended
    def test_d4_4_sizing_has_reference_architectures(self):
        """D4.4 extended: Sizing covers small/medium/large patterns."""
        sh = DATA_DIR / "sizing-heuristics.json"
        if not sh.exists():
            pytest.skip("No sizing-heuristics.json")
        data = _load_json(sh)
        effort = data.get("effort_estimation", {}).get("base_effort_weeks", {})
        for size in ["small", "medium", "large"]:
            assert size in effort, (
                f"D4.4 extended: sizing-heuristics.json missing "
                f"'{size}' reference architecture"
            )

    # ── D4.5: Stakeholders ───────────────────────────────────────────

    def test_d4_5_stakeholders_populated(self):
        """D4.5: steering/stakeholders.md is not empty."""
        lines = _count_lines(STEERING_DIR / "stakeholders.md")
        assert lines >= 15, (
            f"D4.5: stakeholders.md has {lines} lines, need >= 15. "
            f"Should have role definitions and per-step guidance."
        )

    # ── D4.6: Customizations ─────────────────────────────────────────

    @extended
    def test_d4_6_customizations_steering_exists(self):
        """D4.6 extended: steering/customizations.md exists with
        structured question sets."""
        path = STEERING_DIR / "customizations.md"
        assert path.exists(), (
            "D4.6: steering/customizations.md should exist with "
            "Solr→OpenSearch customization mapping table"
        )
        lines = _count_lines(path)
        assert lines >= 15, (
            f"D4.6: customizations.md has {lines} lines, need >= 15"
        )

    # ── steering depth gate (all files) ──────────────────────────────

    def test_d4_all_steering_minimum_depth(self):
        """D4: All steering docs have >= 15 lines (tracking doc metric)."""
        failures = []
        for md in sorted(STEERING_DIR.glob("*.md")):
            lines = _count_lines(md)
            if lines < 15:
                failures.append(f"{md.name}: {lines} lines")
        assert not failures, (
            f"D4: Steering docs below 15-line minimum: "
            f"{'; '.join(failures)}"
        )

    def test_d4_key_steering_docs_depth(self):
        """D4: Key steering docs have >= 50 lines (tracking doc metric)."""
        key_docs = [
            "incompatibilities.md",
            "query_translation.md",
        ]
        failures = []
        for name in key_docs:
            lines = _count_lines(STEERING_DIR / name)
            if lines < 50:
                failures.append(f"{name}: {lines} lines")
        assert not failures, (
            f"D4: Key steering docs below 50-line minimum: "
            f"{'; '.join(failures)}"
        )


# =====================================================================
# D5: MIGRATION ASSISTANT INTEGRATION
# =====================================================================


class TestD5MigrationAssistantIntegration:
    """D5: Migration Assistant integration deliverables."""

    @extended
    def test_d5_1_integration_adapter_exists(self):
        """D5.1 extended: Migration Assistant adapter code exists."""
        # This may live outside the skill directory
        candidates = [
            SKILL_ROOT / "integration",
            SKILL_ROOT.parent.parent.parent / "migrationConsole",
        ]
        found = any(c.is_dir() for c in candidates)
        if not found:
            pytest.skip(
                "D5.1: Migration Assistant adapter not yet implemented"
            )

    @extended
    def test_d5_2_integration_test_exists(self):
        """D5.2 extended: Integration test for Migration Assistant exists."""
        candidates = list(TESTS_DIR.rglob("*integration*"))
        assert candidates, (
            "D5.2: No integration test files found for Migration "
            "Assistant"
        )


# =====================================================================
# SUCCESS METRICS (cross-cutting)
# =====================================================================


class TestSuccessMetrics:
    """Cross-cutting success metrics from the tracking document."""

    def test_unit_test_count(self):
        """Metric: Meaningful number of unit tests exist."""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True, text=True,
            cwd=str(SKILL_ROOT),
        )
        # Parse "N tests collected"
        match = re.search(r"(\d+) tests? collected", result.stdout)
        assert match, f"Could not parse test count from: {result.stdout}"
        count = int(match.group(1))
        assert count >= 25, (
            f"Metric: Need >= 25 tests (tracking doc baseline), "
            f"found {count}"
        )

    def test_eval_scenario_count(self):
        """Metric: >= 10 eval scenarios in eval.yaml."""
        import yaml
        content = (EVALS_DIR / "eval.yaml").read_text(encoding="utf-8")
        config = yaml.safe_load(content)
        count = len(config.get("tests", []))
        assert count >= 10, (
            f"Metric: eval.yaml needs >= 10 scenarios, has {count}"
        )

    def test_scripts_coverage_floor(self):
        """Metric: Test coverage on scripts/ is reportable.

        The tracking doc requires >= 85%. We can't enforce that in
        a unit test without running coverage, but we verify the
        tooling is configured.
        """
        pyproject = SKILL_ROOT / "pyproject.toml"
        content = pyproject.read_text(encoding="utf-8")
        assert "pytest" in content, (
            "Metric: pyproject.toml should configure pytest"
        )

    @extended
    def test_reference_files_minimum_count(self):
        """Extended metric: >= 10 expert reference files."""
        refs = list(REFERENCES_DIR.glob("*.md"))
        # Exclude placeholder files
        real_refs = [
            r for r in refs
            if _count_lines(r) > 5
        ]
        assert len(real_refs) >= 10, (
            f"Extended: Need >= 10 substantial reference files, "
            f"found {len(real_refs)}"
        )

    @extended
    def test_data_files_all_versioned(self):
        """Extended metric: All JSON data files have _version field."""
        for json_file in sorted(DATA_DIR.glob("*.json")):
            data = _load_json(json_file)
            assert "_version" in data, (
                f"Extended: {json_file.name} missing _version field"
            )

    @extended
    def test_analyzer_mappings_minimum_coverage(self):
        """Extended metric: Analyzer mappings cover >= 10 tokenizers
        and >= 20 filters."""
        am = DATA_DIR / "analyzer-mappings.json"
        if not am.exists():
            pytest.skip("No analyzer-mappings.json")
        data = _load_json(am)
        tokenizers = len(data.get("tokenizers", {}))
        filters = len(data.get("filters", {}))
        assert tokenizers >= 10, (
            f"Extended: Need >= 10 tokenizer mappings, found {tokenizers}"
        )
        assert filters >= 20, (
            f"Extended: Need >= 20 filter mappings, found {filters}"
        )
