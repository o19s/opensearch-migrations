"""
Read-only client for inspecting a running Apache Solr instance.

Wraps Solr's Admin and Schema HTTP APIs to gather migration-relevant
data: schema definitions, index statistics, query handler metrics,
cache performance, and cluster topology.

All methods are stateless HTTP GETs — no writes, no session state.
Uses only ``urllib.request`` (stdlib) to avoid extra dependencies.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List


class SolrInspector:
    """Read-only inspector for a running Solr instance."""

    def __init__(self, solr_url: str = "http://localhost:8983") -> None:
        self.solr_url = solr_url.rstrip("/")

    def _get_json(self, path: str, timeout: int = 10) -> Dict[str, Any]:
        """HTTP GET a Solr endpoint and return parsed JSON."""
        url = f"{self.solr_url}{path}"
        sep = "&" if "?" in path else "?"
        url += f"{sep}wt=json"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Solr returned HTTP {e.code} for {url}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Cannot reach Solr at {url}: {e.reason}"
            ) from e

    # ------------------------------------------------------------------
    # Schema API
    # ------------------------------------------------------------------

    def get_schema(self, collection: str) -> Dict[str, Any]:
        """Fetch the live schema for a collection.

        Returns the full schema including fields, fieldTypes,
        copyFields, and dynamicFields.
        """
        return self._get_json(f"/solr/{collection}/schema")

    # ------------------------------------------------------------------
    # Metrics API
    # ------------------------------------------------------------------

    def get_metrics(self, group: str = "core") -> Dict[str, Any]:
        """Fetch Solr metrics for a given group.

        Groups: core, jvm, jetty, node.
        Returns cache stats, query/update rates, JVM heap, etc.
        """
        return self._get_json(f"/solr/admin/metrics?group={group}")

    # ------------------------------------------------------------------
    # MBeans API
    # ------------------------------------------------------------------

    def get_mbeans(
        self, collection: str, category: str = "QUERYHANDLER"
    ) -> Dict[str, Any]:
        """Fetch MBean stats for a collection.

        Categories: QUERYHANDLER, UPDATEHANDLER, SEARCHER, CACHE, etc.
        Returns request counts, latency, error rates per handler.
        """
        return self._get_json(
            f"/solr/{collection}/admin/mbeans?stats=true&cat={category}"
        )

    # ------------------------------------------------------------------
    # Luke API
    # ------------------------------------------------------------------

    def get_luke(self, collection: str) -> Dict[str, Any]:
        """Fetch index statistics for a collection.

        Returns numDocs, maxDoc, field cardinality, top terms, etc.
        """
        return self._get_json(f"/solr/{collection}/admin/luke?numTerms=0")

    # ------------------------------------------------------------------
    # Collections / Cores API
    # ------------------------------------------------------------------

    def list_collections(self) -> List[str]:
        """List all collections (SolrCloud) or cores (standalone).

        Tries the Collections API first (SolrCloud), falls back to
        the Core Admin API for standalone Solr.
        """
        try:
            data = self._get_json(
                "/solr/admin/collections?action=LIST"
            )
            return data.get("collections", [])
        except RuntimeError:
            # Not SolrCloud — fall back to core admin
            data = self._get_json("/solr/admin/cores")
            return list(data.get("status", {}).keys())

    # ------------------------------------------------------------------
    # System Info API
    # ------------------------------------------------------------------

    def get_system_info(self) -> Dict[str, Any]:
        """Fetch Solr system information.

        Returns Solr/Lucene version, JVM details, heap usage,
        CPU count, and OS info.
        """
        return self._get_json("/solr/admin/info/system")
