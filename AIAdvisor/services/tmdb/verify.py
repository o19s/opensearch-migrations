"""Verify Solr TMDB is running and loaded.

Requires: bash setup.sh (from this directory) before running.
"""

import json
import os
import urllib.request

SOLR_URL = os.environ.get("SOLR_URL", "http://localhost:38984")


def solr_get(path):
    return json.load(urllib.request.urlopen(f"{SOLR_URL}{path}"))


def test_solr_reachable():
    data = solr_get("/solr/tmdb/admin/ping?wt=json")
    assert data["status"] == "OK"


def test_tmdb_collection_exists():
    data = solr_get("/solr/admin/cores?action=STATUS&wt=json")
    assert "tmdb" in data["status"]


def test_tmdb_has_documents():
    data = solr_get("/solr/tmdb/select?q=*:*&rows=0&wt=json")
    assert data["response"]["numFound"] > 5000


def test_schema_has_text_heavy_fields():
    data = solr_get("/solr/tmdb/schema/fields?wt=json")
    names = [f["name"] for f in data["fields"]]
    for field in ["title", "overview", "cast", "directors", "genres"]:
        assert field in names, f"missing field: {field}"


def test_schema_has_copy_fields():
    data = solr_get("/solr/tmdb/schema/copyfields?wt=json")
    sources = [cf["source"] for cf in data["copyFields"]]
    assert "title" in sources, "title should be a copyField source"
