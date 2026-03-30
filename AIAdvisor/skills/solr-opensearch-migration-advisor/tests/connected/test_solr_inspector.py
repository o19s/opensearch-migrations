"""
Integration tests for SolrInspector against a running Solr instance.

Prerequisites:
    cd tests/connected && docker compose up -d

All tests are skipped if Solr is not reachable on localhost:38983.
"""

import sys
import os
import urllib.request

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from solr_inspector import SolrInspector


@pytest.fixture(scope="module")
def solr_available():
    """Skip all tests if Solr is not running on localhost:38983."""
    try:
        urllib.request.urlopen(
            "http://localhost:38983/solr/admin/info/system?wt=json", timeout=3
        )
    except Exception:
        pytest.skip("Solr not running on localhost:38983 — start with: docker compose up -d")


@pytest.fixture(scope="module")
def inspector():
    return SolrInspector("http://localhost:38983")


@pytest.fixture(scope="module")
def collection(inspector, solr_available):
    """Discover the first available collection/core."""
    collections = inspector.list_collections()
    assert len(collections) > 0, "No collections found in Solr"
    return collections[0]


class TestSolrInspectorConnected:
    """Integration tests requiring a live Solr instance."""

    def test_get_system_info(self, inspector, solr_available):
        info = inspector.get_system_info()
        assert "lucene" in info
        assert "solr-spec-version" in info["lucene"]

    def test_list_collections(self, inspector, solr_available):
        collections = inspector.list_collections()
        assert isinstance(collections, list)
        assert len(collections) > 0

    def test_get_schema(self, inspector, collection):
        schema = inspector.get_schema(collection)
        assert "schema" in schema
        assert "fields" in schema["schema"]

    def test_get_schema_has_field_types(self, inspector, collection):
        schema = inspector.get_schema(collection)
        assert "fieldTypes" in schema["schema"]
        assert len(schema["schema"]["fieldTypes"]) > 0

    def test_get_metrics(self, inspector, solr_available):
        metrics = inspector.get_metrics("core")
        assert "metrics" in metrics

    def test_get_metrics_jvm(self, inspector, solr_available):
        metrics = inspector.get_metrics("jvm")
        assert "metrics" in metrics

    def test_get_mbeans(self, inspector, collection):
        mbeans = inspector.get_mbeans(collection, "QUERYHANDLER")
        assert "solr-mbeans" in mbeans

    def test_get_luke(self, inspector, collection):
        luke = inspector.get_luke(collection)
        assert "index" in luke
        assert "numDocs" in luke["index"]

    def test_get_luke_has_fields(self, inspector, collection):
        luke = inspector.get_luke(collection)
        assert "fields" in luke


class TestSolrInspectorUnit:
    """Unit tests that don't require a running Solr instance."""

    def test_constructor_strips_trailing_slash(self):
        si = SolrInspector("http://example.com:8983/")
        assert si.solr_url == "http://example.com:8983"

    def test_constructor_default_url(self):
        si = SolrInspector()
        assert si.solr_url == "http://localhost:8983"

    def test_unreachable_raises_runtime_error(self):
        si = SolrInspector("http://localhost:19999")
        with pytest.raises(RuntimeError, match="Cannot reach Solr"):
            si.get_system_info()
