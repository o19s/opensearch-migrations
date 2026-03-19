#!/usr/bin/env python3
"""
Solr → OpenSearch Migration Script (Pass 1: Quick & Dirty)

Usage:
    python solr_to_opensearch.py \
        --solr-url http://minti9:8985/solr \
        --opensearch-url http://minti9:19200 \
        --collection corpusminder

    # Or just run with defaults (your current setup):
    python solr_to_opensearch.py

Requirements:
    pip install requests opensearch-py

What this does (Pass 1):
    1. Pulls the live schema from Solr's Schema API
    2. Auto-translates field types, copyFields, dynamic fields → OpenSearch mapping
    3. Creates the index on OpenSearch (drops existing if --recreate)
    4. Bulk reindexes ALL documents from Solr → OpenSearch (paginated)
    5. Runs smoke-test queries and prints results

What this does NOT do (future passes):
    - Custom analyzer chain translation (uses OpenSearch defaults for now)
    - Relevance tuning (BM25 defaults, no boost calibration)
    - Synonym/stopword file migration
    - Nested document handling
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
from opensearchpy import OpenSearch, helpers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("solr2os")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class MigrationConfig:
    solr_url: str = "http://minti9:8985/solr"
    opensearch_url: str = "http://minti9:19200"
    collection: str = "corpusminder"
    target_index: str = ""  # defaults to collection name
    batch_size: int = 500
    recreate_index: bool = False
    scroll_timeout: str = "5m"
    refresh_interval_during_bulk: str = "-1"
    dump_schema: bool = False  # dump raw Solr schema to JSON file
    dry_run: bool = False  # generate mapping but don't create index or reindex

    def __post_init__(self):
        if not self.target_index:
            self.target_index = self.collection


# ---------------------------------------------------------------------------
# Solr Schema Extraction
# ---------------------------------------------------------------------------

def solr_get(base_url: str, collection: str, endpoint: str) -> dict:
    """Hit a Solr API endpoint and return the JSON response."""
    url = f"{base_url}/{collection}/{endpoint}"
    log.debug(f"GET {url}")
    resp = requests.get(url, params={"wt": "json"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def pull_solr_schema(config: MigrationConfig) -> dict:
    """Pull the full schema from Solr's Schema API."""
    log.info(f"Pulling schema from Solr: {config.solr_url}/{config.collection}")

    schema = solr_get(config.solr_url, config.collection, "schema")
    fields = solr_get(config.solr_url, config.collection, "schema/fields")
    field_types = solr_get(config.solr_url, config.collection, "schema/fieldtypes")
    copy_fields = solr_get(config.solr_url, config.collection, "schema/copyfields")
    dynamic_fields = solr_get(config.solr_url, config.collection, "schema/dynamicfields")

    # Get document count
    count_resp = solr_get(config.solr_url, config.collection,
                          "select?q=*:*&rows=0&wt=json")
    doc_count = count_resp.get("response", {}).get("numFound", 0)

    # Get a sample document to see actual field usage
    sample_resp = solr_get(config.solr_url, config.collection,
                           "select?q=*:*&rows=3&wt=json")
    sample_docs = sample_resp.get("response", {}).get("docs", [])

    result = {
        "schema": schema.get("schema", {}),
        "fields": fields.get("fields", []),
        "fieldTypes": field_types.get("fieldTypes", []),
        "copyFields": copy_fields.get("copyFields", []),
        "dynamicFields": dynamic_fields.get("dynamicFields", []),
        "uniqueKey": schema.get("schema", {}).get("uniqueKey", "id"),
        "docCount": doc_count,
        "sampleDocs": sample_docs,
    }

    log.info(f"  Fields: {len(result['fields'])}")
    log.info(f"  Field types: {len(result['fieldTypes'])}")
    log.info(f"  Copy fields: {len(result['copyFields'])}")
    log.info(f"  Dynamic fields: {len(result['dynamicFields'])}")
    log.info(f"  Document count: {doc_count:,}")
    log.info(f"  Unique key: {result['uniqueKey']}")

    return result


# ---------------------------------------------------------------------------
# Schema Translation: Solr → OpenSearch
# ---------------------------------------------------------------------------

# Solr field type class → OpenSearch type mapping
# This is the Pass 1 "good enough" mapping — intentionally permissive
SOLR_TYPE_MAP = {
    # String / keyword types
    "solr.StrField": "keyword",
    "string": "keyword",

    # Text types (will use standard analyzer for Pass 1)
    "solr.TextField": "text",
    "text_general": "text",

    # Numeric types
    "solr.IntPointField": "integer",
    "solr.LongPointField": "long",
    "solr.FloatPointField": "float",
    "solr.DoublePointField": "double",
    "solr.TrieIntField": "integer",
    "solr.TrieLongField": "long",
    "solr.TrieFloatField": "float",
    "solr.TrieDoubleField": "double",

    # Newer point fields (Solr 7+)
    "pint": "integer",
    "plong": "long",
    "pfloat": "float",
    "pdouble": "double",

    # Date types
    "solr.DatePointField": "date",
    "solr.TrieDateField": "date",
    "pdate": "date",

    # Boolean
    "solr.BoolField": "boolean",
    "boolean": "boolean",

    # Geo types
    "solr.LatLonPointSpatialField": "geo_point",
    "solr.SpatialRecursivePrefixTreeFieldType": "geo_shape",
    "location": "geo_point",
    "location_rpt": "geo_shape",

    # Binary
    "solr.BinaryField": "binary",
}

# Solr dynamic field suffix → OpenSearch type
DYNAMIC_SUFFIX_MAP = {
    "_i": "integer",
    "_is": "integer",
    "_l": "long",
    "_ls": "long",
    "_f": "float",
    "_fs": "float",
    "_d": "double",
    "_ds": "double",
    "_s": "keyword",
    "_ss": "keyword",
    "_t": "text",
    "_ts": "text",
    "_txt": "text",
    "_b": "boolean",
    "_bs": "boolean",
    "_dt": "date",
    "_dts": "date",
    "_p": "geo_point",
    "_srpt": "geo_shape",
}


def resolve_solr_type(solr_field_type: str, field_types_lookup: dict) -> str:
    """Resolve a Solr field type name to an OpenSearch type."""
    # Direct match on type name
    if solr_field_type in SOLR_TYPE_MAP:
        return SOLR_TYPE_MAP[solr_field_type]

    # Look up the field type definition to get the class
    ft_def = field_types_lookup.get(solr_field_type, {})
    ft_class = ft_def.get("class", "")
    if ft_class in SOLR_TYPE_MAP:
        return SOLR_TYPE_MAP[ft_class]

    # If it's a TextField subclass, map to text
    if "Text" in ft_class or "text" in solr_field_type.lower():
        return "text"

    # Default fallback — keyword is safest (won't analyze unexpectedly)
    log.warning(f"  Unknown Solr type '{solr_field_type}' (class={ft_class}) → defaulting to 'keyword'")
    return "keyword"


def translate_schema(solr_schema: dict) -> dict:
    """Translate Solr schema to OpenSearch index mapping + settings."""

    # Build a lookup of field type name → definition
    field_types_lookup = {}
    for ft in solr_schema["fieldTypes"]:
        name = ft.get("name", "")
        field_types_lookup[name] = ft

    unique_key = solr_schema["uniqueKey"]

    # --- Translate explicit fields ---
    properties = {}
    copy_to_map = {}  # field_name → [dest_fields]

    # Build copy_to mapping from copyField rules
    for cf in solr_schema["copyFields"]:
        src = cf.get("source", "")  # note: Solr API uses "source" (not "src")
        if "source" not in cf:
            src = cf.get("src", "")  # some versions use "src"
        dest = cf.get("dest", "")
        if src and dest:
            copy_to_map.setdefault(src, []).append(dest)

    # Track which fields are copy_to targets (we need to declare them)
    copy_to_targets = set()
    for dests in copy_to_map.values():
        copy_to_targets.update(dests)

    # Fields to skip (Solr internal fields)
    skip_fields = {"_version_", "_root_", "_nest_path_"}

    for f in solr_schema["fields"]:
        name = f.get("name", "")
        if name in skip_fields:
            continue

        solr_type = f.get("type", "string")
        os_type = resolve_solr_type(solr_type, field_types_lookup)

        prop: dict[str, Any] = {"type": os_type}

        # Date format
        if os_type == "date":
            prop["format"] = "strict_date_optional_time||epoch_millis"

        # DocValues → doc_values (explicit for sorting/agg fields)
        if f.get("docValues") is True:
            prop["doc_values"] = True

        # Stored → store (only set if explicitly false, since OS defaults to true for _source)
        if f.get("stored") is False:
            prop["store"] = False

        # copy_to
        if name in copy_to_map:
            targets = copy_to_map[name]
            if len(targets) == 1:
                prop["copy_to"] = targets[0]
            else:
                prop["copy_to"] = targets

        # Multi-valued fields: OpenSearch handles arrays automatically,
        # no explicit mapping change needed

        properties[name] = prop

    # Ensure copy_to target fields exist in mapping
    for target in copy_to_targets:
        if target not in properties:
            # Catch-all copy targets are typically text fields
            properties[target] = {"type": "text"}
            log.info(f"  Added copy_to target field: {target} (type: text)")

    # --- Translate dynamic fields ---
    dynamic_templates = []
    for df in solr_schema["dynamicFields"]:
        pattern = df.get("name", "")
        solr_type = df.get("type", "string")
        os_type = resolve_solr_type(solr_type, field_types_lookup)

        # Convert Solr glob pattern to OpenSearch match pattern
        # Solr uses *_s, OpenSearch dynamic_templates use match: "*_s"
        template_name = pattern.replace("*", "dyn").replace("_", "_")

        template = {
            template_name: {
                "match": pattern,
                "mapping": {"type": os_type}
            }
        }

        if os_type == "date":
            template[template_name]["mapping"]["format"] = "strict_date_optional_time||epoch_millis"

        dynamic_templates.append(template)

    # --- Build final index definition ---
    index_def = {
        "settings": {
            "index": {
                "number_of_shards": 1,       # Pass 1 default; tune later
                "number_of_replicas": 0,      # Pass 1: no replicas for speed
                "refresh_interval": "1s",
            }
        },
        "mappings": {
            "dynamic": "true",  # Pass 1: permissive; tighten to "strict" in Pass 2
            "properties": properties,
        }
    }

    if dynamic_templates:
        index_def["mappings"]["dynamic_templates"] = dynamic_templates

    return index_def


# ---------------------------------------------------------------------------
# OpenSearch Index Creation
# ---------------------------------------------------------------------------

def get_opensearch_client(config: MigrationConfig) -> OpenSearch:
    """Create an OpenSearch client."""
    # Parse URL to extract host/port
    from urllib.parse import urlparse
    parsed = urlparse(config.opensearch_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 9200
    use_ssl = parsed.scheme == "https"

    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        use_ssl=use_ssl,
        verify_certs=False,  # Pass 1: permissive; fix for production
        ssl_show_warn=False,
    )
    # Verify connection
    info = client.info()
    log.info(f"Connected to OpenSearch: {info['version']['distribution']} {info['version']['number']}")
    return client


def create_index(client: OpenSearch, config: MigrationConfig, index_def: dict):
    """Create the OpenSearch index (optionally drop existing)."""
    index = config.target_index

    if client.indices.exists(index=index):
        if config.recreate_index:
            log.info(f"Dropping existing index: {index}")
            client.indices.delete(index=index)
        else:
            log.error(f"Index '{index}' already exists. Use --recreate to drop it first.")
            sys.exit(1)

    log.info(f"Creating index: {index}")
    log.info(f"  Shards: {index_def['settings']['index']['number_of_shards']}")
    log.info(f"  Replicas: {index_def['settings']['index']['number_of_replicas']}")
    log.info(f"  Properties: {len(index_def['mappings']['properties'])}")

    client.indices.create(index=index, body=index_def)
    log.info(f"Index '{index}' created successfully")


# ---------------------------------------------------------------------------
# Bulk Reindex: Solr → OpenSearch
# ---------------------------------------------------------------------------

def fetch_solr_docs(config: MigrationConfig, start: int, rows: int) -> list[dict]:
    """Fetch a batch of documents from Solr."""
    url = f"{config.solr_url}/{config.collection}/select"
    params = {
        "q": "*:*",
        "start": start,
        "rows": rows,
        "wt": "json",
        "sort": f"{pull_solr_schema.__defaults__}",  # we'll fix this
    }
    # Use the uniqueKey for stable sort during pagination
    params["sort"] = "id asc"  # safe default; adjust if uniqueKey differs

    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json().get("response", {}).get("docs", [])


def clean_doc_for_opensearch(doc: dict, unique_key: str) -> dict:
    """Remove Solr-internal fields and prepare doc for OpenSearch."""
    # Fields to strip
    strip_fields = {"_version_", "_root_", "_nest_path_", "score"}

    cleaned = {}
    for k, v in doc.items():
        if k in strip_fields:
            continue
        cleaned[k] = v

    return cleaned


def bulk_reindex(client: OpenSearch, config: MigrationConfig, unique_key: str):
    """Paginate through Solr and bulk-index into OpenSearch."""
    index = config.target_index

    # Disable refresh during bulk for throughput
    log.info(f"Setting refresh_interval to {config.refresh_interval_during_bulk} for bulk loading")
    client.indices.put_settings(
        index=index,
        body={"index": {"refresh_interval": config.refresh_interval_during_bulk}}
    )

    start = 0
    total_indexed = 0
    batch_num = 0
    t0 = time.time()

    while True:
        # Fetch batch from Solr
        url = f"{config.solr_url}/{config.collection}/select"
        params = {
            "q": "*:*",
            "start": start,
            "rows": config.batch_size,
            "wt": "json",
            "sort": f"{unique_key} asc",
        }
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json().get("response", {})
        docs = data.get("docs", [])
        total = data.get("numFound", 0)

        if not docs:
            break

        # Prepare bulk actions
        actions = []
        for doc in docs:
            cleaned = clean_doc_for_opensearch(doc, unique_key)
            doc_id = cleaned.pop(unique_key, None) if unique_key in cleaned else None

            action = {
                "_index": index,
                "_source": cleaned,
            }
            if doc_id is not None:
                action["_id"] = str(doc_id)
                # Keep the unique key in _source too
                action["_source"][unique_key] = doc_id

            actions.append(action)

        # Bulk index
        success, errors = helpers.bulk(client, actions, raise_on_error=False)
        total_indexed += success
        batch_num += 1

        elapsed = time.time() - t0
        rate = total_indexed / elapsed if elapsed > 0 else 0

        log.info(f"  Batch {batch_num}: indexed {success}/{len(docs)} "
                 f"(total: {total_indexed:,}/{total:,}, {rate:.0f} docs/sec)")

        if errors:
            log.warning(f"  {len(errors)} errors in batch {batch_num}")
            for err in errors[:3]:  # show first 3 errors
                log.warning(f"    {err}")

        start += config.batch_size

        if start >= total:
            break

    # Re-enable refresh
    log.info("Restoring refresh_interval to 1s")
    client.indices.put_settings(
        index=index,
        body={"index": {"refresh_interval": "1s"}}
    )

    # Force refresh to make all docs searchable
    client.indices.refresh(index=index)

    elapsed = time.time() - t0
    log.info(f"Bulk reindex complete: {total_indexed:,} documents in {elapsed:.1f}s "
             f"({total_indexed / elapsed:.0f} docs/sec)")

    return total_indexed


# ---------------------------------------------------------------------------
# Smoke Tests
# ---------------------------------------------------------------------------

def run_smoke_tests(client: OpenSearch, config: MigrationConfig, unique_key: str):
    """Run basic queries to verify the index is working."""
    index = config.target_index
    log.info("=" * 60)
    log.info("SMOKE TESTS")
    log.info("=" * 60)

    # Test 1: Document count
    count = client.count(index=index)["count"]
    log.info(f"[PASS] Document count: {count:,}")

    # Test 2: Match all with size=3
    result = client.search(index=index, body={
        "query": {"match_all": {}},
        "size": 3,
    })
    hits = result["hits"]["total"]["value"]
    log.info(f"[PASS] match_all returns {hits:,} total hits")
    for hit in result["hits"]["hits"][:3]:
        doc_id = hit["_id"]
        source_keys = list(hit["_source"].keys())[:5]
        log.info(f"  doc {doc_id}: fields={source_keys}...")

    # Test 3: Get mapping to verify field types
    mapping = client.indices.get_mapping(index=index)
    props = mapping[index]["mappings"]["properties"]
    log.info(f"[PASS] Index mapping has {len(props)} properties")

    # Test 4: Simple text search (if any text fields exist)
    text_fields = [k for k, v in props.items() if v.get("type") == "text"]
    if text_fields:
        test_field = text_fields[0]
        result = client.search(index=index, body={
            "query": {"match": {test_field: "test"}},
            "size": 3,
        })
        hits = result["hits"]["total"]["value"]
        log.info(f"[PASS] text search on '{test_field}' for 'test': {hits} hits")

    # Test 5: Terms aggregation on first keyword field
    keyword_fields = [k for k, v in props.items() if v.get("type") == "keyword" and k != unique_key]
    if keyword_fields:
        test_field = keyword_fields[0]
        result = client.search(index=index, body={
            "size": 0,
            "aggs": {
                "top_values": {
                    "terms": {"field": test_field, "size": 5}
                }
            }
        })
        buckets = result["aggregations"]["top_values"]["buckets"]
        log.info(f"[PASS] terms agg on '{test_field}': {len(buckets)} buckets")
        for b in buckets[:3]:
            log.info(f"  {b['key']}: {b['doc_count']}")

    log.info("=" * 60)
    log.info("Smoke tests complete!")
    log.info(f"Your index is ready to query at: {config.opensearch_url}/{index}/_search")
    log.info("=" * 60)


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(config: MigrationConfig, solr_schema: dict, index_def: dict,
                    docs_indexed: int) -> str:
    """Generate a migration report."""
    report_lines = [
        "# Solr → OpenSearch Migration Report (Pass 1)",
        f"",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Source:** {config.solr_url}/{config.collection}",
        f"**Target:** {config.opensearch_url}/{config.target_index}",
        f"",
        f"## Schema Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Solr fields | {len(solr_schema['fields'])} |",
        f"| Solr field types | {len(solr_schema['fieldTypes'])} |",
        f"| Solr copy fields | {len(solr_schema['copyFields'])} |",
        f"| Solr dynamic fields | {len(solr_schema['dynamicFields'])} |",
        f"| OpenSearch properties | {len(index_def['mappings']['properties'])} |",
        f"| Documents migrated | {docs_indexed:,} |",
        f"",
        f"## Field Mapping",
        f"",
        f"| Solr Field | Solr Type | OpenSearch Type | Notes |",
        f"|------------|-----------|-----------------|-------|",
    ]

    field_types_lookup = {ft["name"]: ft for ft in solr_schema["fieldTypes"]}
    for f in solr_schema["fields"]:
        name = f.get("name", "")
        if name.startswith("_") and name.endswith("_") and name != "_text_":
            continue
        solr_type = f.get("type", "?")
        os_prop = index_def["mappings"]["properties"].get(name, {})
        os_type = os_prop.get("type", "—")
        notes = []
        if "copy_to" in os_prop:
            notes.append(f"copy_to: {os_prop['copy_to']}")
        if os_type == "keyword" and "text" in solr_type.lower():
            notes.append("⚠️ text→keyword (Pass 2: add analyzer)")
        report_lines.append(
            f"| `{name}` | `{solr_type}` | `{os_type}` | {', '.join(notes)} |"
        )

    report_lines.extend([
        f"",
        f"## Pass 2 TODO",
        f"",
        f"- [ ] Review text fields — add proper analyzers (currently using defaults)",
        f"- [ ] Migrate synonym and stopword files",
        f"- [ ] Translate top query patterns to OpenSearch DSL",
        f"- [ ] Set `dynamic: strict` once all fields are mapped",
        f"- [ ] Tune shard count based on data size",
        f"- [ ] Add replicas for HA",
        f"- [ ] Set up relevance comparison (Quepid or manual)",
        f"- [ ] Compare BM25 results vs Solr's TF-IDF baseline",
        f"",
    ])

    return "\n".join(report_lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Solr → OpenSearch Migration (Pass 1: Quick & Dirty)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate with defaults (your current setup)
  python solr_to_opensearch.py

  # Migrate with explicit URLs
  python solr_to_opensearch.py \\
      --solr-url http://minti9:8985/solr \\
      --opensearch-url http://minti9:19200 \\
      --collection corpusminder

  # Recreate existing index
  python solr_to_opensearch.py --recreate

  # Dry run: generate mapping without creating index
  python solr_to_opensearch.py --dry-run

  # Dump Solr schema to JSON for inspection
  python solr_to_opensearch.py --dump-schema
        """
    )
    parser.add_argument("--solr-url", default="http://minti9:8985/solr",
                        help="Solr base URL (default: http://minti9:8985/solr)")
    parser.add_argument("--opensearch-url", default="http://minti9:19200",
                        help="OpenSearch URL (default: http://minti9:19200)")
    parser.add_argument("--collection", default="corpusminder",
                        help="Solr collection name (default: corpusminder)")
    parser.add_argument("--target-index", default="",
                        help="OpenSearch index name (default: same as collection)")
    parser.add_argument("--batch-size", type=int, default=500,
                        help="Batch size for bulk indexing (default: 500)")
    parser.add_argument("--recreate", action="store_true",
                        help="Drop and recreate OpenSearch index if it exists")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate mapping and report but don't create index or reindex")
    parser.add_argument("--dump-schema", action="store_true",
                        help="Dump raw Solr schema to JSON file")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = MigrationConfig(
        solr_url=args.solr_url,
        opensearch_url=args.opensearch_url,
        collection=args.collection,
        target_index=args.target_index or args.collection,
        batch_size=args.batch_size,
        recreate_index=args.recreate,
        dump_schema=args.dump_schema,
        dry_run=args.dry_run,
    )

    log.info("=" * 60)
    log.info("Solr → OpenSearch Migration (Pass 1)")
    log.info("=" * 60)
    log.info(f"Source:  {config.solr_url}/{config.collection}")
    log.info(f"Target:  {config.opensearch_url}/{config.target_index}")
    log.info("")

    # Step 1: Pull Solr schema
    solr_schema = pull_solr_schema(config)

    if config.dump_schema:
        dump_path = f"{config.collection}_solr_schema.json"
        with open(dump_path, "w") as f:
            json.dump(solr_schema, f, indent=2, default=str)
        log.info(f"Solr schema dumped to: {dump_path}")

    # Step 2: Translate to OpenSearch mapping
    log.info("")
    log.info("Translating schema to OpenSearch mapping...")
    index_def = translate_schema(solr_schema)

    # Save the generated mapping for review
    mapping_path = f"{config.target_index}_opensearch_mapping.json"
    with open(mapping_path, "w") as f:
        json.dump(index_def, f, indent=2)
    log.info(f"OpenSearch mapping saved to: {mapping_path}")

    if config.dry_run:
        log.info("")
        log.info("DRY RUN: Stopping before index creation. Review the mapping file above.")
        report = generate_report(config, solr_schema, index_def, 0)
        report_path = f"{config.target_index}_migration_report.md"
        with open(report_path, "w") as f:
            f.write(report)
        log.info(f"Migration report saved to: {report_path}")
        return

    # Step 3: Create OpenSearch index
    log.info("")
    os_client = get_opensearch_client(config)
    create_index(os_client, config, index_def)

    # Step 4: Bulk reindex
    log.info("")
    log.info("Starting bulk reindex from Solr → OpenSearch...")
    docs_indexed = bulk_reindex(os_client, config, solr_schema["uniqueKey"])

    # Step 5: Smoke tests
    log.info("")
    run_smoke_tests(os_client, config, solr_schema["uniqueKey"])

    # Step 6: Generate report
    report = generate_report(config, solr_schema, index_def, docs_indexed)
    report_path = f"{config.target_index}_migration_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    log.info(f"Migration report saved to: {report_path}")

    log.info("")
    log.info("Pass 1 complete! Next steps:")
    log.info("  1. Review the mapping file and migration report")
    log.info("  2. Run your real queries against OpenSearch and compare results")
    log.info(f"  3. Re-run with --recreate after fixing issues in Pass 2")


if __name__ == "__main__":
    main()