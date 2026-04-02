import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "tests" / "scenario-evals" / "run_eval_tasks.py"
DATASET = REPO_ROOT / "tests" / "scenario-evals" / "datasets" / "golden_scenarios.json"
BASELINE = REPO_ROOT / "tests" / "scenario-evals" / "baselines" / "golden_scenarios_baseline.json"


def test_golden_scenarios_dataset_has_expected_shape():
    with DATASET.open(encoding="utf-8") as handle:
        scenarios = json.load(handle)

    assert len(scenarios) >= 7  # 5 original + techproducts + drupal

    for scenario in scenarios:
        assert "id" in scenario
        assert "title" in scenario
        assert "scenario" in scenario
        assert "expectations" in scenario
        assert "keyword_assertions" in scenario


def test_eval_runner_emits_structured_tasks_from_dataset():
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--dataset", str(DATASET)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    tasks = json.loads(result.stdout)
    assert len(tasks) >= 7  # 5 original + techproducts + drupal

    first = tasks[0]
    assert "scenario_id" in first
    assert "title" in first
    assert "judge_prompt" in first
    assert "input_scenario" in first
    assert "advisor_response" in first
    assert "expectations" in first
    assert "keyword_assertions" in first


def test_eval_runner_accepts_external_responses(tmp_path):
    responses_path = tmp_path / "responses.json"
    responses_path.write_text(
        json.dumps(
            {
                "legacy-solr4-custom-components": "Use a staged migration with validation and refactoring."
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(RUNNER), "--dataset", str(DATASET), "--responses", str(responses_path)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    tasks = json.loads(result.stdout)
    first = next(task for task in tasks if task["scenario_id"] == "legacy-solr4-custom-components")
    assert first["advisor_response"] == "Use a staged migration with validation and refactoring."


def test_golden_scenarios_include_techproducts_and_drupal():
    with DATASET.open(encoding="utf-8") as handle:
        scenarios = json.load(handle)

    ids = {s["id"] for s in scenarios}
    assert "techproducts-full-workflow" in ids, "Missing techproducts golden scenario"
    assert "drupal-full-workflow" in ids, "Missing drupal golden scenario"


def test_full_workflow_scenarios_have_extended_fields():
    with DATASET.open(encoding="utf-8") as handle:
        scenarios = json.load(handle)

    full_workflow = [s for s in scenarios if s.get("golden_scenario_ref")]
    assert len(full_workflow) >= 2

    for scenario in full_workflow:
        assert "persona" in scenario, f"{scenario['id']} missing persona"
        assert "complexity" in scenario, f"{scenario['id']} missing complexity"
        ref_path = REPO_ROOT / scenario["golden_scenario_ref"]
        assert ref_path.exists(), f"{scenario['id']} golden_scenario_ref points to missing file: {ref_path}"


def test_drupal_scenario_has_anti_patterns():
    with DATASET.open(encoding="utf-8") as handle:
        scenarios = json.load(handle)

    drupal = next(s for s in scenarios if s["id"] == "drupal-full-workflow")
    assert "anti_patterns" in drupal, "Drupal scenario should have anti_patterns"
    assert len(drupal["anti_patterns"]) >= 3


def test_techproducts_scenario_has_sufficient_expectations():
    with DATASET.open(encoding="utf-8") as handle:
        scenarios = json.load(handle)

    tp = next(s for s in scenarios if s["id"] == "techproducts-full-workflow")
    assert len(tp["expectations"]) >= 8, "TechProducts should have at least 8 expectations"
    assert len(tp["keyword_assertions"]) >= 5, "TechProducts should have at least 5 keyword assertions"


def test_eval_runner_requires_api_key_for_live_scoring():
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--dataset", str(DATASET), "--score"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--score requires --api-key or JUDGE_API_KEY" in result.stderr or "--score requires --api-key or JUDGE_API_KEY" in result.stdout


def test_checked_in_eval_baseline_exists_and_matches_dataset_shape():
    with DATASET.open(encoding="utf-8") as handle:
        scenarios = json.load(handle)
    with BASELINE.open(encoding="utf-8") as handle:
        baseline = json.load(handle)

    baseline_ids = {item["scenario_id"] for item in baseline["results"]}
    dataset_ids = {item["id"] for item in scenarios}

    assert BASELINE.exists()
    assert baseline["summary"]["scenario_count"] == len(scenarios)
    assert baseline_ids == dataset_ids


def test_eval_runner_can_compare_checked_in_baseline_to_itself(tmp_path):
    output_path = tmp_path / "baseline-compare.json"

    subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--dataset",
            str(DATASET),
            "--results-file",
            str(BASELINE),
            "--baseline",
            str(BASELINE),
            "--fail-on-regression",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    bundle = json.loads(output_path.read_text(encoding="utf-8"))
    assert bundle["baseline_comparison"]["regression_detected"] is False


def test_eval_runner_rejects_invalid_scored_results_file(tmp_path):
    bad_results_path = tmp_path / "bad-results.json"
    bad_results_path.write_text(
        json.dumps(
            [
                {
                    "scenario_id": "legacy-solr4-custom-components",
                    "title": "Legacy Solr 4.x with Custom Java Components",
                    "judge_output": {
                        "methodology_alignment": 9,
                        "expert_judgement": 4,
                        "heuristics": 4,
                        "risk_identification": 4,
                        "final_decision": "PASS"
                    }
                }
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--dataset",
            str(DATASET),
            "--results-file",
            str(bad_results_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "between 1 and 5 inclusive" in result.stderr or "between 1 and 5 inclusive" in result.stdout


def test_eval_runner_can_summarize_imported_results_and_persist_history(tmp_path):
    results_path = tmp_path / "results.json"
    output_path = tmp_path / "bundle.json"
    history_dir = tmp_path / "history"
    results_path.write_text(
        json.dumps(
            [
                {
                    "scenario_id": "legacy-solr4-custom-components",
                    "title": "Legacy Solr 4.x with Custom Java Components",
                    "judge_output": {
                        "methodology_alignment": 4,
                        "expert_judgement": 4,
                        "heuristics": 4,
                        "risk_identification": 5,
                        "final_decision": "PASS",
                        "rationale": "Solid coverage",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--dataset",
            str(DATASET),
            "--results-file",
            str(results_path),
            "--history-dir",
            str(history_dir),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    bundle = json.loads(output_path.read_text(encoding="utf-8"))
    assert bundle["summary"]["scenario_count"] == 1
    assert bundle["summary"]["pass_count"] == 1
    assert bundle["run_metadata"]["score_mode"] == "imported_results"
    assert (history_dir / "latest.json").exists()
    assert any((history_dir / "runs").iterdir())


def test_eval_runner_can_compare_against_baseline_and_fail_on_regression(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_results_path = tmp_path / "candidate-results.json"

    baseline_path.write_text(
        json.dumps(
            {
                "summary": {
                    "scenario_count": 1,
                    "scored_scenario_count": 1,
                    "pass_count": 1,
                    "fail_count": 0,
                    "pass_rate": 1.0,
                    "average_scores": {
                        "methodology_alignment": 5.0,
                        "expert_judgement": 5.0,
                        "heuristics": 5.0,
                        "risk_identification": 5.0,
                        "overall": 5.0,
                    },
                    "scenario_results": {
                        "legacy-solr4-custom-components": {
                            "title": "Legacy Solr 4.x with Custom Java Components",
                            "average_score": 5.0,
                            "final_decision": "PASS",
                            "scores": {
                                "methodology_alignment": 5.0,
                                "expert_judgement": 5.0,
                                "heuristics": 5.0,
                                "risk_identification": 5.0,
                            },
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    candidate_results_path.write_text(
        json.dumps(
            [
                {
                    "scenario_id": "legacy-solr4-custom-components",
                    "title": "Legacy Solr 4.x with Custom Java Components",
                    "judge_output": {
                        "methodology_alignment": 3,
                        "expert_judgement": 3,
                        "heuristics": 3,
                        "risk_identification": 3,
                        "final_decision": "FAIL",
                        "rationale": "Regressed result",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--dataset",
            str(DATASET),
            "--results-file",
            str(candidate_results_path),
            "--baseline",
            str(baseline_path),
            "--fail-on-regression",
            "--max-overall-score-drop",
            "0.1",
            "--max-pass-rate-drop",
            "0.0",
            "--max-scenario-score-drop",
            "0.1",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Regression detected against baseline" in result.stderr or "Regression detected against baseline" in result.stdout


def test_eval_runner_can_fail_on_instability(tmp_path):
    unstable_results_path = tmp_path / "unstable-results.json"
    unstable_results_path.write_text(
        json.dumps(
            [
                {
                    "scenario_id": "legacy-solr4-custom-components",
                    "title": "Legacy Solr 4.x with Custom Java Components",
                    "judge_output": {
                        "methodology_alignment": 4,
                        "expert_judgement": 4,
                        "heuristics": 4,
                        "risk_identification": 4,
                        "final_decision": "PASS",
                    },
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
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--dataset",
            str(DATASET),
            "--results-file",
            str(unstable_results_path),
            "--repeat-judge",
            "2",
            "--fail-on-instability",
            "--max-judge-average-score-spread",
            "0.5",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Judge instability detected" in result.stderr or "Judge instability detected" in result.stdout
