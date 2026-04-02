from run_eval_tasks import (
    aggregate_judge_runs,
    evaluate_stability,
    summarize_judge_run_stability,
)


def test_aggregate_judge_runs_averages_scores_and_uses_majority_decision():
    judge_runs = [
        {
            "methodology_alignment": 5,
            "expert_judgement": 4,
            "heuristics": 4,
            "risk_identification": 5,
            "final_decision": "PASS",
        },
        {
            "methodology_alignment": 3,
            "expert_judgement": 4,
            "heuristics": 4,
            "risk_identification": 3,
            "final_decision": "FAIL",
        },
        {
            "methodology_alignment": 4,
            "expert_judgement": 4,
            "heuristics": 5,
            "risk_identification": 4,
            "final_decision": "PASS",
        },
    ]
    aggregated = aggregate_judge_runs(judge_runs)

    assert aggregated["methodology_alignment"] == 4.0
    assert aggregated["risk_identification"] == 4.0
    assert aggregated["final_decision"] == "PASS"


def test_summarize_judge_run_stability_reports_spread_and_consensus():
    judge_runs = [
        {
            "methodology_alignment": 5,
            "expert_judgement": 4,
            "heuristics": 4,
            "risk_identification": 5,
            "final_decision": "PASS",
        },
        {
            "methodology_alignment": 4,
            "expert_judgement": 4,
            "heuristics": 5,
            "risk_identification": 3,
            "final_decision": "PASS",
        },
    ]
    stability = summarize_judge_run_stability(judge_runs)

    assert stability["run_count"] == 2
    assert stability["decision_consensus"] is True
    assert stability["score_spread"]["methodology_alignment"] == 1.0
    assert stability["average_score_spread"] == 0.5


def test_evaluate_stability_flags_spread_and_disagreement():
    results = [
        {
            "scenario_id": "scenario-a",
            "stability_summary": {
                "run_count": 2,
                "decision_consensus": False,
                "decision_set": ["FAIL", "PASS"],
                "score_spread": {
                    "methodology_alignment": 1.0,
                    "expert_judgement": 0.0,
                    "heuristics": 0.0,
                    "risk_identification": 1.0,
                },
                "average_score_spread": 1.0,
            }
        }
    ]
    stability = evaluate_stability(
        results,
        max_average_score_spread=0.5,
        allow_decision_disagreement=False,
    )

    assert stability["instability_detected"] is True
    assert any("average judge score spread" in issue for issue in stability["issues"])
    assert any("decision disagreement" in issue for issue in stability["issues"])
