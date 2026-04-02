"""
LLM-as-judge harness for the Solr-to-OpenSearch migration advisor.

This module defines the judge prompt, scoring criteria, and the scaffolding to
turn golden-scenario records into structured eval tasks. It is consumed by
``run_eval_tasks.py`` (batch runner) and ``run_end_to_end_skill_eval.py``
(single end-to-end flow).

Scoring model
-------------
Each advisor response is graded on four required dimensions (1–5 scale):

* ``methodology_alignment`` — Does the advisor recommend a full refactor over
  lift-and-shift?
* ``expert_judgement`` — Does it give opinionated, hard-won guidance (e.g.
  warn about BM25 differences)?
* ``heuristics`` — Does it use "if X, then Y" patterns?
* ``risk_identification`` — Does it name concrete pitfalls (co-location rule,
  pagination cliff, etc.)?

For artifact-heavy responses (reports, approval docs, cutover plans) there are
four additional optional dimensions: ``artifact_completeness``,
``approval_discipline``, ``consumer_impact_awareness``, ``cutover_readiness``.

A response PASSes when its required-dimension average is above 3.5 and it
contains no major technical errors.
"""

import json
from pathlib import Path


DATASET_PATH = Path(__file__).resolve().parent / "datasets" / "golden_scenarios.json"

JUDGE_PROMPT = """
You are a Senior Search Consultant at OpenSearch Search Consulting (OSC).
Your task is to judge the quality of a Solr-to-OpenSearch migration advisor's response.

### Scoring Criteria:
1.  **Methodology Alignment (1-5):** Does it follow the "Full Refactor beats Lift-and-Shift" mantra?
2.  **Expert Judgement (1-5):** Does it provide opinionated, hard-won guidance (e.g., warning about BM25 differences)?
3.  **Heuristics (1-5):** Does it use "If X, then Y" patterns (e.g., "If you have custom Java plugins, re-indexing is complex")?
4.  **Risk Identification (1-5):** Does it correctly identify common pitfalls (shard co-location, pagination cliff)?

### Optional Artifact Scoring:
If the response is primarily a migration report, artifact set, approval document, or cutover-oriented output, also include these optional 1-5 fields:
- **artifact_completeness**
- **approval_discipline**
- **consumer_impact_awareness**
- **cutover_readiness**

### Optional Advice Interaction Scoring:
If the scenario tests advisor interaction quality (follow-up questions, persona calibration, scope management), also include these optional 1-5 fields:
- **follow_up_quality** — Did the advisor ask the right clarifying questions? Were they targeted and prioritized, not a laundry list?
- **persona_appropriateness** — Was the response calibrated to the audience (CTO vs business owner vs DevOps)? Right depth, right vocabulary?
- **scope_discipline** — Did the advisor resist premature commitment, flag unknowns, and manage scope expectations?

### Final Decision:
A response is "PASS" if it averages above 3.5 across all categories and has NO major technical errors.
"""

def load_scenarios(dataset_path: Path = DATASET_PATH) -> list[dict]:
    """Load the golden-scenario dataset from *dataset_path*.

    Returns a list of scenario records, each a dict with at minimum the keys
    ``id``, ``title``, ``scenario``, ``expectations``, and
    ``keyword_assertions``.
    """
    with dataset_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def generate_eval_task(
    scenario: str,
    advisor_response: str,
    expectations=None,
    scenario_id=None,
    title=None,
) -> dict:
    """Build a structured evaluation task from a scenario string and an advisor response.

    The returned dict contains everything the judge backend needs: the judge
    prompt, the scenario text, the advisor response to grade, and the list of
    expected qualities. It is ready to be serialised to JSON or passed directly
    to ``score_task_with_openai_compatible_backend``.

    Args:
        scenario:         Natural-language description of the client situation.
        advisor_response: The migration advisor's response to be graded.
        expectations:     Optional list of specific qualities the response must
                          demonstrate. Defaults to three standard expectations
                          (BM25 mention, anti-lift-and-shift counsel, dual-write
                          recommendation).
        scenario_id:      Optional stable identifier for the scenario.
        title:            Optional human-readable title for display.

    Returns:
        A dict with keys: ``scenario_id``, ``title``, ``judge_prompt``,
        ``input_scenario``, ``advisor_response``, ``expectations``.
    """
    return {
        "scenario_id": scenario_id,
        "title": title,
        "judge_prompt": JUDGE_PROMPT,
        "input_scenario": scenario,
        "advisor_response": advisor_response,
        "expectations": expectations or [
            "Must mention relevance tuning (BM25 vs TF-IDF)",
            "Must counsel against simple porting of XML configsets",
            "Must recommend dual-write or shadow-traffic validation"
        ]
    }


def generate_eval_task_from_scenario_record(record: dict, advisor_response: str) -> dict:
    """Build an eval task from a dataset record and an advisor response.

    Convenience wrapper around :func:`generate_eval_task` that unpacks the
    standard dataset-record keys (``id``, ``title``, ``scenario``,
    ``expectations``) and also attaches ``keyword_assertions``,
    ``artifact_expectations``, ``anti_patterns``, and
    ``expected_response_type`` when present in the record.

    Args:
        record:           A single entry from a scenario dataset (golden,
                          solr_feature_challenges, or advisor_interactions).
        advisor_response: The advisor output to be graded.

    Returns:
        A structured eval task dict ready for the judge pipeline.
    """
    task = generate_eval_task(
        scenario=record["scenario"],
        advisor_response=advisor_response,
        expectations=record.get("expectations", []),
        scenario_id=record.get("id"),
        title=record.get("title"),
    )
    task["keyword_assertions"] = record.get("keyword_assertions", [])
    task["anti_patterns"] = record.get("anti_patterns", [])
    task["expected_response_type"] = record.get("expected_response_type")
    task["persona"] = record.get("persona")
    task["category"] = record.get("category")
    return task

if __name__ == "__main__":
    scenario = "Client has Solr 4.10, 20 collections, 500GB data, and uses heavy custom Java search components."
    response = "I will port your XML schema to JSON mappings and use a re-indexer to move your 500GB of data."
    
    eval_task = generate_eval_task(scenario, response)
    print(f"Evaluation Task Created for Scenario: {scenario[:50]}...")
    # This task would then be sent to an LLM judge via API
    print(f"Expectations for Judge: {eval_task['expectations']}")
