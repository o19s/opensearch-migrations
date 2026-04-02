"""Validate the structured data files in skills/solr-to-opensearch-migration/data/.

These JSON files are consumed by converters (schema_converter.py, query_converter.py)
and the report generator. Tests verify schema validity, required keys, internal
consistency, and cross-file references.
"""

import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


# ── helpers ──────────────────────────────────────────────────────────────────

def load_json(name: str) -> dict:
    path = DATA_DIR / name
    assert path.exists(), f"Missing data file: {name}"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ── analyzer-mappings.json ───────────────────────────────────────────────────

class TestAnalyzerMappings:
    @pytest.fixture(autouse=True)
    def data(self):
        self.am = load_json("analyzer-mappings.json")

    def test_has_required_sections(self):
        for section in ("tokenizers", "filters", "filters_no_equivalent", "char_filters", "parameter_mappings"):
            assert section in self.am, f"Missing section: {section}"

    def test_tokenizer_entries_have_opensearch_key(self):
        for solr_name, entry in self.am["tokenizers"].items():
            assert "opensearch" in entry, f"Tokenizer {solr_name} missing 'opensearch' key"
            assert "notes" in entry, f"Tokenizer {solr_name} missing 'notes' key"

    def test_filter_entries_have_opensearch_key(self):
        for solr_name, entry in self.am["filters"].items():
            assert "opensearch" in entry, f"Filter {solr_name} missing 'opensearch' key"
            # opensearch can be null (no equivalent)

    def test_char_filter_entries_have_opensearch_key(self):
        for solr_name, entry in self.am["char_filters"].items():
            assert "opensearch" in entry, f"Char filter {solr_name} missing 'opensearch' key"

    def test_solr_names_follow_naming_convention(self):
        """All Solr keys should start with 'solr.' prefix."""
        for section in ("tokenizers", "filters", "filters_no_equivalent", "char_filters"):
            for solr_name in self.am[section]:
                assert solr_name.startswith("solr."), f"Key {solr_name} in {section} should start with 'solr.'"

    def test_parameter_mappings_are_camel_to_snake(self):
        for camel, snake in self.am["parameter_mappings"].items():
            if camel.startswith("_"):
                continue
            assert "_" in snake or snake.islower(), f"Parameter mapping {camel} → {snake} doesn't look like snake_case"

    def test_no_duplicate_opensearch_names_within_section(self):
        for section in ("tokenizers", "filters", "char_filters"):
            os_names = [
                entry["opensearch"]
                for entry in self.am[section].values()
                if entry.get("opensearch") is not None
            ]
            dupes = [n for n in os_names if os_names.count(n) > 1]
            # Some dupes are expected (e.g., ngram appears as both tokenizer and filter)
            # but within a single section there should be no dupes
            assert len(set(dupes)) == 0, f"Duplicate opensearch names in {section}: {set(dupes)}"

    def test_minimum_coverage(self):
        assert len(self.am["tokenizers"]) >= 10, "Expected at least 10 tokenizer mappings"
        assert len(self.am["filters"]) >= 20, "Expected at least 20 filter mappings"
        assert len(self.am["char_filters"]) >= 3, "Expected at least 3 char_filter mappings"


# ── query-parameter-mappings.json ────────────────────────────────────────────

class TestQueryParameterMappings:
    @pytest.fixture(autouse=True)
    def data(self):
        self.qm = load_json("query-parameter-mappings.json")

    def test_has_required_sections(self):
        for section in ("dismax_parameters", "edismax_extensions", "filter_queries",
                        "faceting", "highlighting", "sorting", "pagination",
                        "special_queries", "no_equivalent"):
            assert section in self.qm, f"Missing section: {section}"

    def test_dismax_params_have_opensearch_path(self):
        for param, entry in self.qm["dismax_parameters"].items():
            assert "opensearch_path" in entry, f"DisMax param {param} missing 'opensearch_path'"

    def test_no_equivalent_entries_have_flag_and_severity(self):
        for feature, entry in self.qm["no_equivalent"].items():
            assert "flag_as" in entry, f"No-equivalent feature {feature} missing 'flag_as'"
            assert "severity" in entry, f"No-equivalent feature {feature} missing 'severity'"

    def test_faceting_covers_core_types(self):
        faceting = self.qm["faceting"]
        for facet_type in ("facet.field", "facet.range", "facet.pivot"):
            assert facet_type in faceting, f"Missing facet type: {facet_type}"

    def test_entries_with_examples_have_both_solr_and_opensearch(self):
        """If an entry has example_solr, it should also have example_opensearch (and vice versa)."""
        for section_name in ("dismax_parameters", "filter_queries", "faceting", "sorting", "pagination"):
            section = self.qm[section_name]
            for param, entry in section.items():
                if isinstance(entry, dict) and "example_solr" in entry:
                    assert "example_opensearch" in entry, \
                        f"{section_name}.{param} has example_solr but no example_opensearch"


# ── incompatibility-catalog.json ─────────────────────────────────────────────

class TestIncompatibilityCatalog:
    @pytest.fixture(autouse=True)
    def data(self):
        self.ic = load_json("incompatibility-catalog.json")

    def test_has_incompatibilities_list(self):
        assert "incompatibilities" in self.ic
        assert isinstance(self.ic["incompatibilities"], list)

    def test_minimum_count(self):
        assert len(self.ic["incompatibilities"]) >= 25, "Expected at least 25 incompatibilities"

    def test_required_fields_on_each_entry(self):
        required = {"id", "area", "feature", "category", "severity", "description", "recommendation"}
        for entry in self.ic["incompatibilities"]:
            missing = required - set(entry.keys())
            assert not missing, f"Incompatibility {entry.get('id', '???')} missing fields: {missing}"

    def test_ids_are_unique(self):
        ids = [entry["id"] for entry in self.ic["incompatibilities"]]
        dupes = [i for i in ids if ids.count(i) > 1]
        assert not dupes, f"Duplicate incompatibility IDs: {set(dupes)}"

    def test_ids_follow_naming_convention(self):
        """IDs should be AREA-NNN format."""
        import re
        pattern = re.compile(r"^[A-Z]+-\d{3}$")
        for entry in self.ic["incompatibilities"]:
            assert pattern.match(entry["id"]), \
                f"ID {entry['id']} doesn't match AREA-NNN pattern"

    def test_valid_categories(self):
        valid = {"Breaking", "Behavioral", "Unsupported"}
        for entry in self.ic["incompatibilities"]:
            assert entry["category"] in valid, \
                f"Incompatibility {entry['id']} has invalid category: {entry['category']}"

    def test_valid_severities(self):
        valid = {"high", "medium", "low"}
        for entry in self.ic["incompatibilities"]:
            assert entry["severity"] in valid, \
                f"Incompatibility {entry['id']} has invalid severity: {entry['severity']}"

    def test_detection_field_has_known_keys(self):
        valid_detection_keys = {
            "schema_xml", "solrconfig_xml", "query_params",
            "code_patterns", "cluster_topology", "deployment"
        }
        for entry in self.ic["incompatibilities"]:
            if "detection" in entry:
                unknown = set(entry["detection"].keys()) - valid_detection_keys
                assert not unknown, \
                    f"Incompatibility {entry['id']} has unknown detection keys: {unknown}"

    def test_areas_cover_expected_domains(self):
        areas = {entry["area"] for entry in self.ic["incompatibilities"]}
        for expected in ("query", "schema", "scoring", "operations"):
            assert expected in areas, f"Expected area '{expected}' not found"

    def test_id_prefix_matches_area(self):
        """The ID prefix should relate to the area (QUERY→query, SCHEMA→schema, etc.)."""
        area_to_prefix = {
            "query": "QUERY",
            "schema": "SCHEMA",
            "scoring": "SCORING",
            "operations": "OPS",
            "aws": "AWS",
        }
        for entry in self.ic["incompatibilities"]:
            prefix = entry["id"].split("-")[0]
            expected_prefix = area_to_prefix.get(entry["area"])
            if expected_prefix:
                assert prefix == expected_prefix, \
                    f"Incompatibility {entry['id']} area={entry['area']} but ID prefix is {prefix}"


# ── sizing-heuristics.json ───────────────────────────────────────────────────

class TestSizingHeuristics:
    @pytest.fixture(autouse=True)
    def data(self):
        self.sh = load_json("sizing-heuristics.json")

    def test_has_required_sections(self):
        for section in ("cluster_sizing", "effort_estimation", "cost_estimation"):
            assert section in self.sh, f"Missing section: {section}"

    def test_cluster_sizing_has_node_count_formula(self):
        ns = self.sh["cluster_sizing"]["node_count"]
        assert "formula" in ns
        assert "rule" in ns

    def test_effort_estimation_has_base_effort(self):
        be = self.sh["effort_estimation"]["base_effort_weeks"]
        for size in ("small", "medium", "large", "enterprise"):
            assert size in be, f"Missing base effort size: {size}"
            assert "range" in be[size]
            assert "criteria" in be[size]

    def test_per_incompatibility_effort_covers_categories(self):
        pie = self.sh["effort_estimation"]["per_incompatibility_effort"]
        for cat in ("Breaking", "Behavioral", "Unsupported"):
            assert cat in pie, f"Missing per-incompatibility effort for category: {cat}"
            assert "average_days" in pie[cat]

    def test_instance_type_guidance_has_patterns(self):
        itg = self.sh["cluster_sizing"]["instance_type_guidance"]
        for pattern in ("search_heavy", "index_heavy", "balanced"):
            assert pattern in itg, f"Missing instance type guidance: {pattern}"
            assert "recommendation" in itg[pattern]

    def test_cost_estimation_has_infrastructure(self):
        ci = self.sh["cost_estimation"]["infrastructure"]
        assert "rule" in ci


# ── workflow-step-prompts.json ───────────────────────────────────────────────

class TestWorkflowStepPrompts:
    @pytest.fixture(autouse=True)
    def data(self):
        self.wf = load_json("workflow-step-prompts.json")

    def test_has_steps_and_global_behaviors(self):
        assert "steps" in self.wf
        assert "global_behaviors" in self.wf

    def test_has_all_eight_steps(self):
        expected_steps = {
            "greeting", "schema_intake", "schema_review", "query_intake",
            "customization", "infrastructure", "integration", "report"
        }
        assert set(self.wf["steps"].keys()) == expected_steps

    def test_step_numbers_are_sequential(self):
        numbers = sorted(step["step_number"] for step in self.wf["steps"].values())
        assert numbers == list(range(8)), f"Step numbers should be 0-7, got {numbers}"

    def test_each_step_has_required_fields(self):
        required = {"step_number", "name", "next_step"}
        for step_name, step in self.wf["steps"].items():
            missing = required - set(step.keys())
            assert not missing, f"Step {step_name} missing fields: {missing}"

    def test_each_step_has_prompt(self):
        """Each step should have either prompt_text or prompt_text_template."""
        for step_name, step in self.wf["steps"].items():
            has_prompt = "prompt_text" in step or "prompt_text_template" in step
            assert has_prompt, f"Step {step_name} has no prompt_text or prompt_text_template"

    def test_next_step_references_are_valid(self):
        valid_steps = set(self.wf["steps"].keys()) | {None}
        for step_name, step in self.wf["steps"].items():
            assert step["next_step"] in valid_steps, \
                f"Step {step_name} references invalid next_step: {step['next_step']}"

    def test_step_chain_covers_all_steps(self):
        """Walking next_step from greeting should visit all steps."""
        visited = set()
        current = "greeting"
        while current is not None:
            assert current not in visited, f"Cycle detected at step {current}"
            visited.add(current)
            current = self.wf["steps"][current]["next_step"]
        assert visited == set(self.wf["steps"].keys()), \
            f"Step chain doesn't cover all steps. Missing: {set(self.wf['steps'].keys()) - visited}"

    def test_facts_to_record_present_where_expected(self):
        """Steps that gather user data should have facts_to_record."""
        data_steps = {"greeting", "schema_intake", "schema_review", "query_intake",
                      "customization", "infrastructure", "integration"}
        for step_name in data_steps:
            step = self.wf["steps"][step_name]
            assert "facts_to_record" in step, \
                f"Data-gathering step {step_name} should have facts_to_record"

    def test_report_step_has_report_sections(self):
        report = self.wf["steps"]["report"]
        assert "report_sections" in report
        assert len(report["report_sections"]) >= 7, "Report should have at least 7 sections"

    def test_customization_step_has_incompatibility_triggers(self):
        custom = self.wf["steps"]["customization"]
        assert "incompatibility_triggers" in custom
        triggers = custom["incompatibility_triggers"]
        for key in ("streaming_expressions", "cdcr", "data_import_handler"):
            assert key in triggers, f"Missing incompatibility trigger: {key}"
            assert "id" in triggers[key], f"Trigger {key} missing 'id'"


# ── cross-file consistency ───────────────────────────────────────────────────

class TestCrossFileConsistency:
    @pytest.fixture(autouse=True)
    def data(self):
        self.ic = load_json("incompatibility-catalog.json")
        self.wf = load_json("workflow-step-prompts.json")
        self.sh = load_json("sizing-heuristics.json")

    def test_workflow_incompatibility_triggers_reference_valid_ids(self):
        """IDs in workflow triggers should exist in the incompatibility catalog."""
        catalog_ids = {entry["id"] for entry in self.ic["incompatibilities"]}
        triggers = self.wf["steps"]["customization"]["incompatibility_triggers"]
        for trigger_name, trigger in triggers.items():
            assert trigger["id"] in catalog_ids, \
                f"Workflow trigger '{trigger_name}' references {trigger['id']} not in catalog"

    def test_sizing_incompatibility_categories_match_catalog(self):
        """Categories in sizing effort table should match catalog categories."""
        sizing_cats = set(self.sh["effort_estimation"]["per_incompatibility_effort"].keys())
        catalog_cats = {entry["category"] for entry in self.ic["incompatibilities"]}
        assert catalog_cats.issubset(sizing_cats), \
            f"Catalog has categories {catalog_cats - sizing_cats} not in sizing heuristics"

    def test_all_data_files_have_version(self):
        """All data files should have a _version field."""
        for name in ("analyzer-mappings.json", "query-parameter-mappings.json",
                      "incompatibility-catalog.json", "sizing-heuristics.json",
                      "workflow-step-prompts.json"):
            data = load_json(name)
            assert "_version" in data, f"{name} missing _version field"
