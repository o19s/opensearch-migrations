"""Tests for artifact_generator.py"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import pytest

from artifact_generator import (
    generate_progress_dashboard,
    generate_intake_worksheet,
    generate_incompatibility_tracker,
)
from storage import SessionState, Incompatibility, ClientIntegration


@pytest.fixture
def empty_state():
    return SessionState.new("test-session")


@pytest.fixture
def rich_state():
    """A session with data in every field — simulates a mid-migration state."""
    state = SessionState.new("acme-migration")
    state.progress = 4
    state.set_fact("stakeholder_role", "architect")
    state.set_fact("schema_source", "xml")
    state.set_fact("schema_migrated", True)
    state.set_fact("solr_version", "7.7.3")
    state.set_fact("solr_collection", "products")
    state.set_fact("solr_num_docs", 1_500_000)
    state.set_fact("target_platform", "aws_managed")
    state.set_fact("queries_translated", 12)
    state.set_fact("customizations_assessed", True)
    state.set_fact("auth_method", "BasicAuth")
    state.set_fact("customizations", {
        "Custom UpdateProcessor": "Ingest pipeline",
        "CDCR": "Cross-cluster replication",
    })
    state.add_incompatibility(
        "schema", "Breaking", "copyField unsupported", "Use copy_to"
    )
    state.add_incompatibility(
        "query", "Behavioral", "BM25 vs TF-IDF drift", "Baseline before cutover"
    )
    state.add_incompatibility(
        "plugin", "Unsupported", "Custom QParser", "Rewrite as Query DSL"
    )
    state.add_client_integration(
        "SolrJ", "library", "Java search client", "Replace with opensearch-java"
    )
    return state


TS = datetime(2026, 4, 2, 18, 30, tzinfo=timezone.utc)


# ------------------------------------------------------------------
# Progress dashboard
# ------------------------------------------------------------------

class TestProgressDashboard:

    def test_creates_file(self, tmp_path, rich_state):
        path = generate_progress_dashboard(rich_state, str(tmp_path), now=TS)
        assert os.path.exists(path)
        assert path.endswith(".md")

    def test_filename_pattern(self, tmp_path, rich_state):
        path = generate_progress_dashboard(rich_state, str(tmp_path), now=TS)
        assert os.path.basename(path) == "progress-acme-migration-202604021830.md"

    def test_contains_session_id(self, tmp_path, rich_state):
        path = generate_progress_dashboard(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "acme-migration" in content

    def test_contains_phase_table(self, tmp_path, rich_state):
        path = generate_progress_dashboard(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "Executive Summary" in content
        assert "Stakeholder identification" in content
        assert "Schema acquisition" in content
        assert "Report & recommendations" in content

    def test_phase_status_reflects_progress(self, tmp_path, rich_state):
        path = generate_progress_dashboard(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "| 0. Stakeholder identification | Done |" in content
        assert "| 4. Customization assessment | In progress |" in content
        assert "| 5. Infrastructure planning | Not started |" in content

    def test_incompatibility_counts(self, tmp_path, rich_state):
        path = generate_progress_dashboard(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "1 breaking" in content
        assert "1 unsupported" in content
        assert "1 behavioral" in content

    def test_empty_state_not_started(self, tmp_path, empty_state):
        empty_state.set_fact("stakeholder_role", "developer")
        path = generate_progress_dashboard(empty_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "Not started" in content

    def test_client_integrations_shown(self, tmp_path, rich_state):
        path = generate_progress_dashboard(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "SolrJ" in content
        assert "opensearch-java" in content

    def test_no_client_integrations_message(self, tmp_path, empty_state):
        empty_state.set_fact("stakeholder_role", "developer")
        path = generate_progress_dashboard(empty_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "No client integrations recorded" in content


# ------------------------------------------------------------------
# Intake worksheet
# ------------------------------------------------------------------

class TestIntakeWorksheet:

    def test_creates_file(self, tmp_path, rich_state):
        path = generate_intake_worksheet(rich_state, str(tmp_path), now=TS)
        assert os.path.exists(path)

    def test_filename_pattern(self, tmp_path, rich_state):
        path = generate_intake_worksheet(rich_state, str(tmp_path), now=TS)
        assert os.path.basename(path) == "intake-acme-migration-202604021830.md"

    def test_quick_facts_populated(self, tmp_path, rich_state):
        path = generate_intake_worksheet(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "7.7.3" in content
        assert "products" in content
        assert "1500000" in content
        assert "aws_managed" in content

    def test_missing_facts_show_placeholder(self, tmp_path, empty_state):
        empty_state.progress = 1
        path = generate_intake_worksheet(empty_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "\u2014" in content  # em-dash placeholder

    def test_customizations_shown(self, tmp_path, rich_state):
        path = generate_intake_worksheet(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "Custom UpdateProcessor" in content
        assert "Ingest pipeline" in content

    def test_open_questions_for_gaps(self, tmp_path, empty_state):
        empty_state.progress = 1
        path = generate_intake_worksheet(empty_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "Schema not yet provided" in content
        assert "Target platform not decided" in content

    def test_no_open_questions_when_complete(self, tmp_path, rich_state):
        path = generate_intake_worksheet(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "No open questions" in content


# ------------------------------------------------------------------
# Incompatibility tracker
# ------------------------------------------------------------------

class TestIncompatibilityTracker:

    def test_creates_file(self, tmp_path, rich_state):
        path = generate_incompatibility_tracker(rich_state, str(tmp_path), now=TS)
        assert os.path.exists(path)

    def test_filename_pattern(self, tmp_path, rich_state):
        path = generate_incompatibility_tracker(rich_state, str(tmp_path), now=TS)
        assert os.path.basename(path) == "incompatibilities-acme-migration-202604021830.md"

    def test_header_counts(self, tmp_path, rich_state):
        path = generate_incompatibility_tracker(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "**Total:** 3" in content
        assert "**Breaking:** 1" in content
        assert "**Unsupported:** 1" in content
        assert "**Behavioral:** 1" in content

    def test_breaking_items_listed(self, tmp_path, rich_state):
        path = generate_incompatibility_tracker(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "copyField unsupported" in content
        assert "Use copy_to" in content
        assert "B-1" in content

    def test_unsupported_items_listed(self, tmp_path, rich_state):
        path = generate_incompatibility_tracker(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "Custom QParser" in content
        assert "U-1" in content

    def test_behavioral_items_listed(self, tmp_path, rich_state):
        path = generate_incompatibility_tracker(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "BM25 vs TF-IDF drift" in content
        assert "V-1" in content

    def test_cutover_blocking_count(self, tmp_path, rich_state):
        path = generate_incompatibility_tracker(rich_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "Cutover-blocking items | 2" in content

    def test_empty_incompatibilities(self, tmp_path, empty_state):
        path = generate_incompatibility_tracker(empty_state, str(tmp_path), now=TS)
        content = open(path).read()
        assert "**Total:** 0" in content
        assert "No breaking incompatibilities found" in content

    def test_multiple_snapshots_coexist(self, tmp_path, rich_state):
        ts1 = datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 4, 2, 19, 0, tzinfo=timezone.utc)
        p1 = generate_incompatibility_tracker(rich_state, str(tmp_path), now=ts1)
        p2 = generate_incompatibility_tracker(rich_state, str(tmp_path), now=ts2)
        assert p1 != p2
        assert os.path.exists(p1)
        assert os.path.exists(p2)
