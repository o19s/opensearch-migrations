import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "tests" / "scenario-evals" / "run_end_to_end_skill_eval.py"


def test_end_to_end_eval_flow_emits_response_payload(tmp_path):
    output_path = tmp_path / "e2e-response.json"
    subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--scenario-id",
            "techproducts-full-workflow",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["scenario_id"] == "techproducts-full-workflow"
    response = payload["responses"]["techproducts-full-workflow"]
    assert "Solr to OpenSearch Migration Report" in response
    assert "SolrJ" in response


def test_end_to_end_eval_flow_supports_drupal_scenario(tmp_path):
    output_path = tmp_path / "e2e-drupal-response.json"
    subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--scenario-id",
            "drupal-full-workflow",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    response = payload["responses"]["drupal-full-workflow"]
    assert "Solr to OpenSearch Migration Report" in response
    assert "Drupal Search API" in response
    assert "module migration" in response.lower() or "drupal" in response.lower()
