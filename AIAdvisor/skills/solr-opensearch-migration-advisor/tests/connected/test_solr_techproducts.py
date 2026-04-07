"""Verify SolrCloud TechProducts is running and loaded.

Requires: docker compose up -d (from this directory) before running.
"""

import json
import os
import urllib.request

SOLR_URL = os.environ.get("SOLR_URL", "http://localhost:38983")


def solr_get(path):
    return json.load(urllib.request.urlopen(f"{SOLR_URL}{path}"))


def test_solr_reachable():
    data = solr_get("/solr/techproducts/admin/ping?wt=json")
    assert data["status"] == "OK"


def test_techproducts_collection_exists():
    data = solr_get("/solr/admin/collections?action=LIST&wt=json")
    assert "techproducts" in data["collections"]


def test_techproducts_has_documents():
    data = solr_get("/solr/techproducts/select?q=*:*&rows=0&wt=json")
    assert data["response"]["numFound"] > 0


def test_schema_has_expected_fields():
    data = solr_get("/solr/techproducts/schema/fields?wt=json")
    names = [f["name"] for f in data["fields"]]
    for field in ["id", "name", "manu", "cat"]:
        assert field in names
