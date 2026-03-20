#!/usr/bin/env python3
"""
Bootstrap the Northstar sample corpus into the repo-level OpenSearch and Elasticsearch demos.
"""

import argparse
import json
import sys
from pathlib import Path

import requests


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def request_json(method: str, url: str, **kwargs) -> object:
    response = requests.request(method, url, timeout=60, **kwargs)
    response.raise_for_status()
    if response.content:
        return response.json()
    return {}


def index_exists(base_url: str, index_name: str) -> bool:
    response = requests.head(f"{base_url}/{index_name}", timeout=30)
    if response.status_code == 200:
        return True
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return False


def delete_index(base_url: str, index_name: str) -> None:
    response = requests.delete(f"{base_url}/{index_name}", timeout=30)
    if response.status_code not in (200, 404):
        response.raise_for_status()


def create_index(base_url: str, index_name: str, mapping: dict) -> None:
    request_json("PUT", f"{base_url}/{index_name}", json=mapping)


def update_aliases(base_url: str, index_name: str, read_alias: str, write_alias: str) -> None:
    payload = {
        "actions": [
            {"remove": {"index": "*", "alias": read_alias, "ignore_unavailable": True}},
            {"remove": {"index": "*", "alias": write_alias, "ignore_unavailable": True}},
            {"add": {"index": index_name, "alias": read_alias}},
            {"add": {"index": index_name, "alias": write_alias, "is_write_index": True}},
        ]
    }
    request_json("POST", f"{base_url}/_aliases", json=payload)


def bulk_index(base_url: str, write_alias: str, documents: list[dict]) -> dict:
    lines: list[str] = []
    for document in documents:
        lines.append(json.dumps({"index": {"_index": write_alias, "_id": document["id"]}}))
        lines.append(json.dumps(document))

    response = requests.post(
        f"{base_url}/_bulk",
        data="\n".join(lines) + "\n",
        headers={"Content-Type": "application/x-ndjson"},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def count_documents(base_url: str, read_alias: str) -> int:
    payload = request_json("GET", f"{base_url}/{read_alias}/_count")
    return int(payload["count"])


def bootstrap_engine(
    engine_name: str,
    base_url: str,
    index_name: str,
    read_alias: str,
    write_alias: str,
    mapping: dict,
    documents: list[dict],
    recreate: bool,
) -> dict:
    if recreate and index_exists(base_url, index_name):
        delete_index(base_url, index_name)

    if not index_exists(base_url, index_name):
        create_index(base_url, index_name, mapping)

    update_aliases(base_url, index_name, read_alias, write_alias)
    result = bulk_index(base_url, write_alias, documents)
    count = count_documents(base_url, read_alias)

    return {
        "engine": engine_name,
        "base_url": base_url,
        "index": index_name,
        "read_alias": read_alias,
        "write_alias": write_alias,
        "bulk_errors": result.get("errors"),
        "items_indexed": len(result.get("items", [])),
        "document_count": count,
    }


def resolve_demo_app_root(repo_root: Path) -> Path:
    return repo_root / "01-sources" / "samples" / "northstar-enterprise-app" / "northstar-enterprise-app"


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the repo-level search demo engines")
    parser.add_argument(
        "--engine",
        choices=["opensearch", "elasticsearch", "both"],
        default="both",
    )
    parser.add_argument("--opensearch-url", default="http://localhost:9200")
    parser.add_argument("--elasticsearch-url", default="http://localhost:9201")
    parser.add_argument("--index-name", default="atlas-search-v1")
    parser.add_argument("--read-alias", default="atlas-search-read")
    parser.add_argument("--write-alias", default="atlas-search-write")
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    app_root = resolve_demo_app_root(repo_root)
    mapping_path = app_root / "src" / "main" / "resources" / "opensearch" / "atlas-index.json"
    docs_path = app_root / "src" / "main" / "resources" / "samples" / "northstar-sample-docs.json"

    mapping = load_json(mapping_path)
    documents = load_json(docs_path)
    if not isinstance(documents, list):
        print("Sample document file must contain a JSON array", file=sys.stderr)
        return 1

    results = []
    if args.engine in ("opensearch", "both"):
        results.append(
            bootstrap_engine(
                "opensearch",
                args.opensearch_url,
                args.index_name,
                args.read_alias,
                args.write_alias,
                mapping,
                documents,
                args.recreate,
            )
        )

    if args.engine in ("elasticsearch", "both"):
        results.append(
            bootstrap_engine(
                "elasticsearch",
                args.elasticsearch_url,
                args.index_name,
                args.read_alias,
                args.write_alias,
                mapping,
                documents,
                args.recreate,
            )
        )

    print(json.dumps({"results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
