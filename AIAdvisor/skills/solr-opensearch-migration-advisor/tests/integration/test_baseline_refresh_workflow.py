import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMOTER = REPO_ROOT / "tests" / "scenario-evals" / "promote_eval_baseline.py"
DATASET = REPO_ROOT / "tests" / "scenario-evals" / "datasets" / "golden_scenarios.json"


def _candidate_payload():
    scenarios = json.loads(DATASET.read_text(encoding="utf-8"))
    results = []
    for scenario in scenarios:
        results.append(
            {
                "scenario_id": scenario["id"],
                "title": scenario["title"],
                "judge_output": {
                    "methodology_alignment": 4,
                    "expert_judgement": 4,
                    "heuristics": 4,
                    "risk_identification": 4,
                    "final_decision": "PASS",
                    "rationale": "Fixture candidate baseline.",
                },
            }
        )
    return {"results": results}


def test_promote_eval_baseline_creates_valid_baseline_file(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    output_path = tmp_path / "baseline.json"
    candidate_path.write_text(json.dumps(_candidate_payload()), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(PROMOTER),
            "--candidate",
            str(candidate_path),
            "--dataset",
            str(DATASET),
            "--output",
            str(output_path),
            "--note",
            "refresh after manual review",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    baseline = json.loads(output_path.read_text(encoding="utf-8"))
    assert str(output_path) in result.stdout
    assert baseline["baseline_metadata"]["promotion_note"] == "refresh after manual review"
    assert baseline["summary"]["scenario_count"] == len(json.loads(DATASET.read_text(encoding="utf-8")))


def test_promote_eval_baseline_rejects_incomplete_candidate(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    output_path = tmp_path / "baseline.json"
    candidate_path.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "scenario_id": "legacy-solr4-custom-components",
                        "title": "Legacy Solr 4.x with Custom Java Components",
                        "judge_output": {
                            "methodology_alignment": 4,
                            "expert_judgement": 4,
                            "heuristics": 4,
                            "risk_identification": 4,
                            "final_decision": "PASS",
                            "rationale": "Only one scenario present.",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PROMOTER),
            "--candidate",
            str(candidate_path),
            "--dataset",
            str(DATASET),
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "missing scenarios" in result.stderr or "missing scenarios" in result.stdout
