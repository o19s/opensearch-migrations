"""Tests for mcp_server.py — exercises each registered tool function."""
import json
from unittest.mock import patch, MagicMock
import pytest

# Import the module-level tool functions directly (bypassing FastMCP decorator
# side-effects) by importing the module and accessing its globals.
import mcp_server as _mod
from skill import SolrToOpenSearchMigrationSkill
from storage import InMemoryStorage


@pytest.fixture(autouse=True)
def in_memory_skill(monkeypatch):
    monkeypatch.setattr(
        _mod,
        "_skill",
        SolrToOpenSearchMigrationSkill(storage=InMemoryStorage()),
    )


# --- handle_message ---

def test_handle_message_returns_string():
    result = _mod.handle_message("hello", "test-session-hm")
    assert isinstance(result, str)
    assert len(result) > 0


# --- generate_report ---

def test_generate_report_returns_markdown():
    result = _mod.generate_report("test-session-gr")
    assert "Migration Report" in result


# --- convert_schema_xml ---

SIMPLE_XML = """<schema name="t" version="1.6">
  <fieldType name="string" class="solr.StrField"/>
  <field name="id" type="string"/>
</schema>"""

def test_convert_schema_xml_valid():
    result = _mod.convert_schema_xml(SIMPLE_XML)
    parsed = json.loads(result)
    assert parsed["mappings"]["properties"]["id"]["type"] == "keyword"


def test_convert_schema_xml_invalid():
    with pytest.raises(ValueError):
        _mod.convert_schema_xml("not xml")


# --- convert_schema_json ---

def test_convert_schema_json_valid():
    schema = json.dumps({
        "schema": {
            "fieldTypes": [{"name": "string", "class": "solr.StrField"}],
            "fields": [{"name": "title", "type": "string"}],
        }
    })
    result = _mod.convert_schema_json(schema)
    parsed = json.loads(result)
    assert parsed["mappings"]["properties"]["title"]["type"] == "keyword"


# --- convert_query ---

def test_convert_query_match_all():
    result = _mod.convert_query("*:*")
    assert json.loads(result) == {"query": {"match_all": {}}}


def test_convert_query_field():
    result = _mod.convert_query("title:test")
    parsed = json.loads(result)
    assert "match" in parsed["query"]


# --- get_migration_checklist ---

def test_get_migration_checklist():
    result = _mod.get_migration_checklist()
    assert "PREPARATION" in result
    assert "CUTOVER" in result


# --- get_field_type_mapping_reference ---

def test_get_field_type_mapping_reference():
    result = _mod.get_field_type_mapping_reference()
    assert "| Solr Field Type | OpenSearch Type |" in result


# --- create_opensearch_index ---

def test_create_opensearch_index_invalid_json():
    result = _mod.create_opensearch_index("my-index", "{bad json")
    assert "Invalid mapping JSON" in result


def test_create_opensearch_index_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"acknowledged": True}).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = _mod.create_opensearch_index(
            "my-index", json.dumps({"mappings": {"properties": {}}})
        )
    assert "created successfully" in result


def test_create_opensearch_index_http_error(monkeypatch):
    import urllib.error
    http_err = urllib.error.HTTPError(
        url="http://localhost:9200/my-index",
        code=400,
        msg="Bad Request",
        hdrs={},
        fp=MagicMock(read=lambda: b'{"error":"already exists"}'),
    )
    with patch("urllib.request.urlopen", side_effect=http_err):
        result = _mod.create_opensearch_index(
            "my-index", json.dumps({"mappings": {}})
        )
    assert "HTTP 400" in result


def test_create_opensearch_index_connection_error(monkeypatch):
    import urllib.error
    url_err = urllib.error.URLError(reason="Connection refused")
    with patch("urllib.request.urlopen", side_effect=url_err):
        result = _mod.create_opensearch_index(
            "my-index", json.dumps({"mappings": {}})
        )
    assert "Could not connect" in result


def test_create_opensearch_index_uses_env_url(monkeypatch):
    monkeypatch.setenv("OPENSEARCH_URL", "http://myhost:9201")
    captured = {}

    def fake_urlopen(req):
        captured["url"] = req.full_url
        import urllib.error
        raise urllib.error.URLError(reason="Connection refused")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        _mod.create_opensearch_index("idx", json.dumps({}))

    assert "myhost:9201" in captured.get("url", "")


def test_create_opensearch_index_basic_auth(monkeypatch):
    monkeypatch.setenv("OPENSEARCH_USER", "admin")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "secret")
    captured_headers = {}

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"acknowledged": True}).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    original_urlopen = __builtins__

    def fake_urlopen(req):
        captured_headers.update(dict(req.headers))
        return mock_response

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        _mod.create_opensearch_index("idx", json.dumps({}))

    assert "Authorization" in captured_headers
