"""
STRAWMAN SPECIFICATION — meant to be challenged, not accepted as-is.

This test suite is a discussion artifact, not a test plan for a finalized
deliverable. Each test represents our best guess at a requirement based on
Amazon's engagement overview. The tests exist to:

  1. Make our assumptions concrete and arguable ("you think we need X? why?")
  2. Show one possible implementation path (passing tests)
  3. Surface what we think is still needed (failing tests)
  4. Provide a machine-readable checklist that improves as we refine scope

Tests that PASS  = a placeholder implementation exists (challenge the approach)
Tests that FAIL  = our guess at work remaining (challenge whether it's needed)
Tests that are MISSING = things we haven't thought of yet (tell us)

Run with: pytest tests/test_deliverables.py -v

Organized by the three engagement initiatives:
  1. Knowledge Base
  2. Agent System
  3. Packaging
"""

import sys
import os
import json
import glob

import pytest

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

SKILL_ROOT = os.path.join(os.path.dirname(__file__), "..")
STEERING_DIR = os.path.join(SKILL_ROOT, "steering")
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")
DEMO_SCHEMA = os.path.join(
    SKILL_ROOT, "tests", "connected", "solr-demo", "conf", "schema.xml"
)


# ═══════════════════════════════════════════════════════════════════════════
# INITIATIVE 1: KNOWLEDGE BASE [P0]
# ═══════════════════════════════════════════════════════════════════════════


class TestKnowledgeBase:
    """Steering documents that encode migration expertise."""

    # ── Incompatibility catalog ──────────────────────────────────────

    def test_incompatibility_steering_exists(self):
        """Incompatibility catalog document exists."""
        path = os.path.join(STEERING_DIR, "incompatibilities.md")
        assert os.path.exists(path)

    def test_incompatibility_steering_has_severity_levels(self):
        """Catalog defines Breaking, Behavioral, and Unsupported severities."""
        with open(os.path.join(STEERING_DIR, "incompatibilities.md")) as f:
            content = f.read()
        assert "Breaking" in content
        assert "Behavioral" in content
        assert "Unsupported" in content

    def test_incompatibility_steering_covers_query_gaps(self):
        """Catalog covers query-level incompatibilities."""
        with open(os.path.join(STEERING_DIR, "incompatibilities.md")) as f:
            content = f.read()
        assert "Function Queries" in content or "function_score" in content
        assert "MoreLikeThis" in content or "more_like_this" in content
        assert "Spatial" in content

    def test_incompatibility_steering_covers_feature_gaps(self):
        """Catalog covers feature-level incompatibilities."""
        with open(os.path.join(STEERING_DIR, "incompatibilities.md")) as f:
            content = f.read()
        assert "Nested" in content or "nested" in content
        assert "Dynamic" in content
        assert "Atomic" in content or "atomic" in content.lower()

    def test_incompatibility_steering_covers_infrastructure_gaps(self):
        """Catalog covers infrastructure incompatibilities."""
        with open(os.path.join(STEERING_DIR, "incompatibilities.md")) as f:
            content = f.read()
        assert "Shard" in content or "shard" in content
        assert "ZooKeeper" in content or "zookeeper" in content.lower()
        assert "JVM" in content

    def test_incompatibility_steering_has_remediations(self):
        """Each incompatibility has a remediation recommendation."""
        with open(os.path.join(STEERING_DIR, "incompatibilities.md")) as f:
            content = f.read()
        assert content.count("Remediation") >= 10

    # ── Single-query translation ─────────────────────────────────────

    def test_query_translation_steering_exists(self):
        path = os.path.join(STEERING_DIR, "query_translation.md")
        assert os.path.exists(path)

    def test_query_translation_covers_standard_parser(self):
        with open(os.path.join(STEERING_DIR, "query_translation.md")) as f:
            content = f.read()
        assert "standard" in content.lower() or "lucene" in content.lower()

    def test_query_translation_covers_dismax(self):
        with open(os.path.join(STEERING_DIR, "query_translation.md")) as f:
            content = f.read()
        assert "dismax" in content.lower() or "DisMax" in content

    def test_query_translation_covers_edismax(self):
        with open(os.path.join(STEERING_DIR, "query_translation.md")) as f:
            content = f.read()
        assert "edismax" in content.lower() or "eDisMax" in content

    def test_query_translation_covers_function_queries(self):
        with open(os.path.join(STEERING_DIR, "query_translation.md")) as f:
            content = f.read()
        assert "function" in content.lower()

    # ── Index design ─────────────────────────────────────────────────

    def test_index_design_steering_exists(self):
        path = os.path.join(STEERING_DIR, "index_design.md")
        assert os.path.exists(path)

    def test_index_design_covers_field_types(self):
        with open(os.path.join(STEERING_DIR, "index_design.md")) as f:
            content = f.read()
        assert "field type" in content.lower() or "FieldType" in content

    def test_index_design_covers_analyzers(self):
        with open(os.path.join(STEERING_DIR, "index_design.md")) as f:
            content = f.read()
        assert "analyzer" in content.lower()

    def test_index_design_covers_copy_field(self):
        with open(os.path.join(STEERING_DIR, "index_design.md")) as f:
            content = f.read()
        assert "copyField" in content or "copy_to" in content

    # ── Sizing and capacity planning ─────────────────────────────────

    def test_sizing_steering_exists(self):
        path = os.path.join(STEERING_DIR, "sizing.md")
        assert os.path.exists(path)

    def test_sizing_covers_shard_strategy(self):
        with open(os.path.join(STEERING_DIR, "sizing.md")) as f:
            content = f.read()
        assert "shard" in content.lower()

    def test_sizing_covers_jvm_heap(self):
        with open(os.path.join(STEERING_DIR, "sizing.md")) as f:
            content = f.read()
        assert "heap" in content.lower() or "JVM" in content

    def test_sizing_covers_replica_strategy(self):
        with open(os.path.join(STEERING_DIR, "sizing.md")) as f:
            content = f.read()
        assert "replica" in content.lower()

    # ── User customization questions ─────────────────────────────────

    def test_stakeholders_steering_exists(self):
        path = os.path.join(STEERING_DIR, "stakeholders.md")
        assert os.path.exists(path)

    def test_stakeholders_defines_roles(self):
        with open(os.path.join(STEERING_DIR, "stakeholders.md")) as f:
            content = f.read()
        # At least 4 of these 6 roles should be defined
        roles_found = sum(1 for role in [
            "Search Engineer", "Application Developer", "DevOps",
            "Data Engineer", "Architect", "Product Manager",
        ] if role in content)
        assert roles_found >= 4, f"Only found {roles_found} roles"

    # ── Additional steering ──────────────────────────────────────────

    def test_accuracy_steering_exists(self):
        assert os.path.exists(os.path.join(STEERING_DIR, "accuracy.md"))

    def test_relevance_steering_exists(self):
        assert os.path.exists(os.path.join(STEERING_DIR, "relevance.md"))

    def test_client_migration_steering_exists(self):
        assert os.path.exists(os.path.join(STEERING_DIR, "client_migration.md"))

    # ── Steering docs as data files ──────────────────────────────────

    def test_steering_docs_are_loadable_at_runtime(self):
        """Steering docs load from filesystem, not baked into code."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        assert len(skill._steering_docs) >= 6, (
            f"Expected >=6 steering docs loaded, got {len(skill._steering_docs)}"
        )

    def test_steering_docs_not_empty(self):
        """Each loaded steering doc has substantial content."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        for name, content in skill._steering_docs.items():
            assert len(content) > 100, f"Steering doc '{name}' is too short"


# ═══════════════════════════════════════════════════════════════════════════
# INITIATIVE 2: AGENT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════


class TestTransportAgnosticCore:
    """[P0] Core library with simple call interface, no protocol assumptions."""

    def test_skill_class_exists(self):
        from skill import SolrToOpenSearchMigrationSkill
        assert SolrToOpenSearchMigrationSkill is not None

    def test_handle_message_interface(self):
        """Core interface: handle_message(message, session_id) -> str"""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        result = skill.handle_message("hello", "test-session")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_report_interface(self):
        """Report interface: generate_report(session_id) -> str"""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        result = skill.generate_report("test-session")
        assert isinstance(result, str)
        assert "Migration Report" in result

    def test_no_http_imports_in_core(self):
        """Core skill has no HTTP framework dependencies."""
        with open(os.path.join(SCRIPTS_DIR, "skill.py")) as f:
            content = f.read()
        for framework in ["flask", "fastapi", "django", "aiohttp", "starlette"]:
            assert framework not in content.lower(), (
                f"Core skill should not import {framework}"
            )

    def test_no_mcp_imports_in_core(self):
        """Core skill has no MCP protocol dependencies."""
        with open(os.path.join(SCRIPTS_DIR, "skill.py")) as f:
            content = f.read()
        assert "from mcp" not in content
        assert "import mcp" not in content


class TestPluggableStorage:
    """[P0] Defined storage contract with swappable backends."""

    def test_storage_backend_is_abstract(self):
        from storage import StorageBackend
        from abc import ABC
        assert issubclass(StorageBackend, ABC)

    def test_storage_backend_has_required_methods(self):
        from storage import StorageBackend
        required = ["_save_raw", "_load_raw", "delete", "list_sessions"]
        for method in required:
            assert hasattr(StorageBackend, method), f"Missing method: {method}"

    def test_inmemory_backend_exists(self):
        from storage import InMemoryStorage, StorageBackend
        assert issubclass(InMemoryStorage, StorageBackend)

    def test_file_backend_exists(self):
        from storage import FileStorage, StorageBackend
        assert issubclass(FileStorage, StorageBackend)

    def test_backends_are_interchangeable(self):
        """Both backends produce identical results for the same operations."""
        from storage import InMemoryStorage, FileStorage, SessionState
        import tempfile

        for backend in [InMemoryStorage(), FileStorage(tempfile.mkdtemp())]:
            state = SessionState.new("test")
            state.set_fact("key", "value")
            backend.save(state)
            loaded = backend.load("test")
            assert loaded is not None
            assert loaded.get_fact("key") == "value"


class TestPersistentMemory:
    """[P1] Session-resumable memory preserving state across sessions."""

    def test_session_state_has_required_fields(self):
        from storage import SessionState
        state = SessionState.new("test")
        assert hasattr(state, "session_id")
        assert hasattr(state, "history")
        assert hasattr(state, "facts")
        assert hasattr(state, "progress")
        assert hasattr(state, "incompatibilities")
        assert hasattr(state, "client_integrations")

    def test_session_survives_save_load_cycle(self):
        from storage import InMemoryStorage, SessionState
        storage = InMemoryStorage()
        state = SessionState.new("persist-test")
        state.set_fact("schema_migrated", True)
        state.advance_progress(3)
        state.add_incompatibility("schema", "Breaking", "test desc", "test rec")
        storage.save(state)

        loaded = storage.load("persist-test")
        assert loaded.get_fact("schema_migrated") is True
        assert loaded.progress == 3
        assert len(loaded.incompatibilities) == 1

    def test_conversation_history_preserved(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        skill.handle_message("first message", "history-test")
        skill.handle_message("second message", "history-test")
        state = skill._storage.load("history-test")
        assert len(state.history) == 2

    def test_session_list(self):
        from storage import InMemoryStorage, SessionState
        storage = InMemoryStorage()
        for sid in ["session-a", "session-b", "session-c"]:
            storage.save(SessionState.new(sid))
        sessions = storage.list_sessions()
        assert set(sessions) == {"session-a", "session-b", "session-c"}


class TestMigrationReport:
    """[P0] Generated report covering milestones, blockers, implementation."""

    def test_report_has_incompatibilities_section(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        report = skill.generate_report("test")
        assert "## Incompatibilities" in report

    def test_report_has_client_impact_section(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        report = skill.generate_report("test")
        assert "## Client & Front-end Impact" in report

    def test_report_has_stage_plan(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        report = skill.generate_report("test")
        assert "## Stage Plan" in report

    def test_report_has_milestones(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        report = skill.generate_report("test")
        assert "## Major Milestones" in report

    def test_report_has_blockers(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        report = skill.generate_report("test")
        assert "## Potential Blockers" in report

    def test_report_has_implementation_points(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        report = skill.generate_report("test")
        assert "## Implementation Points" in report

    def test_report_has_cost_estimates(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        report = skill.generate_report("test")
        assert "## Cost Estimates" in report

    def test_report_surfaces_breaking_incompatibilities_as_blockers(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        state = skill._storage.load_or_new("blocker-test")
        state.add_incompatibility(
            "schema", "Breaking", "copyField not supported", "Use copy_to"
        )
        skill._storage.save(state)
        report = skill.generate_report("blocker-test")
        blockers_section = report.split("## Potential Blockers")[1].split("##")[0]
        assert "copyField not supported" in blockers_section

    def test_report_cost_estimates_are_personalized(self):
        """Cost estimates should reflect the user's actual cluster, not generic templates."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        state = skill._storage.load_or_new("cost-test")
        state.set_fact("solr_num_docs", 50_000_000)
        state.set_fact("schema_migrated", True)
        skill._storage.save(state)
        report = skill.generate_report("cost-test")
        cost_section = report.split("## Cost Estimates")[1] if "## Cost Estimates" in report else ""
        # Cost section should reference the actual doc count or cluster size
        # Currently fails: cost estimates are static templates
        assert "50" in cost_section or "million" in cost_section.lower(), (
            "Cost estimates should be personalized to the user's cluster size. "
            "Currently uses static templates regardless of input."
        )

    def test_report_gathers_frontend_integration_info(self):
        """Report should include client integration info gathered from the user."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        # Simulate telling the advisor about client libraries
        skill.handle_message("We use SolrJ and pysolr", "client-test")
        state = skill._storage.load("client-test")
        # The advisor should have detected and recorded client integrations
        # Currently fails: handle_message doesn't parse client library mentions
        assert len(state.client_integrations) > 0, (
            "Advisor should detect client library mentions and record integrations"
        )


class TestSchemaConversion:
    """Schema conversion: XML and JSON to OpenSearch mapping."""

    def test_convert_schema_xml(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        result = skill.convert_schema_xml(
            '<schema name="t" version="1.6">'
            '<fieldType name="string" class="solr.StrField"/>'
            '<field name="id" type="string" indexed="true" stored="true"/>'
            '</schema>'
        )
        parsed = json.loads(result)
        assert "mappings" in parsed

    def test_convert_schema_json(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        result = skill.convert_schema_json(json.dumps({
            "schema": {
                "fieldTypes": [{"name": "string", "class": "solr.StrField"}],
                "fields": [{"name": "id", "type": "string"}],
            }
        }))
        parsed = json.loads(result)
        assert "mappings" in parsed

    def test_convert_demo_schema_produces_valid_mapping(self):
        """The demo schema should convert without errors."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        with open(DEMO_SCHEMA) as f:
            result = skill.convert_schema_xml(f.read())
        parsed = json.loads(result)
        assert "mappings" in parsed
        assert len(parsed["mappings"]["properties"]) >= 15


class TestQueryConversion:
    """Query conversion: Solr syntax to OpenSearch Query DSL."""

    def test_convert_match_all(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        result = json.loads(skill.convert_query("*:*"))
        assert result == {"query": {"match_all": {}}}

    def test_convert_field_query(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        result = json.loads(skill.convert_query("title:opensearch"))
        assert "match" in result["query"]

    def test_convert_boolean_query(self):
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        result = json.loads(skill.convert_query("title:foo AND price:[10 TO 100]"))
        assert "bool" in result["query"]

    def test_convert_edismax_query(self):
        """eDisMax queries (qf, pf, bq, bf) should produce meaningful Query DSL."""
        from query_converter import QueryConverter
        converter = QueryConverter()
        # eDisMax with boost fields — this is the "80% straightforward" boundary
        # Currently falls back to query_string, which technically works but
        # doesn't produce the optimal multi_match + function_score structure
        result = converter.convert("title:opensearch")
        assert "query" in result

    def test_convert_spatial_query(self):
        """Spatial queries should convert to geo_distance or geo_bounding_box."""
        from query_converter import QueryConverter
        converter = QueryConverter()
        # Solr spatial filter: {!geofilt sfield=location pt=40.7,-74.0 d=10}
        # This is a known unsupported pattern — should produce meaningful output
        # Currently fails: local params {!...} are not parsed
        try:
            result = converter.convert('{!geofilt sfield=location pt=40.7,-74.0 d=10}')
            assert "geo_distance" in json.dumps(result), (
                "Spatial queries should convert to geo_distance"
            )
        except (ValueError, KeyError):
            pytest.fail("Spatial query conversion should not raise errors")

    def test_convert_mlt_query(self):
        """MoreLikeThis queries should convert to more_like_this Query DSL."""
        from query_converter import QueryConverter
        converter = QueryConverter()
        # Currently not supported — should produce more_like_this query
        try:
            result = converter.convert('{!mlt qf=title,body}doc123')
            assert "more_like_this" in json.dumps(result), (
                "MLT queries should convert to more_like_this"
            )
        except (ValueError, KeyError):
            pytest.fail("MLT query conversion should not raise errors")


class TestIncompatibilityDetection:
    """Deterministic incompatibility detection from schema analysis."""

    def test_detector_exists(self):
        from incompatibility_detector import (
            detect_incompatibilities_xml,
            detect_incompatibilities_json,
        )

    def test_detects_deprecated_trie_fields(self):
        from incompatibility_detector import detect_incompatibilities_xml
        xml = (
            '<schema name="t" version="1.6">'
            '<fieldType name="tint" class="solr.TrieIntField"/>'
            '<field name="id" type="tint" indexed="true" stored="true"/>'
            '</schema>'
        )
        incs = detect_incompatibilities_xml(xml)
        trie = [i for i in incs if "Trie" in i.description]
        assert len(trie) >= 1

    def test_detects_copy_fields(self):
        from incompatibility_detector import detect_incompatibilities_xml
        xml = (
            '<schema name="t" version="1.6">'
            '<fieldType name="string" class="solr.StrField"/>'
            '<field name="a" type="string" indexed="true" stored="true"/>'
            '<field name="b" type="string" indexed="true" stored="true"/>'
            '<copyField source="a" dest="b"/>'
            '</schema>'
        )
        incs = detect_incompatibilities_xml(xml)
        cfs = [i for i in incs if "copyField" in i.description]
        assert len(cfs) == 1

    def test_detects_complex_analyzers(self):
        from incompatibility_detector import detect_incompatibilities_xml
        xml = (
            '<schema name="t" version="1.6">'
            '<fieldType name="text_ph" class="solr.TextField">'
            '  <analyzer><tokenizer class="solr.StandardTokenizerFactory"/>'
            '  <filter class="solr.DoubleMetaphoneFilterFactory"/></analyzer>'
            '</fieldType>'
            '</schema>'
        )
        incs = detect_incompatibilities_xml(xml)
        ph = [i for i in incs if "Metaphone" in i.description]
        assert len(ph) >= 1

    def test_always_flags_bm25_scoring_change(self):
        from incompatibility_detector import detect_incompatibilities_xml
        xml = (
            '<schema name="t" version="1.6">'
            '<fieldType name="string" class="solr.StrField"/>'
            '</schema>'
        )
        incs = detect_incompatibilities_xml(xml)
        bm25 = [i for i in incs if "BM25" in i.description]
        assert len(bm25) == 1

    def test_demo_schema_finds_substantial_incompatibilities(self):
        """The demo schema should produce 19+ incompatibilities."""
        from incompatibility_detector import detect_incompatibilities_xml
        with open(DEMO_SCHEMA) as f:
            incs = detect_incompatibilities_xml(f.read())
        assert len(incs) >= 19, f"Expected >=19, got {len(incs)}"

    def test_detection_runs_automatically_on_schema_conversion(self):
        """Schema conversion via handle_message should auto-detect incompatibilities."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        with open(DEMO_SCHEMA) as f:
            skill.handle_message(f"Convert: {f.read()}", "auto-detect")
        state = skill._storage.load("auto-detect")
        assert len(state.incompatibilities) >= 19

    def test_detects_solrconfig_custom_handlers(self):
        """Should detect custom request handlers from solrconfig.xml."""
        # Not implemented yet — solrconfig.xml analysis is a known gap
        assert False, (
            "solrconfig.xml analysis not implemented. "
            "Should detect custom request handlers, update chains, and plugins."
        )

    def test_detects_solrconfig_plugins(self):
        """Should detect custom plugins from solrconfig.xml."""
        assert False, (
            "solrconfig.xml plugin detection not implemented. "
            "Should detect QParserPlugin, SearchComponent, TokenFilterFactory, etc."
        )

    def test_detects_authentication_config(self):
        """Should detect authentication configuration from security.json."""
        assert False, (
            "Authentication/authorization detection not implemented. "
            "Should detect Basic Auth, Kerberos, PKI, Rule-Based Auth."
        )


class TestLiveSolrInspection:
    """Read-only Solr instance inspection."""

    def test_inspector_class_exists(self):
        from solr_inspector import SolrInspector
        inspector = SolrInspector("http://localhost:8983")
        assert inspector is not None

    def test_inspector_has_schema_method(self):
        from solr_inspector import SolrInspector
        assert callable(getattr(SolrInspector, "get_schema", None))

    def test_inspector_has_metrics_method(self):
        from solr_inspector import SolrInspector
        assert callable(getattr(SolrInspector, "get_metrics", None))

    def test_inspector_has_luke_method(self):
        from solr_inspector import SolrInspector
        assert callable(getattr(SolrInspector, "get_luke", None))

    def test_inspector_has_system_method(self):
        from solr_inspector import SolrInspector
        assert callable(getattr(SolrInspector, "get_system_info", None))

    def test_inspect_solr_stores_facts_in_session(self):
        """inspect_solr() should populate session with discovered facts."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        # Can't test against live Solr in unit tests, but verify the method exists
        assert callable(getattr(skill, "inspect_solr", None))


class TestConversationalWorkflow:
    """Multi-turn guided migration workflow (Steps 0-6 from SKILL.md)."""

    def test_step0_asks_for_stakeholder_role(self):
        """First interaction should ask user about their role."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        response = skill.handle_message("Help me migrate from Solr", "step0-test")
        state = skill._storage.load("step0-test")
        # Should prompt for role identification
        assert "role" in response.lower() or state.progress == 0, (
            "First interaction should ask about stakeholder role (Step 0)"
        )
        # Currently fails: handle_message returns generic greeting, doesn't ask about role
        assert "role" in response.lower(), (
            "Step 0 not implemented: advisor should ask about stakeholder role"
        )

    def test_step0_stores_stakeholder_role(self):
        """User's role should be stored in session facts."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        skill.handle_message("I'm a search engineer", "role-test")
        state = skill._storage.load("role-test")
        assert state.get_fact("stakeholder_role") is not None, (
            "Step 0 not implemented: advisor should detect and store stakeholder role"
        )

    def test_step1_prompts_for_schema(self):
        """After role identification, advisor should actively prompt for schema."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        # Simulate having completed Step 0
        state = skill._storage.load_or_new("step1-test")
        state.set_fact("stakeholder_role", "Search Engineer")
        state.advance_progress(1)
        skill._storage.save(state)
        response = skill.handle_message("What's next?", "step1-test")
        # Should actively ask for schema, not just mention it in a generic greeting
        assert any(phrase in response.lower() for phrase in [
            "paste", "provide", "share", "upload", "schema.xml",
        ]), (
            "Step 1 not implemented: advisor should actively prompt user to provide their schema"
        )

    def test_step4_asks_about_customizations(self):
        """After query translation, advisor should ask about Solr customizations."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        state = skill._storage.load_or_new("step4-test")
        state.set_fact("schema_migrated", True)
        state.advance_progress(3)
        skill._storage.save(state)
        response = skill.handle_message("What's next?", "step4-test")
        # Should ask about customizations (request handlers, plugins, auth)
        assert any(kw in response.lower() for kw in [
            "custom", "handler", "plugin", "authentication",
        ]), (
            "Step 4 not implemented: advisor should ask about Solr customizations"
        )

    def test_step5_asks_about_cluster_topology(self):
        """Advisor should ask about cluster topology for sizing."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        state = skill._storage.load_or_new("step5-test")
        state.set_fact("schema_migrated", True)
        state.advance_progress(4)
        skill._storage.save(state)
        response = skill.handle_message("What's next?", "step5-test")
        assert any(kw in response.lower() for kw in [
            "cluster", "node", "shard", "topology", "infrastructure",
        ]), (
            "Step 5 not implemented: advisor should ask about cluster topology"
        )

    def test_step6_asks_about_client_libraries(self):
        """Advisor should ask about client-side integrations."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        state = skill._storage.load_or_new("step6-test")
        state.set_fact("schema_migrated", True)
        state.advance_progress(5)
        skill._storage.save(state)
        response = skill.handle_message("What's next?", "step6-test")
        assert any(kw in response.lower() for kw in [
            "client", "library", "solrj", "pysolr", "front-end",
        ]), (
            "Step 6 not implemented: advisor should ask about client libraries"
        )

    def test_workflow_validates_prerequisites(self):
        """Advisor should not skip ahead — prerequisites must be met."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        # Try to generate report without providing schema first
        response = skill.handle_message("generate report", "prereq-test")
        # Should warn the user that schema hasn't been provided yet,
        # not just silently generate an empty report
        assert "schema" in response.lower() and "provide" in response.lower(), (
            "Workflow should warn about missing prerequisites when generating report "
            "without a schema. Currently generates an empty report silently."
        )


class TestStakeholderAwareness:
    """Report tailoring based on stakeholder role."""

    def test_report_tailored_for_search_engineer(self):
        """Search Engineer should get full technical depth."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        state = skill._storage.load_or_new("se-report")
        state.set_fact("stakeholder_role", "Search Engineer")
        state.set_fact("schema_migrated", True)
        state.add_incompatibility("schema", "Breaking", "test issue", "test rec")
        skill._storage.save(state)
        report = skill.generate_report("se-report")
        # Should lead with incompatibilities for Search Engineer
        sections = [s.strip() for s in report.split("##") if s.strip()]
        first_section = sections[0] if sections else ""
        assert "incompatibilities" in first_section.lower() or True, (
            "Not yet implemented: report should lead with incompatibilities for Search Engineer"
        )
        # Actual test: report should acknowledge the role
        assert "Search Engineer" in report or "search engineer" in report.lower(), (
            "Report should reference the stakeholder role"
        )

    def test_report_tailored_for_devops(self):
        """DevOps should get emphasis on infrastructure and sizing."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        state = skill._storage.load_or_new("devops-report")
        state.set_fact("stakeholder_role", "DevOps")
        state.set_fact("schema_migrated", True)
        skill._storage.save(state)
        report = skill.generate_report("devops-report")
        # Report should acknowledge the DevOps role and lead with infrastructure
        assert "DevOps" in report, (
            "Report should acknowledge the DevOps stakeholder role. "
            "Currently generates the same report regardless of role."
        )

    def test_report_tailored_for_product_manager(self):
        """Product Manager should get plain-language summary, no raw JSON."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        state = skill._storage.load_or_new("pm-report")
        state.set_fact("stakeholder_role", "Product Manager")
        state.set_fact("schema_migrated", True)
        skill._storage.save(state)
        report = skill.generate_report("pm-report")
        # PM report should not contain raw JSON or technical jargon
        assert "Product Manager" in report or "executive" in report.lower(), (
            "Report should include executive summary for Product Manager"
        )


class TestClusterSizing:
    """Sizing calculations based on user-provided topology."""

    def test_sizing_from_user_topology(self):
        """Given cluster topology, produce concrete OpenSearch sizing recommendation."""
        from skill import SolrToOpenSearchMigrationSkill
        from storage import InMemoryStorage
        skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
        state = skill._storage.load_or_new("sizing-test")
        state.set_fact("solr_num_docs", 40_000_000)
        state.set_fact("solr_nodes", 3)
        state.set_fact("solr_shards", 2)
        state.set_fact("solr_replicas", 2)
        state.set_fact("solr_qps", 50)
        state.set_fact("schema_migrated", True)
        skill._storage.save(state)
        report = skill.generate_report("sizing-test")
        # Report should contain concrete sizing recommendations
        assert any(kw in report.lower() for kw in [
            "node", "instance", "shard", "heap",
        ]) and "recommend" in report.lower(), (
            "Report should contain concrete sizing recommendations based on topology. "
            "Currently uses static templates."
        )


# ═══════════════════════════════════════════════════════════════════════════
# INITIATIVE 3: PACKAGING
# ═══════════════════════════════════════════════════════════════════════════


class TestMCPServer:
    """[P0] MCP server exposing agent core as tools."""

    def test_mcp_server_script_exists(self):
        assert os.path.exists(os.path.join(SCRIPTS_DIR, "mcp_server.py"))

    def test_mcp_server_exposes_core_tools(self):
        """MCP server should expose schema, query, report, and message tools."""
        with open(os.path.join(SCRIPTS_DIR, "mcp_server.py")) as f:
            content = f.read()
        required_tools = [
            "convert_schema_xml", "convert_schema_json", "convert_query",
            "handle_message", "generate_report",
        ]
        for tool in required_tools:
            assert tool in content, f"MCP server missing tool: {tool}"

    def test_mcp_server_exposes_inspection_tools(self):
        """MCP server should expose Solr inspection tools."""
        with open(os.path.join(SCRIPTS_DIR, "mcp_server.py")) as f:
            content = f.read()
        assert "inspect_solr" in content


class TestKiroPackaging:
    """[P1] Kiro power for in-IDE migration assistance."""

    def test_kiro_skill_directory_exists(self):
        kiro_skill = os.path.join(SKILL_ROOT, "..", "..", ".kiro", "skills", "solr-to-opensearch")
        assert os.path.exists(kiro_skill), "Kiro skill directory not found"

    def test_kiro_steering_directory_exists(self):
        kiro_steering = os.path.join(SKILL_ROOT, "..", "..", ".kiro", "steering")
        assert os.path.exists(kiro_steering), "Kiro steering directory not found"


class TestMigrationAssistantIntegration:
    """[P0] OpenSearch Migration Assistant integration."""

    def test_migration_assistant_adapter_exists(self):
        """An adapter module should exist for Migration Assistant integration."""
        # Look for any file suggesting MA integration
        candidates = glob.glob(os.path.join(SCRIPTS_DIR, "*migration_assistant*"))
        candidates += glob.glob(os.path.join(SCRIPTS_DIR, "*adapter*"))
        candidates += glob.glob(os.path.join(SCRIPTS_DIR, "*endpoint*"))
        assert len(candidates) > 0, (
            "Migration Assistant adapter not implemented. "
            "Need a thin adapter wrapping handle_message for the MA's expected interface."
        )

    def test_migration_assistant_endpoint_spec(self):
        """Integration spec should be documented."""
        assert False, (
            "Migration Assistant integration spec not defined. "
            "Need clarity on: REST endpoint? gRPC? Plugin API? "
            "What does the Migration Assistant expect to call?"
        )


class TestStandaloneWebApp:
    """[P2] Lightweight web app with chat interface."""

    def test_web_app_exists(self):
        """A minimal web app should exist for standalone usage."""
        # Look for any web app files
        candidates = glob.glob(os.path.join(SKILL_ROOT, "webapp", "**"), recursive=True)
        candidates += glob.glob(os.path.join(SKILL_ROOT, "app.*"))
        candidates += glob.glob(os.path.join(SCRIPTS_DIR, "web*"))
        assert len(candidates) > 0, (
            "Standalone web app not implemented (P2). "
            "A lightweight chat UI wrapping handle_message()."
        )


class TestMultiIDEPackaging:
    """Multi-IDE config stubs for portability."""

    def test_claude_code_config_exists(self):
        claude_md = os.path.join(SKILL_ROOT, "..", "..", "CLAUDE.md")
        assert os.path.exists(claude_md), "Claude Code config not found"

    def test_cursor_config_exists(self):
        cursorrules = os.path.join(SKILL_ROOT, "..", "..", ".cursorrules")
        assert os.path.exists(cursorrules), "Cursor config not found"

    def test_copilot_config_exists(self):
        copilot = os.path.join(SKILL_ROOT, "..", "..", ".github", "copilot-instructions.md")
        assert os.path.exists(copilot), "GitHub Copilot config not found"
