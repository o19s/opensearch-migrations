from skill import SolrToOpenSearchMigrationSkill
from storage import FileStorage


SIMPLE_SCHEMA_XML = """<schema name="techproducts" version="1.6">
  <fieldType name="string" class="solr.StrField"/>
  <fieldType name="text_general" class="solr.TextField"/>
  <field name="id" type="string" indexed="true" stored="true"/>
  <field name="name" type="text_general" indexed="true" stored="true"/>
  <field name="manu_exact" type="string" indexed="true" stored="true"/>
</schema>"""


def test_end_to_end_skill_flow_persists_session_and_generates_report(tmp_path):
    storage = FileStorage(str(tmp_path / "sessions"))
    skill = SolrToOpenSearchMigrationSkill(storage=storage)
    session_id = "e2e-techproducts"

    schema_response = skill.handle_message(
        f"Please convert this schema for migration: {SIMPLE_SCHEMA_XML}",
        session_id,
    )
    assert "OpenSearch mapping" in schema_response
    assert '"mappings"' in schema_response

    query_response = skill.handle_message(
        "translate query: name:opensearch AND manu_exact:acme",
        session_id,
    )
    assert '"query"' in query_response
    assert "OpenSearch equivalent" in query_response

    state = storage.load_or_new(session_id)
    state.add_incompatibility(
        "query",
        "Behavioral",
        "TF-IDF vs BM25 ranking drift likely on top queries",
        "Establish a judged relevance baseline before cutover.",
    )
    state.add_client_integration(
        "SolrJ",
        "library",
        "Spring Boot service still uses SolrJ client calls.",
        "Replace with opensearch-java and update search endpoint handling.",
    )
    storage.save(state)

    resumed_skill = SolrToOpenSearchMigrationSkill(storage=storage)
    report = resumed_skill.handle_message("generate report", session_id)

    assert "# Solr to OpenSearch Migration Report" in report
    assert "## Incompatibilities" in report
    assert "TF-IDF vs BM25 ranking drift likely on top queries" in report
    assert "## Client & Front-end Impact" in report
    assert "SolrJ" in report
    assert "opensearch-java" in report
    assert "## Major Milestones" in report
    assert "## Potential Blockers" in report
    assert "## Implementation Points" in report
    assert "## Cost Estimates" in report

    persisted_state = storage.load(session_id)
    assert persisted_state is not None
    assert persisted_state.get_fact("schema_migrated") is True
    assert persisted_state.progress >= 3
    assert len(persisted_state.history) == 3
    assert persisted_state.history[-1]["user"] == "generate report"
    assert (tmp_path / "sessions" / f"{session_id}.json").exists()
