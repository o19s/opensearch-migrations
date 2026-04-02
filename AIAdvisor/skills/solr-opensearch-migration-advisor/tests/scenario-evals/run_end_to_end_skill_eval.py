"""
End-to-end skill evaluation for the Solr-to-OpenSearch migration advisor.

This script drives a real skill session — schema conversion, query translation,
session-state manipulation — then generates a migration report from that session
and optionally routes it through the LLM judge.  It is the closest automated
proxy for "what would a real advisor response look like for this scenario?"

Supported scenario flows
------------------------
``techproducts-full-workflow``
    Schema conversion of the Solr techproducts demo collection, a boolean
    filter query translation, and a report including a BM25 incompatibility
    and a SolrJ client integration.

``drupal-full-workflow``
    Schema conversion of a multilingual Drupal Search API collection, a URL
    query translation, and a report including a platform incompatibility and
    a language-analyzer warning.

Usage examples
--------------
Generate output only (no scoring)::

    python run_end_to_end_skill_eval.py \\
        --scenario-id techproducts-full-workflow \\
        --output /tmp/e2e-out.json

Generate and score::

    python run_end_to_end_skill_eval.py \\
        --scenario-id techproducts-full-workflow \\
        --score --api-key $JUDGE_API_KEY \\
        --output /tmp/e2e-scored.json

Compare against a baseline after scoring::

    python run_end_to_end_skill_eval.py \\
        --scenario-id techproducts-full-workflow \\
        --score --api-key $JUDGE_API_KEY \\
        --baseline baselines/golden_scenarios_baseline.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from judge_migration_advice import JUDGE_PROMPT, load_scenarios
from run_eval_tasks import build_run_bundle, compare_summaries, evaluate_tasks, load_summary_payload
from skill import SolrToOpenSearchMigrationSkill
from storage import InMemoryStorage


TECHPRODUCTS_SCHEMA_XML = """<schema name="techproducts" version="1.6">
  <fieldType name="string" class="solr.StrField"/>
  <fieldType name="text_general" class="solr.TextField"/>
  <fieldType name="pfloat" class="solr.FloatPointField"/>
  <fieldType name="pint" class="solr.IntPointField"/>
  <fieldType name="boolean" class="solr.BoolField"/>
  <field name="id" type="string" indexed="true" stored="true"/>
  <field name="name" type="text_general" indexed="true" stored="true"/>
  <field name="features" type="text_general" indexed="true" stored="true"/>
  <field name="cat" type="text_general" indexed="true" stored="true"/>
  <field name="price" type="pfloat" indexed="true" stored="true"/>
  <field name="popularity" type="pint" indexed="true" stored="true"/>
  <field name="inStock" type="boolean" indexed="true" stored="true"/>
  <copyField source="name" dest="_text_"/>
</schema>"""

DRUPAL_SCHEMA_XML = """<schema name="drupal" version="1.6">
  <fieldType name="string" class="solr.StrField"/>
  <fieldType name="text_und" class="solr.TextField"/>
  <field name="id" type="string" indexed="true" stored="true"/>
  <field name="tm_X3_en_title" type="text_und" indexed="true" stored="true"/>
  <field name="tm_X3_es_body" type="text_und" indexed="true" stored="true"/>
  <field name="ss_url" type="string" indexed="true" stored="true"/>
  <field name="sm_field_tags" type="string" indexed="true" stored="true" multiValued="true"/>
</schema>"""


def build_techproducts_response() -> str:
    """Run the techproducts end-to-end skill flow and return the migration report.

    Drives an in-memory skill session through schema conversion, query
    translation, and manual state enrichment (BM25 incompatibility + SolrJ
    client integration), then calls ``generate_report`` to produce the final
    Markdown report.

    Returns:
        A Markdown-formatted migration report string.
    """
    skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
    session_id = "e2e-techproducts-eval"

    skill.handle_message(
        f"Please convert this schema for migration: {TECHPRODUCTS_SCHEMA_XML}",
        session_id,
    )
    skill.handle_message(
        "translate query: inStock:true AND cat:electronics",
        session_id,
    )

    state = skill._storage.load_or_new(session_id)
    state.add_incompatibility(
        "scoring",
        "Behavioral",
        "BM25 may rank top queries differently than Solr's legacy similarity setup.",
        "Establish a judged relevance baseline before cutover.",
    )
    state.add_client_integration(
        "SolrJ",
        "library",
        "Spring Boot service uses SolrJ query and admin APIs.",
        "Replace with opensearch-java and adjust request/response handling.",
    )
    skill._storage.save(state)
    return skill.generate_report(session_id)


def build_drupal_response() -> str:
    """Run the Drupal end-to-end skill flow and return the migration report.

    Drives an in-memory skill session for a multilingual Drupal Search API
    collection.  Adds two incompatibilities (platform + language-analyzer) and
    a Drupal Search API client integration before generating the report.

    Returns:
        A Markdown-formatted migration report string.
    """
    skill = SolrToOpenSearchMigrationSkill(storage=InMemoryStorage())
    session_id = "e2e-drupal-eval"

    skill.handle_message(
        f"Please convert this schema for migration: {DRUPAL_SCHEMA_XML}",
        session_id,
    )
    skill.handle_message(
        "translate query: ss_url:/products/camera",
        session_id,
    )

    state = skill._storage.load_or_new(session_id)
    state.add_incompatibility(
        "platform",
        "Unsupported",
        "Drupal search_api_solr schemas should not be ported line by line.",
        "Treat this as a module migration and validate Search API OpenSearch support before cutover.",
    )
    state.add_incompatibility(
        "language",
        "Behavioral",
        "Multilingual Drupal field patterns suggest analyzer behavior may differ by language.",
        "Review English and Spanish analyzers and test top customer searches before cutover.",
    )
    state.add_client_integration(
        "Drupal Search API",
        "ui",
        "Drupal site relies on Search API Solr modules and Views integration.",
        "Replace engine integration with the OpenSearch-compatible module path and validate Views/autocomplete behavior.",
    )
    skill._storage.save(state)
    return skill.generate_report(session_id)


def build_artifact_expectations(scenario_id: str) -> list[str]:
    """Return artifact-quality expectations for a given end-to-end scenario.

    These expectations are passed to the judge as ``artifact_expectations``
    and inform the optional artifact-scoring dimensions (completeness,
    approval discipline, consumer impact, cutover readiness).

    Args:
        scenario_id: One of the supported end-to-end flow IDs.

    Returns:
        List of expectation strings, or an empty list for unknown scenarios.
    """
    if scenario_id == "techproducts-full-workflow":
        return [
            "Should look like a structured migration report, not just free-form advice.",
            "Should contain incompatibilities, client impact, milestones, blockers, implementation points, and cost estimates.",
            "Should show approval/cutover discipline appropriate for a migration report.",
        ]
    if scenario_id == "drupal-full-workflow":
        return [
            "Should look like a structured migration report for a Drupal-oriented migration, not just generic search advice.",
            "Should capture client impact and migration blockers tied to Drupal/Search API integration.",
            "Should show migration-readiness structure suitable for a go/no-go discussion.",
        ]
    return []


def build_end_to_end_response(scenario_id: str) -> str:
    """Dispatch to the appropriate end-to-end skill flow by scenario ID.

    Args:
        scenario_id: The scenario to run (``"techproducts-full-workflow"`` or
                     ``"drupal-full-workflow"``).

    Returns:
        The generated migration report string.

    Raises:
        ValueError: If no flow is implemented for the given ``scenario_id``.
    """
    if scenario_id == "techproducts-full-workflow":
        return build_techproducts_response()
    if scenario_id == "drupal-full-workflow":
        return build_drupal_response()
    raise ValueError(f"No end-to-end skill flow implemented for scenario_id={scenario_id!r}")


def main():
    parser = argparse.ArgumentParser(description="Run one end-to-end skill flow and optionally score it with the LLM judge.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).resolve().parent / "datasets" / "golden_scenarios.json",
    )
    parser.add_argument(
        "--scenario-id",
        default="techproducts-full-workflow",
        help="Scenario ID to generate via the real skill flow.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write JSON output.",
    )
    parser.add_argument(
        "--score",
        action="store_true",
        help="Score the generated response with the configured judge backend.",
    )
    parser.add_argument(
        "--api-base",
        default=os.environ.get("JUDGE_API_BASE", "https://api.openai.com/v1"),
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("JUDGE_API_KEY"),
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("JUDGE_MODEL", "gpt-4o-mini"),
    )
    parser.add_argument(
        "--repeat-judge",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Optional baseline bundle to compare against after scoring.",
    )
    args = parser.parse_args()

    scenario = next(
        (item for item in load_scenarios(args.dataset) if item["id"] == args.scenario_id),
        None,
    )
    if scenario is None:
        raise SystemExit(f"Unknown scenario_id: {args.scenario_id}")

    advisor_response = build_end_to_end_response(args.scenario_id)
    response_map = {args.scenario_id: advisor_response}

    if not args.score:
        output_obj = {
            "scenario_id": args.scenario_id,
            "responses": response_map,
        }
    else:
        if not args.api_key:
            raise SystemExit("--score requires --api-key or JUDGE_API_KEY")
        task = {
            "scenario_id": scenario["id"],
            "title": scenario["title"],
            "judge_prompt": JUDGE_PROMPT,
            "input_scenario": scenario["scenario"],
            "advisor_response": advisor_response,
            "expectations": scenario.get("expectations", []),
            "keyword_assertions": scenario.get("keyword_assertions", []),
            "artifact_expectations": build_artifact_expectations(args.scenario_id),
        }
        results = evaluate_tasks(
            [task],
            args.api_base,
            args.api_key,
            args.model,
            repeat_judge=args.repeat_judge,
        )
        output_obj = build_run_bundle(
            results,
            dataset_path=args.dataset,
            responses_path=None,
            model=args.model,
            api_base=args.api_base,
            run_label=f"e2e-{args.scenario_id}",
            score_mode="end_to_end_skill_flow",
        )
        if args.baseline is not None:
            output_obj["baseline_comparison"] = compare_summaries(
                output_obj["summary"],
                load_summary_payload(args.baseline),
                max_overall_score_drop=0.25,
                max_pass_rate_drop=0.05,
                max_scenario_score_drop=0.5,
            )

    output = json.dumps(output_obj, indent=2)
    if args.output is not None:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
