"""
Converts Apache Solr query syntax to OpenSearch Query DSL.

Supported Solr query patterns
------------------------------
* ``field:value``                    → ``match`` query
* ``field:"phrase value"``           → ``match_phrase`` query
* ``field:val*`` / ``field:*val``    → ``wildcard`` query
* ``field:[low TO high]``            → ``range`` query (inclusive)
* ``field:{low TO high}``            → ``range`` query (exclusive)
* ``field:[low TO *]`` / ``field:[* TO high]`` → open-ended range
* ``+term`` / ``-term``              → boolean ``must`` / ``must_not``
* ``term1 AND term2``                → boolean ``must``
* ``term1 OR term2``                 → boolean ``should``
* ``NOT term``                       → boolean ``must_not``
* ``*:*``                            → ``match_all``
* Plain ``term`` (no field)          → ``query_string``

Limitations
-----------
* Nested parentheses grouping is limited; complex nested expressions will
  fall back to a ``query_string`` query so that no information is lost.
* Boost values (``^n``) are preserved for fielded term, phrase, and wildcard
  clauses, but not for every Solr query form.
* Fuzzy operators (``~``) are not converted and fall back to
  ``query_string``.
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

_FIELD_VALUE_RE = re.compile(
    r'^(?P<field>\w+):(?P<value>.+)$', re.DOTALL
)
_PHRASE_RE = re.compile(r'^"(?P<phrase>[^"]+)"$')
_WILDCARD_RE = re.compile(r'[*?]')
_RANGE_RE = re.compile(
    r'^(?P<open>[\[{])\s*(?P<low>\S+)\s+TO\s+(?P<high>\S+)\s*(?P<close>[\]}])$'
)
_BOOST_RE = re.compile(r'\^[\d.]+$')


def _split_boost(value: str) -> tuple[str, float | None]:
    match = _BOOST_RE.search(value.strip())
    if not match:
        return value.strip(), None
    boost = float(match.group(0)[1:])
    return value[: match.start()].strip(), boost


def _build_term_query(field: str, raw_value: str) -> dict[str, Any]:
    """Build a single field→value query clause."""
    value, boost = _split_boost(raw_value)

    # Phrase
    phrase_match = _PHRASE_RE.match(value)
    if phrase_match:
        body: Any = phrase_match.group("phrase")
        if boost is not None:
            body = {"query": phrase_match.group("phrase"), "boost": boost}
        return {"match_phrase": {field: body}}

    # Range
    range_match = _RANGE_RE.match(value)
    if range_match:
        low = range_match.group("low")
        high = range_match.group("high")
        inclusive_low = range_match.group("open") == "["
        inclusive_high = range_match.group("close") == "]"

        range_clause: dict[str, Any] = {}
        if low != "*":
            range_clause["gte" if inclusive_low else "gt"] = _coerce_number(low)
        if high != "*":
            range_clause["lte" if inclusive_high else "lt"] = _coerce_number(high)

        return {"range": {field: range_clause}}

    # Wildcard
    if _WILDCARD_RE.search(value):
        body: Any = value.lower()
        if boost is not None:
            body = {"value": value.lower(), "boost": boost}
        return {"wildcard": {field: body}}

    # Plain term → match
    body: Any = value
    if boost is not None:
        body = {"query": value, "boost": boost}
    return {"match": {field: body}}


def _coerce_number(value: str) -> int | float | str:
    """Try to return a numeric type; fall back to string."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


# ---------------------------------------------------------------------------
# Boolean splitting helpers
# ---------------------------------------------------------------------------

def _split_boolean(query: str) -> tuple[str, list[str]] | None:
    """Split a query on a top-level AND or OR operator.

    Returns ``(operator, [parts])`` or ``None`` if no top-level operator is
    found.  Only splits on AND/OR that are not inside parentheses or quotes.
    """
    depth = 0
    in_quote = False
    i = 0
    while i < len(query):
        ch = query[i]
        if ch == '"':
            in_quote = not in_quote
        elif not in_quote:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif depth == 0:
                # Check for AND / OR
                for op in (' AND ', ' OR '):
                    if query[i:].upper().startswith(op):
                        left = query[:i].strip()
                        right = query[i + len(op):].strip()
                        return op.strip(), [left, right]
        i += 1
    return None


def _build_must_not(inner_query: str) -> dict[str, Any]:
    """Wrap a query string in a must_not boolean."""
    inner = _convert_simple(inner_query)
    return {"bool": {"must_not": [inner]}}


def _convert_simple(query: str) -> dict[str, Any]:
    """Convert a single (non-compound) Solr query clause to OpenSearch DSL."""
    query = query.strip()

    # match_all
    if query in ("*:*", "*"):
        return {"match_all": {}}

    # NOT prefix
    if query.upper().startswith("NOT "):
        return _build_must_not(query[4:].strip())

    # +/- prefix (required / prohibited)
    if query.startswith("+") or query.startswith("-"):
        must: list[dict[str, Any]] = []
        must_not: list[dict[str, Any]] = []
        # Split on space-separated +/- tokens
        tokens = _tokenize_prefixed(query)
        for sign, tok in tokens:
            clause = _convert_simple(tok)
            if sign == "+":
                must.append(clause)
            else:
                must_not.append(clause)
        bool_query: dict[str, Any] = {}
        if must:
            bool_query["must"] = must
        if must_not:
            bool_query["must_not"] = must_not
        return {"bool": bool_query}

    # field:value
    fv_match = _FIELD_VALUE_RE.match(query)
    if fv_match:
        field = fv_match.group("field")
        value = fv_match.group("value")
        return _build_term_query(field, value)

    # Bare term with no field — use query_string
    return {"query_string": {"query": query}}


def _tokenize_prefixed(query: str) -> list[tuple[str, str]]:
    """Break a ``+a -b +c`` style query into ``[(sign, term), …]``."""
    tokens: list[tuple[str, str]] = []
    # Split respecting quoted strings
    parts = re.findall(r'[+-](?:"[^"]*"|\S+)', query)
    for part in parts:
        sign = "+" if part[0] == "+" else "-"
        tokens.append((sign, part[1:].strip()))
    return tokens


class QueryConverter:
    """Converts Solr query strings to OpenSearch Query DSL dicts.

    Usage::

        converter = QueryConverter()

        # Simple field query
        dsl = converter.convert("title:opensearch")

        # Range query
        dsl = converter.convert("price:[10 TO 100]")

        # Boolean query
        dsl = converter.convert("title:search AND category:docs")

        print(json.dumps(dsl, indent=2))
    """

    def convert(self, solr_query: str) -> dict[str, Any]:
        """Convert a Solr query string to an OpenSearch Query DSL dict.

        The returned dict is the full ``query`` object, i.e. it can be used
        directly as the value of the ``"query"`` key in an OpenSearch search
        request body.

        Args:
            solr_query: A Solr query string (``q`` parameter value).

        Returns:
            An OpenSearch Query DSL dict.

        Raises:
            ValueError: If ``solr_query`` is empty.
        """
        if not solr_query or not solr_query.strip():
            raise ValueError("solr_query must not be empty")

        query = solr_query.strip()

        # Remove wrapping parentheses if they span the whole expression.
        query = _unwrap_parens(query)

        # Top-level AND
        result = _split_boolean(query)
        if result:
            operator, parts = result
            if operator == "AND":
                clauses = [self.convert(p)["query"] for p in parts]
                return {"query": {"bool": {"must": clauses}}}
            else:  # OR
                clauses = [self.convert(p)["query"] for p in parts]
                return {"query": {"bool": {"should": clauses, "minimum_should_match": 1}}}

        return {"query": _convert_simple(query)}

    def convert_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """Convert a minimal Solr request-parameter dict to an OpenSearch body.

        This is intentionally a placeholder-level request converter. It handles
        a narrow but useful subset of common migration cases:

        - ``q`` with ``defType=edismax`` and ``qf`` -> ``multi_match``
        - ``fq`` -> ``bool.filter``
        - ``facet.field`` -> ``terms`` aggregation
        - ``hl.*`` -> ``highlight``
        - ``rows`` -> ``size``
        - ``sort`` -> ``sort``

        It is not a full Solr request parser and should be treated as interim
        scaffolding for future, richer conversion logic.
        """
        q = str(params.get("q", "*:*")).strip()
        body: dict[str, Any] = {}

        if params.get("defType") == "edismax":
            body["query"] = self._convert_edismax_placeholder(
                q=q,
                qf=params.get("qf", ""),
            )
        else:
            body["query"] = self.convert(q)["query"]

        filter_clauses = self._convert_filter_queries_placeholder(params.get("fq"))
        if filter_clauses:
            existing_query = body["query"]
            body["query"] = {
                "bool": {
                    "must": [existing_query],
                    "filter": filter_clauses,
                }
            }

        aggs = self._convert_facets_placeholder(params)
        if aggs:
            body["aggs"] = aggs

        highlight = self._convert_highlight_placeholder(params)
        if highlight:
            body["highlight"] = highlight

        size = self._convert_size_placeholder(params.get("rows"))
        if size is not None:
            body["size"] = size

        sort = self._convert_sort_placeholder(params.get("sort"))
        if sort:
            body["sort"] = sort

        return body

    def _convert_edismax_placeholder(self, *, q: str, qf: Any) -> dict[str, Any]:
        fields: list[str] = []
        if isinstance(qf, str):
            fields = [part for part in qf.split() if part]
        elif isinstance(qf, list):
            fields = [str(part) for part in qf if str(part).strip()]

        return {
            "multi_match": {
                "query": q,
                "fields": fields or ["_all"],
                "type": "best_fields",
            }
        }

    def _convert_filter_queries_placeholder(self, fq: Any) -> list[dict[str, Any]]:
        if fq is None:
            return []
        fq_items = fq if isinstance(fq, list) else [fq]
        filters = []
        for item in fq_items:
            filters.append(self._convert_filter_clause_placeholder(str(item)))
        return filters

    def _convert_filter_clause_placeholder(self, fq_item: str) -> dict[str, Any]:
        query = fq_item.strip()
        field_match = _FIELD_VALUE_RE.match(query)
        if not field_match:
            return self.convert(query)["query"]

        field = field_match.group("field")
        value = field_match.group("value").strip()

        range_match = _RANGE_RE.match(value)
        if range_match:
            return self.convert(query)["query"]

        phrase_match = _PHRASE_RE.match(value)
        if phrase_match or _WILDCARD_RE.search(value):
            return self.convert(query)["query"]

        if any(op in value.upper() for op in (" AND ", " OR ")) or value.startswith("("):
            return self.convert(query)["query"]

        coerced = _coerce_boolean_or_number(value)
        return {"term": {field: coerced}}

    def _convert_facets_placeholder(self, params: dict[str, Any]) -> dict[str, Any]:
        facet_field = params.get("facet.field")
        if not facet_field:
            return {}

        fields = facet_field if isinstance(facet_field, list) else [facet_field]
        aggs = {}
        for field in fields:
            field_name = str(field).strip()
            if not field_name:
                continue
            agg_name = field_name.replace(".", "_")
            aggs[agg_name] = {
                "terms": {
                    "field": f"{field_name}.keyword",
                }
            }
        return aggs

    def _convert_highlight_placeholder(self, params: dict[str, Any]) -> dict[str, Any]:
        hl_value = params.get("hl")
        if str(hl_value).lower() not in {"true", "on", "1"}:
            return {}

        fields_param = params.get("hl.fl")
        if not fields_param:
            return {}

        raw_fields = fields_param if isinstance(fields_param, list) else [fields_param]
        field_names: list[str] = []
        for item in raw_fields:
            for part in str(item).split(","):
                field_name = part.strip()
                if field_name:
                    field_names.append(field_name)

        if not field_names:
            return {}

        highlight: dict[str, Any] = {
            "fields": {field_name: {} for field_name in field_names}
        }

        pre_tag = params.get("hl.simple.pre")
        post_tag = params.get("hl.simple.post")
        if pre_tag and post_tag:
            highlight["pre_tags"] = [str(pre_tag)]
            highlight["post_tags"] = [str(post_tag)]

        highlight_query = params.get("hl.q")
        if highlight_query:
            highlight["highlight_query"] = self.convert(str(highlight_query))["query"]

        return highlight

    def _convert_size_placeholder(self, rows: Any) -> int | None:
        if rows is None:
            return None
        try:
            return int(str(rows).strip())
        except ValueError:
            return None

    def _convert_sort_placeholder(self, sort_value: Any) -> list[dict[str, Any]]:
        if not sort_value:
            return []

        sort_items = sort_value if isinstance(sort_value, list) else [sort_value]
        translated = []
        for item in sort_items:
            raw = str(item).strip()
            if not raw:
                continue
            parts = raw.split()
            field = parts[0]
            order = parts[1].lower() if len(parts) > 1 else "asc"
            if field == "score":
                translated.append({"_score": {"order": order}})
            else:
                translated.append({field: {"order": order}})
        return translated


def _unwrap_parens(query: str) -> str:
    """Remove a single layer of matching outer parentheses if present."""
    query = query.strip()
    if not (query.startswith("(") and query.endswith(")")):
        return query
    # Verify the opening paren actually matches the last char.
    depth = 0
    for i, ch in enumerate(query):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and i < len(query) - 1:
            # Closing paren found before end — outer parens are not a single
            # group, don't strip.
            return query
    return query[1:-1].strip()


def _coerce_boolean_or_number(value: str) -> bool | int | float | str:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return _coerce_number(value)
