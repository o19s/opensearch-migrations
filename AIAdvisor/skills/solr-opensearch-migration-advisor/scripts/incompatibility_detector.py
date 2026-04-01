"""
Detects incompatibilities between a Solr schema and OpenSearch.

Analyzes field types, copy fields, analyzers, spatial types, and dynamic
fields to produce a list of :class:`~storage.Incompatibility` objects that
the report generator can surface.

Two public entry points:
- :func:`detect_incompatibilities_xml` for ``schema.xml`` content
- :func:`detect_incompatibilities_json` for Solr Schema API JSON dicts
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from storage import Incompatibility


# ── Internal normalised schema representation ────────────────────────────

@dataclass
class _FieldTypeDef:
    name: str
    class_name: str
    filters: list[str] = field(default_factory=list)


@dataclass
class _FieldDef:
    name: str
    type_name: str
    multi_valued: bool = False


@dataclass
class _CopyFieldDef:
    source: str
    dest: str


@dataclass
class _DynamicFieldDef:
    pattern: str
    type_name: str


@dataclass
class _NormalizedSchema:
    field_types: list[_FieldTypeDef] = field(default_factory=list)
    fields: list[_FieldDef] = field(default_factory=list)
    copy_fields: list[_CopyFieldDef] = field(default_factory=list)
    dynamic_fields: list[_DynamicFieldDef] = field(default_factory=list)


# ── Constants ────────────────────────────────────────────────────────────

_DEPRECATED_TRIE_CLASSES = {
    "solr.TrieIntField", "TrieIntField",
    "solr.TrieDateField", "TrieDateField",
    "solr.TrieLongField", "TrieLongField",
    "solr.TrieFloatField", "TrieFloatField",
    "solr.TrieDoubleField", "TrieDoubleField",
}

_SPATIAL_CLASSES = {
    "solr.LatLonPointSpatialField", "LatLonPointSpatialField",
    "solr.SpatialRecursivePrefixTreeFieldType",
    "SpatialRecursivePrefixTreeFieldType",
}

_UNSUPPORTED_CLASSES = {
    "solr.ICUCollationField", "ICUCollationField",
    "solr.EnumField", "EnumField",
    "solr.EnumFieldType", "EnumFieldType",
    "solr.ExternalFileField", "ExternalFileField",
    "solr.PreAnalyzedField", "PreAnalyzedField",
    "solr.CurrencyFieldType", "CurrencyFieldType",
    "solr.CurrencyField", "CurrencyField",
}

# Analyzer filters that are safe and need no special attention in OpenSearch.
_SAFE_FILTERS = {
    "solr.StandardTokenizerFactory", "StandardTokenizerFactory",
    "solr.LowerCaseFilterFactory", "LowerCaseFilterFactory",
    "solr.StopFilterFactory", "StopFilterFactory",
    "solr.PorterStemFilterFactory", "PorterStemFilterFactory",
    "solr.EnglishPossessiveFilterFactory", "EnglishPossessiveFilterFactory",
    "solr.KeywordTokenizerFactory", "KeywordTokenizerFactory",
    "solr.WhitespaceTokenizerFactory", "WhitespaceTokenizerFactory",
    "solr.ASCIIFoldingFilterFactory", "ASCIIFoldingFilterFactory",
    "solr.ClassicTokenizerFactory", "ClassicTokenizerFactory",
    "solr.PatternTokenizerFactory", "PatternTokenizerFactory",
}

# Filters that deserve a specific, helpful recommendation.
_NOTABLE_FILTERS: dict[str, tuple[str, str]] = {
    "DoubleMetaphoneFilterFactory": (
        "uses DoubleMetaphoneFilterFactory — requires the analysis-phonetic "
        "plugin in OpenSearch",
        "Install the analysis-phonetic plugin and configure the phonetic "
        "token filter. Verify encoder settings match.",
    ),
    "PhoneticFilterFactory": (
        "uses PhoneticFilterFactory — requires the analysis-phonetic plugin "
        "in OpenSearch",
        "Install the analysis-phonetic plugin and configure the phonetic "
        "token filter.",
    ),
    "EdgeNGramFilterFactory": (
        "uses EdgeNGramFilterFactory — parameter names differ in OpenSearch",
        "Verify min_gram/max_gram parameter names and defaults match the "
        "OpenSearch edge_ngram token filter.",
    ),
    "SynonymGraphFilterFactory": (
        "uses SynonymGraphFilterFactory — synonym file loading differs in "
        "OpenSearch",
        "Convert synonyms file to OpenSearch format and configure in "
        "analysis settings. Note: SynonymGraphFilterFactory is recommended "
        "over SynonymFilterFactory.",
    ),
    "SynonymFilterFactory": (
        "uses SynonymFilterFactory — synonym handling differs in OpenSearch",
        "Convert synonyms file to OpenSearch format. Consider upgrading to "
        "synonym_graph token filter.",
    ),
}


# ── XML parsing ──────────────────────────────────────────────────────────

def _parse_xml(schema_xml: str) -> _NormalizedSchema:
    """Parse schema.xml into normalised representation."""
    try:
        root = ET.fromstring(schema_xml)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc

    schema = _NormalizedSchema()

    # Field types
    for ft in root.iter("fieldType"):
        name = ft.get("name", "")
        class_name = ft.get("class", "")
        filters: list[str] = []
        for analyzer in ft.iter("analyzer"):
            for tok in analyzer.iter("tokenizer"):
                cls = tok.get("class", "")
                if cls:
                    filters.append(cls.rsplit(".", 1)[-1] if "." in cls else cls)
            for filt in analyzer.iter("filter"):
                cls = filt.get("class", "")
                if cls:
                    filters.append(cls.rsplit(".", 1)[-1] if "." in cls else cls)
        schema.field_types.append(_FieldTypeDef(name, class_name, filters))

    # Fields
    for f in root.iter("field"):
        fname = f.get("name", "")
        if not fname or fname.startswith("_"):
            continue
        ftype = f.get("type", "")
        mv = f.get("multiValued", "false").lower() == "true"
        schema.fields.append(_FieldDef(fname, ftype, mv))

    # Copy fields
    for cf in root.iter("copyField"):
        src = cf.get("source", "")
        dest = cf.get("dest", "")
        if src and dest:
            schema.copy_fields.append(_CopyFieldDef(src, dest))

    # Dynamic fields
    for df in root.iter("dynamicField"):
        pattern = df.get("name", "")
        ftype = df.get("type", "")
        if pattern:
            schema.dynamic_fields.append(_DynamicFieldDef(pattern, ftype))

    return schema


# ── JSON parsing ─────────────────────────────────────────────────────────

def _parse_json(schema_dict: dict[str, Any]) -> _NormalizedSchema:
    """Parse Solr Schema API JSON dict into normalised representation."""
    data = schema_dict.get("schema", schema_dict)
    schema = _NormalizedSchema()

    for ft in data.get("fieldTypes", []):
        name = ft.get("name", "")
        class_name = ft.get("class", "")
        filters: list[str] = []
        # Solr JSON uses "analyzer" (single) or "indexAnalyzer"/"queryAnalyzer"
        for key in ("analyzer", "indexAnalyzer", "queryAnalyzer"):
            analyzer = ft.get(key)
            if not analyzer:
                continue
            # analyzer can be a dict or list of dicts
            analyzers = analyzer if isinstance(analyzer, list) else [analyzer]
            for a in analyzers:
                tok = a.get("tokenizer", {})
                cls = tok.get("class", "") if isinstance(tok, dict) else ""
                if cls:
                    filters.append(cls.rsplit(".", 1)[-1] if "." in cls else cls)
                for filt in a.get("filters", []):
                    cls = filt.get("class", "")
                    if cls:
                        filters.append(cls.rsplit(".", 1)[-1] if "." in cls else cls)
        schema.field_types.append(_FieldTypeDef(name, class_name, filters))

    for f in data.get("fields", []):
        fname = f.get("name", "")
        if not fname or fname.startswith("_"):
            continue
        ftype = f.get("type", "")
        mv = f.get("multiValued", False)
        schema.fields.append(_FieldDef(fname, ftype, bool(mv)))

    for cf in data.get("copyFields", []):
        src = cf.get("source", "")
        dest = cf.get("dest", "")
        if src and dest:
            schema.copy_fields.append(_CopyFieldDef(src, dest))

    for df in data.get("dynamicFields", []):
        pattern = df.get("name", "")
        ftype = df.get("type", "")
        if pattern:
            schema.dynamic_fields.append(_DynamicFieldDef(pattern, ftype))

    return schema


# ── Detection rules ──────────────────────────────────────────────────────

def _detect_deprecated_trie(schema: _NormalizedSchema) -> list[Incompatibility]:
    """Rule 1: Deprecated Trie field types."""
    results = []
    for ft in schema.field_types:
        if ft.class_name in _DEPRECATED_TRIE_CLASSES:
            short = ft.class_name.replace("solr.", "")
            results.append(Incompatibility(
                category="schema",
                severity="Breaking",
                description=(
                    f'Field type "{ft.name}" uses deprecated {short}'
                ),
                recommendation=(
                    f"Migrate to the Point field equivalent before migration, "
                    f"or confirm the OpenSearch mapping type is acceptable."
                ),
            ))
    return results


def _detect_copy_fields(schema: _NormalizedSchema) -> list[Incompatibility]:
    """Rule 2: copyField directives."""
    results = []
    for cf in schema.copy_fields:
        results.append(Incompatibility(
            category="schema",
            severity="Breaking",
            description=(
                f'copyField source="{cf.source}" dest="{cf.dest}" has no '
                f"OpenSearch equivalent"
            ),
            recommendation=(
                f'Add "copy_to": ["{cf.dest}"] to the "{cf.source}" field '
                f"in the OpenSearch mapping."
            ),
        ))
    return results


def _detect_complex_analyzers(schema: _NormalizedSchema) -> list[Incompatibility]:
    """Rule 3: Analyzer filters that need manual review."""
    results = []
    seen: set[tuple[str, str]] = set()  # (field_type_name, filter_short_name)

    for ft in schema.field_types:
        for filt in ft.filters:
            # Normalise to short name
            short = filt.rsplit(".", 1)[-1] if "." in filt else filt

            if short in _SAFE_FILTERS or f"solr.{short}" in _SAFE_FILTERS:
                continue

            key = (ft.name, short)
            if key in seen:
                continue
            seen.add(key)

            # Check for notable filters with specific recommendations
            if short in _NOTABLE_FILTERS:
                desc_suffix, rec = _NOTABLE_FILTERS[short]
                results.append(Incompatibility(
                    category="schema",
                    severity="Behavioral",
                    description=f'Field type "{ft.name}" {desc_suffix}',
                    recommendation=rec,
                ))
            else:
                results.append(Incompatibility(
                    category="schema",
                    severity="Behavioral",
                    description=(
                        f'Field type "{ft.name}" uses {short} — verify '
                        f"OpenSearch equivalent exists and behaves identically"
                    ),
                    recommendation=(
                        f"Check OpenSearch analysis documentation for a "
                        f"matching token filter. Test with representative "
                        f"queries to confirm equivalent behavior."
                    ),
                ))
    return results


def _detect_spatial(schema: _NormalizedSchema) -> list[Incompatibility]:
    """Rule 4: Spatial field types."""
    results = []
    seen: set[str] = set()
    for ft in schema.field_types:
        if ft.class_name in _SPATIAL_CLASSES and ft.name not in seen:
            seen.add(ft.name)
            short = ft.class_name.replace("solr.", "")
            results.append(Incompatibility(
                category="schema",
                severity="Behavioral",
                description=(
                    f'Spatial field type "{ft.name}" ({short}) requires '
                    f"coordinate order verification"
                ),
                recommendation=(
                    "Solr uses lat,lon order; OpenSearch uses [lon,lat] in "
                    "GeoJSON or {lat:x, lon:y} object form. Rewrite spatial "
                    "queries to OpenSearch geo query DSL."
                ),
            ))
    return results


def _detect_dynamic_fields(schema: _NormalizedSchema) -> list[Incompatibility]:
    """Rule 5: Dynamic field patterns."""
    results = []
    for df in schema.dynamic_fields:
        results.append(Incompatibility(
            category="schema",
            severity="Behavioral",
            description=(
                f'Dynamic field pattern "{df.pattern}" — OpenSearch '
                f"dynamic_templates use different matching syntax"
            ),
            recommendation=(
                "Verify the converted dynamic_template preserves intended "
                "behavior. OpenSearch uses match/match_pattern instead of "
                "Solr glob patterns."
            ),
        ))
    return results


def _detect_scoring_change() -> list[Incompatibility]:
    """Rule 6: TF-IDF vs BM25 scoring model change (always emitted)."""
    return [Incompatibility(
        category="query",
        severity="Behavioral",
        description=(
            "Scoring model change: Solr defaults to TF-IDF; OpenSearch "
            "defaults to BM25"
        ),
        recommendation=(
            "Run shadow queries comparing top-10 overlap for 2-4 weeks "
            "before cutover. Tune BM25 k1/b parameters per-field if "
            "results diverge unacceptably."
        ),
    )]


def _detect_unsupported_types(schema: _NormalizedSchema) -> list[Incompatibility]:
    """Rule 7: Field types with no OpenSearch equivalent."""
    results = []
    for ft in schema.field_types:
        if ft.class_name in _UNSUPPORTED_CLASSES:
            short = ft.class_name.replace("solr.", "")
            results.append(Incompatibility(
                category="schema",
                severity="Unsupported",
                description=(
                    f'Field type "{ft.name}" uses {short} which has no '
                    f"direct OpenSearch equivalent"
                ),
                recommendation=(
                    "Redesign the field using available OpenSearch types, "
                    "or implement equivalent behavior at the application layer."
                ),
            ))
    return results


def _detect_multi_valued(schema: _NormalizedSchema) -> list[Incompatibility]:
    """Rule 8: multiValued fields."""
    mv_fields = [f for f in schema.fields if f.multi_valued]
    if not mv_fields:
        return []
    names = ", ".join(f.name for f in mv_fields)
    return [Incompatibility(
        category="schema",
        severity="Behavioral",
        description=(
            f"multiValued fields detected: {names}"
        ),
        recommendation=(
            "OpenSearch arrays are implicit — any field can hold an array. "
            "No mapping change needed, but verify query and aggregation "
            "behavior on array fields."
        ),
    )]


# ── Core analysis ────────────────────────────────────────────────────────

def _analyze(schema: _NormalizedSchema) -> list[Incompatibility]:
    """Run all detection rules against a normalised schema."""
    results: list[Incompatibility] = []
    results.extend(_detect_deprecated_trie(schema))
    results.extend(_detect_copy_fields(schema))
    results.extend(_detect_complex_analyzers(schema))
    results.extend(_detect_spatial(schema))
    results.extend(_detect_dynamic_fields(schema))
    results.extend(_detect_scoring_change())
    results.extend(_detect_unsupported_types(schema))
    results.extend(_detect_multi_valued(schema))
    return results


# ── Public API ───────────────────────────────────────────────────────────

def detect_incompatibilities_xml(schema_xml: str) -> list[Incompatibility]:
    """Detect incompatibilities from a Solr ``schema.xml`` string.

    Args:
        schema_xml: Full text content of a Solr ``schema.xml`` file.

    Returns:
        A list of :class:`Incompatibility` objects.

    Raises:
        ValueError: If the XML cannot be parsed.
    """
    return _analyze(_parse_xml(schema_xml))


def detect_incompatibilities_json(schema_dict: dict[str, Any]) -> list[Incompatibility]:
    """Detect incompatibilities from a Solr Schema API JSON dict.

    Args:
        schema_dict: Parsed JSON from the Solr Schema API
            (``/solr/<collection>/schema``).  May be the full response
            (with a ``"schema"`` wrapper) or just the inner schema object.

    Returns:
        A list of :class:`Incompatibility` objects.
    """
    return _analyze(_parse_json(schema_dict))
