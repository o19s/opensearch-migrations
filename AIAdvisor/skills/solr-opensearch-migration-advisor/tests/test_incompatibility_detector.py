"""Tests for incompatibility_detector.py"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from incompatibility_detector import (
    detect_incompatibilities_xml,
    detect_incompatibilities_json,
)


# ── Helpers ──────────────────────────────────────────────────────────────

def _minimal_schema(fields="", field_types="", copy_fields="", dynamic_fields=""):
    return (
        f'<schema name="test" version="1.6">\n'
        f'  <fieldType name="string" class="solr.StrField"/>\n'
        f"  {field_types}\n"
        f'  <field name="id" type="string" indexed="true" stored="true"/>\n'
        f"  {fields}\n"
        f"  {copy_fields}\n"
        f"  {dynamic_fields}\n"
        f"</schema>"
    )


def _find(incompatibilities, **kwargs):
    """Find incompatibilities matching all given field values."""
    return [
        i for i in incompatibilities
        if all(getattr(i, k) == v or v in getattr(i, k) for k, v in kwargs.items())
    ]


# ── Rule 1: Deprecated Trie fields ──────────────────────────────────────

def test_detects_deprecated_trie_int_field():
    xml = _minimal_schema(
        field_types='<fieldType name="tint" class="solr.TrieIntField"/>',
        fields='<field name="count" type="tint" indexed="true" stored="true"/>',
    )
    incs = detect_incompatibilities_xml(xml)
    trie = _find(incs, severity="Breaking", description="TrieIntField")
    assert len(trie) == 1
    assert trie[0].category == "schema"


def test_detects_multiple_trie_types():
    xml = _minimal_schema(
        field_types=(
            '<fieldType name="tint" class="solr.TrieIntField"/>'
            '<fieldType name="tdate" class="solr.TrieDateField"/>'
            '<fieldType name="tlong" class="solr.TrieLongField"/>'
        ),
    )
    incs = detect_incompatibilities_xml(xml)
    trie = _find(incs, severity="Breaking", description="Trie")
    assert len(trie) == 3


def test_no_trie_fields_no_trie_incompatibility():
    xml = _minimal_schema(
        field_types='<fieldType name="pint" class="solr.IntPointField"/>',
    )
    incs = detect_incompatibilities_xml(xml)
    trie = _find(incs, description="Trie")
    assert len(trie) == 0


# ── Rule 2: copyField directives ────────────────────────────────────────

def test_detects_copy_fields():
    xml = _minimal_schema(
        fields=(
            '<field name="title" type="string" indexed="true" stored="true"/>'
            '<field name="text" type="string" indexed="true" stored="true"/>'
            '<field name="sort" type="string" indexed="true" stored="true"/>'
        ),
        copy_fields=(
            '<copyField source="title" dest="text"/>'
            '<copyField source="title" dest="sort"/>'
            '<copyField source="id" dest="text"/>'
        ),
    )
    incs = detect_incompatibilities_xml(xml)
    cfs = _find(incs, severity="Breaking", description="copyField")
    assert len(cfs) == 3


def test_no_copy_fields_no_copy_incompatibility():
    xml = _minimal_schema()
    incs = detect_incompatibilities_xml(xml)
    cfs = _find(incs, description="copyField")
    assert len(cfs) == 0


# ── Rule 3: Complex analyzers ───────────────────────────────────────────

def test_detects_phonetic_analyzer():
    xml = _minimal_schema(field_types="""
        <fieldType name="text_phonetic" class="solr.TextField">
          <analyzer>
            <tokenizer class="solr.StandardTokenizerFactory"/>
            <filter class="solr.DoubleMetaphoneFilterFactory" inject="false"/>
          </analyzer>
        </fieldType>
    """)
    incs = detect_incompatibilities_xml(xml)
    ph = _find(incs, description="DoubleMetaphoneFilterFactory")
    assert len(ph) == 1
    assert "phonetic" in ph[0].recommendation.lower()


def test_detects_edge_ngram_analyzer():
    xml = _minimal_schema(field_types="""
        <fieldType name="text_suggest" class="solr.TextField">
          <analyzer type="index">
            <tokenizer class="solr.StandardTokenizerFactory"/>
            <filter class="solr.EdgeNGramFilterFactory" minGramSize="2" maxGramSize="15"/>
          </analyzer>
        </fieldType>
    """)
    incs = detect_incompatibilities_xml(xml)
    eng = _find(incs, description="EdgeNGramFilterFactory")
    assert len(eng) == 1


def test_detects_synonym_filter():
    xml = _minimal_schema(field_types="""
        <fieldType name="text_en" class="solr.TextField">
          <analyzer type="query">
            <tokenizer class="solr.StandardTokenizerFactory"/>
            <filter class="solr.SynonymGraphFilterFactory" synonyms="synonyms.txt"/>
          </analyzer>
        </fieldType>
    """)
    incs = detect_incompatibilities_xml(xml)
    syn = _find(incs, description="SynonymGraphFilterFactory")
    assert len(syn) == 1


def test_safe_analyzers_not_flagged():
    xml = _minimal_schema(field_types="""
        <fieldType name="text_basic" class="solr.TextField">
          <analyzer>
            <tokenizer class="solr.StandardTokenizerFactory"/>
            <filter class="solr.LowerCaseFilterFactory"/>
            <filter class="solr.StopFilterFactory" ignoreCase="true"/>
          </analyzer>
        </fieldType>
    """)
    incs = detect_incompatibilities_xml(xml)
    analyzer_incs = _find(incs, category="schema", description="text_basic")
    assert len(analyzer_incs) == 0


# ── Rule 4: Spatial field types ──────────────────────────────────────────

def test_detects_spatial_field_type():
    xml = _minimal_schema(
        field_types='<fieldType name="location" class="solr.LatLonPointSpatialField"/>',
        fields='<field name="geo" type="location" indexed="true" stored="true"/>',
    )
    incs = detect_incompatibilities_xml(xml)
    spatial = _find(incs, description="Spatial")
    assert len(spatial) == 1
    assert "lat,lon" in spatial[0].recommendation.lower()


# ── Rule 5: Dynamic field patterns ──────────────────────────────────────

def test_detects_dynamic_fields():
    xml = _minimal_schema(
        dynamic_fields=(
            '<dynamicField name="*_s" type="string" indexed="true" stored="true"/>'
            '<dynamicField name="*_i" type="string" indexed="true" stored="true"/>'
        ),
    )
    incs = detect_incompatibilities_xml(xml)
    dfs = _find(incs, description="Dynamic field pattern")
    assert len(dfs) == 2


# ── Rule 6: BM25 scoring ────────────────────────────────────────────────

def test_always_flags_bm25_scoring():
    xml = _minimal_schema()  # minimal schema, no special features
    incs = detect_incompatibilities_xml(xml)
    bm25 = _find(incs, category="query", description="BM25")
    assert len(bm25) == 1


# ── Rule 7: Unsupported types ───────────────────────────────────────────

def test_detects_unsupported_field_types():
    xml = _minimal_schema(
        field_types='<fieldType name="collation" class="solr.ICUCollationField"/>',
    )
    incs = detect_incompatibilities_xml(xml)
    unsup = _find(incs, severity="Unsupported")
    assert len(unsup) == 1
    assert "ICUCollationField" in unsup[0].description


# ── Rule 8: multiValued fields ──────────────────────────────────────────

def test_detects_multi_valued_fields():
    xml = _minimal_schema(
        fields=(
            '<field name="tags" type="string" indexed="true" stored="true" multiValued="true"/>'
            '<field name="cats" type="string" indexed="true" stored="true" multiValued="true"/>'
        ),
    )
    incs = detect_incompatibilities_xml(xml)
    mv = _find(incs, description="multiValued")
    assert len(mv) == 1
    assert "tags" in mv[0].description
    assert "cats" in mv[0].description


# ── JSON entry point ────────────────────────────────────────────────────

def test_json_schema_detection():
    schema = {
        "schema": {
            "fieldTypes": [
                {"name": "tint", "class": "solr.TrieIntField"},
                {"name": "string", "class": "solr.StrField"},
            ],
            "fields": [
                {"name": "id", "type": "string"},
                {"name": "count", "type": "tint"},
            ],
            "copyFields": [
                {"source": "id", "dest": "count"},
            ],
            "dynamicFields": [],
        }
    }
    incs = detect_incompatibilities_json(schema)
    trie = _find(incs, severity="Breaking", description="TrieIntField")
    assert len(trie) == 1
    cfs = _find(incs, severity="Breaking", description="copyField")
    assert len(cfs) == 1


# ── Comprehensive demo schema test ──────────────────────────────────────

def test_demo_schema_comprehensive():
    """Run detection against the actual demo schema.xml."""
    demo_schema_path = os.path.join(
        os.path.dirname(__file__), "connected", "solr-demo", "conf", "schema.xml"
    )
    with open(demo_schema_path, "r") as f:
        schema_xml = f.read()

    incs = detect_incompatibilities_xml(schema_xml)

    # Categorise findings
    breaking = [i for i in incs if i.severity == "Breaking"]
    behavioral = [i for i in incs if i.severity == "Behavioral"]

    # 1 Trie type + 7 copyFields = 8 Breaking
    trie = _find(incs, severity="Breaking", description="Trie")
    assert len(trie) == 1, f"Expected 1 Trie, got {len(trie)}"

    copy = _find(incs, severity="Breaking", description="copyField")
    assert len(copy) == 7, f"Expected 7 copyFields, got {len(copy)}"

    assert len(breaking) == 8, f"Expected 8 Breaking, got {len(breaking)}"

    # Behavioral: phonetic, edge ngram, synonym, spatial, dynamic fields, BM25, multiValued
    assert len(behavioral) >= 7, f"Expected >=7 Behavioral, got {len(behavioral)}"

    # Specific checks
    assert len(_find(incs, description="DoubleMetaphoneFilterFactory")) == 1
    assert len(_find(incs, description="EdgeNGramFilterFactory")) == 1
    assert len(_find(incs, description="SynonymGraphFilterFactory")) == 1
    assert len(_find(incs, description="Spatial")) == 1
    assert len(_find(incs, description="Dynamic field pattern")) == 6
    assert len(_find(incs, description="BM25")) == 1
    assert len(_find(incs, description="multiValued")) == 1

    # Total should be substantial
    assert len(incs) >= 19, f"Expected >=19 total, got {len(incs)}"
