import pytest

from run_eval_tasks import compare_summaries, normalize_judge_output, validate_scored_results


def test_normalize_judge_output_rejects_score_above_range():
    with pytest.raises(ValueError, match="between 1 and 5 inclusive"):
        normalize_judge_output(
            {
                "methodology_alignment": 6,
                "expert_judgement": 4,
                "heuristics": 4,
                "risk_identification": 4,
                "final_decision": "PASS",
            }
        )


def test_normalize_judge_output_rejects_invalid_final_decision():
    with pytest.raises(ValueError, match="PASS or FAIL"):
        normalize_judge_output(
            {
                "methodology_alignment": 4,
                "expert_judgement": 4,
                "heuristics": 4,
                "risk_identification": 4,
                "final_decision": "MAYBE",
            }
        )


def test_validate_scored_results_rejects_missing_judge_output():
    with pytest.raises(ValueError, match="missing judge_output"):
        validate_scored_results(
            [
                {
                    "scenario_id": "s1",
                    "title": "Scenario 1",
                }
            ]
        )


def test_validate_scored_results_normalizes_valid_payload():
    results = validate_scored_results(
        [
            {
                "scenario_id": "s1",
                "title": "Scenario 1",
                "judge_output": {
                    "methodology_alignment": "4",
                    "expert_judgement": "4",
                    "heuristics": "5",
                    "risk_identification": "3",
                    "final_decision": "pass",
                    "rationale": "Fine",
                },
            }
        ]
    )

    assert results[0]["judge_output"]["final_decision"] == "PASS"
    assert results[0]["judge_output"]["average_score"] == 4.0


def test_normalize_judge_output_accepts_optional_artifact_scores():
    normalized = normalize_judge_output(
        {
            "methodology_alignment": 4,
            "expert_judgement": 4,
            "heuristics": 5,
            "risk_identification": 3,
            "artifact_completeness": 5,
            "approval_discipline": 4,
            "consumer_impact_awareness": 4,
            "cutover_readiness": 5,
            "final_decision": "PASS",
        }
    )

    assert normalized["artifact_completeness"] == 5.0
    assert normalized["artifact_average_score"] == 4.5


def test_compare_summaries_can_include_optional_scores():
    candidate = {
        "average_scores": {"overall": 4.0},
        "pass_rate": 1.0,
        "average_optional_scores": {"artifact_completeness": 3.5},
        "scenario_results": {},
    }
    baseline = {
        "average_scores": {"overall": 4.0},
        "pass_rate": 1.0,
        "average_optional_scores": {"artifact_completeness": 4.5},
        "scenario_results": {},
    }
    comparison = compare_summaries(
        candidate,
        baseline,
        max_overall_score_drop=0.25,
        max_pass_rate_drop=0.05,
        max_scenario_score_drop=0.5,
        use_optional_scores_in_regression=True,
        max_optional_score_drop=0.5,
    )

    assert comparison["regression_detected"] is True
    assert any("optional score artifact_completeness dropped" in item for item in comparison["regressions"])
