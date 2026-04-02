"""Unit tests for SolrInspector — mock-based, no live Solr needed."""

import json
import unittest.mock
from unittest.mock import patch, MagicMock

from solr_inspector import SolrInspector


def _mock_response(data: dict) -> MagicMock:
    """Create a mock urllib response that returns JSON data."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode("utf-8")
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestSolrInspectorURLs:
    """Verify correct URL construction for each API endpoint."""

    @patch("solr_inspector.urllib.request.urlopen")
    def test_get_schema_url(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"schema": {}})
        SolrInspector("http://solr:8983").get_schema("products")
        url = mock_urlopen.call_args[0][0].full_url
        assert "/solr/products/schema" in url
        assert "wt=json" in url

    @patch("solr_inspector.urllib.request.urlopen")
    def test_get_metrics_url(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"metrics": {}})
        SolrInspector("http://solr:8983").get_metrics("jvm")
        url = mock_urlopen.call_args[0][0].full_url
        assert "/solr/admin/metrics" in url
        assert "group=jvm" in url

    @patch("solr_inspector.urllib.request.urlopen")
    def test_get_mbeans_url(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"solr-mbeans": []})
        SolrInspector("http://solr:8983").get_mbeans("products", "CACHE")
        url = mock_urlopen.call_args[0][0].full_url
        assert "/solr/products/admin/mbeans" in url
        assert "cat=CACHE" in url

    @patch("solr_inspector.urllib.request.urlopen")
    def test_get_luke_url(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"index": {}})
        SolrInspector("http://solr:8983").get_luke("products")
        url = mock_urlopen.call_args[0][0].full_url
        assert "/solr/products/admin/luke" in url
        assert "numTerms=0" in url

    @patch("solr_inspector.urllib.request.urlopen")
    def test_get_system_info_url(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"lucene": {}})
        SolrInspector("http://solr:8983").get_system_info()
        url = mock_urlopen.call_args[0][0].full_url
        assert "/solr/admin/info/system" in url

    @patch("solr_inspector.urllib.request.urlopen")
    def test_list_collections_solrcloud(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(
            {"collections": ["col1", "col2"]}
        )
        result = SolrInspector("http://solr:8983").list_collections()
        assert result == ["col1", "col2"]

    @patch("solr_inspector.urllib.request.urlopen")
    def test_list_collections_standalone_fallback(self, mock_urlopen):
        """When Collections API fails, falls back to Core Admin."""
        import urllib.error
        mock_urlopen.side_effect = [
            urllib.error.HTTPError(
                "http://solr:8983/solr/admin/collections",
                400, "Bad Request", {}, None
            ),
            _mock_response({"status": {"core1": {}, "core2": {}}}),
        ]
        result = SolrInspector("http://solr:8983").list_collections()
        assert sorted(result) == ["core1", "core2"]


class TestSolrInspectorErrors:
    """Verify error handling."""

    @patch("solr_inspector.urllib.request.urlopen")
    def test_http_error_raises_runtime(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://solr:8983/solr/bad/schema",
            404, "Not Found", {}, None
        )
        inspector = SolrInspector("http://solr:8983")
        try:
            inspector.get_schema("bad")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "404" in str(e)

    @patch("solr_inspector.urllib.request.urlopen")
    def test_url_error_raises_runtime(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        inspector = SolrInspector("http://solr:8983")
        try:
            inspector.get_schema("products")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "Cannot reach Solr" in str(e)

    def test_trailing_slash_stripped(self):
        inspector = SolrInspector("http://solr:8983/")
        assert inspector.solr_url == "http://solr:8983"


class TestSolrInspectorReturnValues:
    """Verify return value handling."""

    @patch("solr_inspector.urllib.request.urlopen")
    def test_get_schema_returns_dict(self, mock_urlopen):
        expected = {"schema": {"fields": [{"name": "id"}]}}
        mock_urlopen.return_value = _mock_response(expected)
        result = SolrInspector("http://solr:8983").get_schema("test")
        assert result == expected

    @patch("solr_inspector.urllib.request.urlopen")
    def test_get_luke_returns_dict(self, mock_urlopen):
        expected = {"index": {"numDocs": 1000, "maxDoc": 1001}}
        mock_urlopen.return_value = _mock_response(expected)
        result = SolrInspector("http://solr:8983").get_luke("test")
        assert result == expected
