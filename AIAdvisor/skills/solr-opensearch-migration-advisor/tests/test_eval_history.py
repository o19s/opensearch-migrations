import json
from pathlib import Path

import pytest

from run_eval_tasks import compare_summaries, load_summary_payload, summarize_scored_results


def sample_results():
    return [
        {
            "scenario_id": "scenario-a",
            "title": "Scenario A",
            "judge_output": {
                "methodology_alignment": 4,
                "expert_judgement": 5,
                "heuristics": 4,
                "risk_identification": 4,
                "final_decision": "PASS",
                "rationale": "Good answer",
            },
        },
        {
            "scenario_id": "scenario-b",
            "title": "Scenario B",
            "judge_output": {
                "methodology_alignment": "3",
                "expert_judgement": "3",
                "heuristics": "4",
                "risk_identification": "2",
                "final_decision": "FAIL",
                "rationale": "Weak answer",
            },
        },
    ]


def test_summarize_scored_results_builds_rollup():
    summary = summarize_scored_results(sample_results())

    assert summary["scenario_count"] == 2
    assert summary["pass_count"] == 1
    assert summary["fail_count"] == 1
    assert summary["pass_rate"] == 0.5
    assert summary["average_scores"]["overall"] == 3.625
    assert summary["scenario_results"]["scenario-a"]["average_score"] == 4.25
    assert summary["scenario_results"]["scenario-b"]["final_decision"] == "FAIL"


def test_compare_summaries_detects_score_drop_and_new_failure():
    baseline = summarize_scored_results(sample_results())
    candidate_results = [
        {
            "scenario_id": "scenario-a",
            "title": "Scenario A",
            "judge_output": {
                "methodology_alignment": 3,
                "expert_judgement": 3,
                "heuristics": 3,
                "risk_identification": 3,
                "final_decision": "FAIL",
                "rationale": "Regressed",
            },
        },
        {
            "scenario_id": "scenario-b",
            "title": "Scenario B",
            "judge_output": {
                "methodology_alignment": 3,
                "expert_judgement": 3,
                "heuristics": 4,
                "risk_identification": 2,
                "final_decision": "FAIL",
                "rationale": "Same",
            },
        },
    ]
    candidate = summarize_scored_results(candidate_results)

    comparison = compare_summaries(
        candidate,
        baseline,
        max_overall_score_drop=0.1,
        max_pass_rate_drop=0.0,
        max_scenario_score_drop=0.5,
    )

    assert comparison["regression_detected"] is True
    assert any("overall average score dropped" in item for item in comparison["regressions"])
    assert any("changed decision from PASS to FAIL" in item for item in comparison["regressions"])


def test_load_summary_payload_accepts_bundle_shape(tmp_path: Path):
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps({"summary": summarize_scored_results(sample_results())}),
        encoding="utf-8",
    )

    loaded = load_summary_payload(bundle_path)
    assert loaded["scenario_count"] == 2
    assert loaded["average_scores"]["overall"] == pytest.approx(3.625)
