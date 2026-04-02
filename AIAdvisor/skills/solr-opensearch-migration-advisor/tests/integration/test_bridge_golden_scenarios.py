"""Bridge tests: validate Jeff's converters against golden scenario expectations.

These tests feed TechProducts and Drupal golden scenario inputs into the actual
schema_converter.py and query_converter.py, asserting what currently works and
marking known gaps with xfail so we can track progress as converters improve.
"""

import json

import pytest

from schema_converter import SchemaConverter
from query_converter import QueryConverter


# ── TechProducts schema fixture ─────────────────────────────────────────────

TECHPRODUCTS_SCHEMA_XML = """\
<schema name="techproducts" version="1.6">
  <fieldType name="string" class="solr.StrField"/>
  <fieldType name="text_general" class="solr.TextField">
    <analyzer type="index">
      <tokenizer class="solr.StandardTokenizerFactory"/>
      <filter class="solr.LowerCaseFilterFactory"/>
      <filter class="solr.StopFilterFactory" words="stopwords.txt" ignoreCase="true"/>
    </analyzer>
    <analyzer type="query">
      <tokenizer class="solr.StandardTokenizerFactory"/>
      <filter class="solr.LowerCaseFilterFactory"/>
      <filter class="solr.StopFilterFactory" words="stopwords.txt" ignoreCase="true"/>
      <filter class="solr.SynonymGraphFilterFactory" synonyms="synonyms.txt"/>
    </analyzer>
  </fieldType>
  <fieldType name="pint" class="solr.IntPointField"/>
  <fieldType name="pfloat" class="solr.FloatPointField"/>
  <fieldType name="plong" class="solr.LongPointField"/>
  <fieldType name="pdate" class="solr.DatePointField"/>
  <fieldType name="boolean" class="solr.BoolField"/>
  <fieldType name="location" class="solr.LatLonPointSpatialField"/>

  <field name="id" type="string" indexed="true" stored="true"/>
  <field name="name" type="text_general" indexed="true" stored="true"/>
  <field name="manu" type="text_general" indexed="true" stored="true"/>
  <field name="manu_exact" type="string" indexed="true" stored="true"/>
  <field name="cat" type="text_general" indexed="true" stored="true"/>
  <field name="features" type="text_general" indexed="true" stored="true"/>
  <field name="includes" type="text_general" indexed="true" stored="true"/>
  <field name="weight" type="pfloat" indexed="true" stored="true"/>
  <field name="price" type="pfloat" indexed="true" stored="true"/>
  <field name="popularity" type="pint" indexed="true" stored="true"/>
  <field name="inStock" type="boolean" indexed="true" stored="true"/>
  <field name="manufacturedate_dt" type="pdate" indexed="true" stored="true"/>
  <field name="store" type="location" indexed="true" stored="true"/>
  <field name="description" type="text_general" indexed="true" stored="true"/>
  <field name="comments" type="text_general" indexed="true" stored="true"/>
  <field name="_version_" type="plong" indexed="true" stored="true"/>

  <dynamicField name="*_s" type="string" indexed="true" stored="true"/>
  <dynamicField name="*_i" type="pint" indexed="true" stored="true"/>
  <dynamicField name="*_f" type="pfloat" indexed="true" stored="true"/>
  <dynamicField name="*_l" type="plong" indexed="true" stored="true"/>
  <dynamicField name="*_b" type="boolean" indexed="true" stored="true"/>
  <dynamicField name="*_dt" type="pdate" indexed="true" stored="true"/>
  <dynamicField name="*_p" type="location" indexed="true" stored="true"/>

  <copyField source="name" dest="_text_"/>
  <copyField source="manu" dest="_text_"/>
  <copyField source="features" dest="_text_"/>
  <copyField source="includes" dest="_text_"/>
  <copyField source="description" dest="_text_"/>
  <copyField source="comments" dest="_text_"/>
</schema>
"""


# ── TechProducts Schema Tests ────────────────────────────────────────────────

class TestTechProductsSchema:
    """Golden scenario: TechProducts schema conversion."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.converter = SchemaConverter()
        self.result = self.converter.convert_xml(TECHPRODUCTS_SCHEMA_XML)
        self.props = self.result["mappings"]["properties"]

    def test_converts_all_15_explicit_fields(self):
        expected_fields = {
            "id", "name", "manu", "manu_exact", "cat", "features", "includes",
            "weight", "price", "popularity", "inStock", "manufacturedate_dt",
            "store", "description", "comments",
        }
        assert expected_fields == set(self.props.keys())

    def test_id_maps_to_keyword(self):
        assert self.props["id"]["type"] == "keyword"

    def test_text_fields_map_to_text(self):
        text_fields = ["name", "manu", "cat", "features", "includes", "description", "comments"]
        for f in text_fields:
            assert self.props[f]["type"] == "text", f"{f} should be text, got {self.props[f]['type']}"

    def test_manu_exact_maps_to_keyword(self):
        assert self.props["manu_exact"]["type"] == "keyword"

    def test_numeric_fields(self):
        assert self.props["weight"]["type"] == "float"
        assert self.props["price"]["type"] == "float"
        assert self.props["popularity"]["type"] == "integer"

    def test_boolean_field(self):
        assert self.props["inStock"]["type"] == "boolean"

    def test_date_field(self):
        assert self.props["manufacturedate_dt"]["type"] == "date"

    def test_geo_field(self):
        assert self.props["store"]["type"] == "geo_point"

    def test_internal_version_field_excluded(self):
        assert "_version_" not in self.props

    def test_dynamic_templates_created(self):
        templates = self.result["mappings"].get("dynamic_templates", [])
        assert len(templates) == 7

    def test_dynamic_template_types_correct(self):
        templates = self.result["mappings"]["dynamic_templates"]
        template_map = {}
        for t in templates:
            for name, spec in t.items():
                template_map[name] = spec["mapping"]["type"]

        assert template_map["dynamic_s"] == "keyword"
        assert template_map["dynamic_i"] == "integer"
        assert template_map["dynamic_f"] == "float"
        assert template_map["dynamic_l"] == "long"
        assert template_map["dynamic_b"] == "boolean"
        assert template_map["dynamic_dt"] == "date"
        assert template_map["dynamic_p"] == "geo_point"

    # ── Known gaps (xfail) ───────────────────────────────────────────────

    def test_analyzer_chain_converted(self):
        """Golden scenario expects text_general_index and text_general_query analyzers."""
        settings = self.result.get("settings", {})
        analysis = settings.get("analysis", {})
        analyzers = analysis.get("analyzer", {})
        assert "text_general_index" in analyzers or "text_general_query" in analyzers

    def test_copy_fields_converted(self):
        """Golden scenario expects name field to have copy_to: ['_text_']."""
        assert "copy_to" in self.props["name"]

    def test_scoring_incompatibility_flagged(self):
        """Golden scenario expects SCORING-001 (TF-IDF→BM25) to be flagged."""
        assert "incompatibilities" in self.result
        assert any(item.get("id") == "SCORING-001" for item in self.result["incompatibilities"])


# ── TechProducts Query Tests ─────────────────────────────────────────────────

class TestTechProductsQueries:
    """Golden scenario: TechProducts query translation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.converter = QueryConverter()

    def test_stock_filter(self):
        """Query 2: q=*:*&fq=inStock:true → bool.filter term."""
        # The query converter handles the q= part
        result = self.converter.convert("*:*")
        assert result == {"query": {"match_all": {}}}

        # fq part
        result = self.converter.convert("inStock:true")
        assert result["query"]["match"]["inStock"] == "true"

    def test_price_range(self):
        """Query 3: fq=price:[50 TO 300] → range query."""
        result = self.converter.convert("price:[50 TO 300]")
        range_q = result["query"]["range"]["price"]
        assert range_q["gte"] == 50
        assert range_q["lte"] == 300

    def test_boolean_and_query(self):
        """Combined filter: inStock:true AND cat:camera."""
        result = self.converter.convert("inStock:true AND cat:camera")
        must = result["query"]["bool"]["must"]
        assert len(must) == 2

    def test_field_value_match(self):
        """Basic field:value → match query."""
        result = self.converter.convert("cat:electronics")
        assert "match" in result["query"]
        assert result["query"]["match"]["cat"] == "electronics"

    # ── Known gaps (xfail) ───────────────────────────────────────────────

    def test_request_level_edismax_placeholder(self):
        """Placeholder request conversion for q + qf -> multi_match."""
        result = self.converter.convert_request(
            {
                "q": "hard drive",
                "defType": "edismax",
                "qf": "name^2 features^1 cat^0.5",
            }
        )
        query = result["query"]
        assert "multi_match" in query
        assert "name^2" in query["multi_match"]["fields"]

    def test_request_level_fq_placeholder(self):
        """Placeholder request conversion for fq -> bool.filter."""
        result = self.converter.convert_request(
            {
                "q": "*:*",
                "fq": ["inStock:true"],
            }
        )
        assert "bool" in result["query"]
        assert "filter" in result["query"]["bool"]

    def test_request_level_facet_placeholder(self):
        """Placeholder request conversion for facet.field -> terms agg."""
        result = self.converter.convert_request(
            {
                "q": "*:*",
                "facet.field": "cat",
            }
        )
        assert "aggs" in result
        assert result["aggs"]["cat"]["terms"]["field"] == "cat.keyword"

    def test_edismax_keyword_search(self):
        """Query 1: q=hard drive&qf=name^2 features^1 cat^0.5&defType=edismax
        → multi_match with field boosts."""
        result = self.converter.convert_request(
            {
                "q": "hard drive",
                "qf": "name^2 features^1 cat^0.5",
                "defType": "edismax",
            }
        )
        query = result["query"]
        assert "multi_match" in query
        assert "name^2" in query["multi_match"]["fields"]

    def test_fq_as_filter_clause(self):
        """fq params should become non-scoring bool.filter clauses."""
        result = self.converter.convert_request(
            {
                "q": "*:*",
                "fq": ["inStock:true"],
            }
        )
        assert "bool" in result["query"]
        assert "filter" in result["query"]["bool"]
        assert {"term": {"inStock": True}} in result["query"]["bool"]["filter"]

    def test_facet_field_to_terms_agg(self):
        """Query 4: facet=true&facet.field=cat → terms aggregation."""
        result = self.converter.convert_request(
            {
                "q": "*:*",
                "facet.field": "cat",
            }
        )
        assert "aggs" in result
        assert result["aggs"]["cat"]["terms"]["field"] == "cat.keyword"

    def test_highlighting_placeholder(self):
        """Highlight params should map to an OpenSearch highlight block."""
        result = self.converter.convert_request(
            {
                "q": "solr migration",
                "hl": "true",
                "hl.fl": "title,body",
                "hl.simple.pre": "<b>",
                "hl.simple.post": "</b>",
            }
        )
        assert result["highlight"]["fields"] == {"title": {}, "body": {}}
        assert result["highlight"]["pre_tags"] == ["<b>"]
        assert result["highlight"]["post_tags"] == ["</b>"]

    def test_integrated_request_demo_shape(self):
        """A demo-ish integrated request should compose cleanly."""
        result = self.converter.convert_request(
            {
                "q": "laptop",
                "defType": "edismax",
                "qf": "title^3 description^1",
                "fq": ["status:active", "price:[0 TO 5000]"],
                "facet.field": "category",
                "hl": "true",
                "hl.fl": "title,description",
                "rows": "10",
                "sort": "price asc",
            }
        )
        assert "bool" in result["query"]
        assert {"term": {"status": "active"}} in result["query"]["bool"]["filter"]
        assert result["aggs"]["category"]["terms"]["field"] == "category.keyword"
        assert result["highlight"]["fields"] == {"title": {}, "description": {}}
        assert result["size"] == 10
        assert result["sort"] == [{"price": {"order": "asc"}}]

    def test_boost_preserved(self):
        """Field boosts should be preserved, not stripped."""
        result = self.converter.convert("name:opensearch^3")
        query = result["query"]
        assert "boost" in json.dumps(query)


# ── Drupal Scenario Tests ────────────────────────────────────────────────────

class TestDrupalScenario:
    """Golden scenario: Drupal migration — tests strategic judgment, not conversion.

    The Drupal scenario's key insight is that the advisor should NOT attempt
    raw schema conversion. These tests verify the converter's behavior with
    Drupal-style schemas to document why module swap is the right approach.
    """

    DRUPAL_SCHEMA_XML = """\
<schema name="drupal" version="1.6">
  <fieldType name="string" class="solr.StrField"/>
  <fieldType name="text_und" class="solr.TextField"/>

  <dynamicField name="*_s" type="string" indexed="true" stored="true"/>

  <field name="id" type="string" indexed="true" stored="true"/>
  <field name="tm_X3_en_title" type="text_und" indexed="true" stored="true"/>
  <field name="tm_X3_es_body" type="text_und" indexed="true" stored="true"/>
  <field name="ss_url" type="string" indexed="true" stored="true"/>
  <field name="is_status" type="string" indexed="true" stored="true"/>
  <field name="sm_field_tags" type="string" indexed="true" stored="true" multiValued="true"/>
  <field name="_version_" type="string" indexed="true" stored="true"/>
</schema>
"""

    def test_drupal_fields_convert_but_lose_meaning(self):
        """Drupal's machine-generated field names convert syntactically but
        the converter doesn't understand the naming convention (tm_, ss_, X3_en_, etc.).
        This documents WHY module swap is the right approach."""
        converter = SchemaConverter()
        result = converter.convert_xml(self.DRUPAL_SCHEMA_XML)
        props = result["mappings"]["properties"]

        # Fields convert — but the converter doesn't know that:
        # - tm_X3_en_title needs an English analyzer
        # - tm_X3_es_body needs a Spanish analyzer
        # - These are machine-managed, not human-designed
        assert "tm_X3_en_title" in props
        assert "tm_X3_es_body" in props

        # They all get mapped to generic "text" — losing the language-specific
        # analyzers that Drupal's search_api_solr module carefully configured
        assert props["tm_X3_en_title"]["type"] == "text"
        assert props["tm_X3_es_body"]["type"] == "text"

    def test_multilingual_fields_flagged(self):
        """Converter should detect X3_en_, X3_es_ patterns and flag multilingual concern."""
        converter = SchemaConverter()
        result = converter.convert_xml(self.DRUPAL_SCHEMA_XML)
        assert "warnings" in result
        assert any(
            item.get("code") == "LANGUAGE-FIELD-PATTERNS"
            for item in result["warnings"]
        )
