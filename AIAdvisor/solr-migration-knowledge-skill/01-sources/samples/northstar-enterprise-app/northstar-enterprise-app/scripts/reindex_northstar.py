#!/usr/bin/env python3
"""
Create a first-pass OpenSearch index and bulk-load the Northstar sample corpus.
"""

import argparse
import json
import sys
from pathlib import Path

import requests


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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
    response = requests.put(
        f"{base_url}/{index_name}",
        json=mapping,
        timeout=30,
    )
    response.raise_for_status()


def update_aliases(base_url: str, index_name: str, read_alias: str, write_alias: str) -> None:
    payload = {
        "actions": [
            {"remove": {"index": "*", "alias": read_alias, "ignore_unavailable": True}},
            {"remove": {"index": "*", "alias": write_alias, "ignore_unavailable": True}},
            {"add": {"index": index_name, "alias": read_alias}},
            {"add": {"index": index_name, "alias": write_alias, "is_write_index": True}},
        ]
    }
    response = requests.post(f"{base_url}/_aliases", json=payload, timeout=30)
    response.raise_for_status()


def bulk_index(base_url: str, write_alias: str, documents: list[dict]) -> dict:
    lines: list[str] = []
    for document in documents:
        doc_id = document["id"]
        lines.append(json.dumps({"index": {"_index": write_alias, "_id": doc_id}}))
        lines.append(json.dumps(document))

    payload = "\n".join(lines) + "\n"
    response = requests.post(
        f"{base_url}/_bulk",
        data=payload,
        headers={"Content-Type": "application/x-ndjson"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def count_documents(base_url: str, read_alias: str) -> int:
    response = requests.get(f"{base_url}/{read_alias}/_count", timeout=30)
    response.raise_for_status()
    return int(response.json()["count"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Northstar sample reindex helper")
    parser.add_argument("--opensearch-url", default="http://localhost:9200")
    parser.add_argument("--index-name", default="atlas-search-v1")
    parser.add_argument("--read-alias", default="atlas-search-read")
    parser.add_argument("--write-alias", default="atlas-search-write")
    parser.add_argument("--create-index", action="store_true")
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    app_root = Path(__file__).resolve().parent.parent
    mapping_path = app_root / "src" / "main" / "resources" / "opensearch" / "atlas-index.json"
    docs_path = app_root / "src" / "main" / "resources" / "samples" / "northstar-sample-docs.json"

    mapping = load_json(mapping_path)
    documents = load_json(docs_path)

    if not isinstance(documents, list):
        print("Sample document file must contain a JSON array", file=sys.stderr)
        return 1

    if args.recreate and index_exists(args.opensearch_url, args.index_name):
        delete_index(args.opensearch_url, args.index_name)

    if args.create_index:
        if index_exists(args.opensearch_url, args.index_name):
            print(f"Index {args.index_name} already exists")
        else:
            create_index(args.opensearch_url, args.index_name, mapping)
        update_aliases(args.opensearch_url, args.index_name, args.read_alias, args.write_alias)

    result = bulk_index(args.opensearch_url, args.write_alias, documents)
    count = count_documents(args.opensearch_url, args.read_alias)

    print(
        json.dumps(
            {
                "index": args.index_name,
                "read_alias": args.read_alias,
                "write_alias": args.write_alias,
                "bulk_errors": result.get("errors"),
                "items_indexed": len(result.get("items", [])),
                "document_count": count,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
