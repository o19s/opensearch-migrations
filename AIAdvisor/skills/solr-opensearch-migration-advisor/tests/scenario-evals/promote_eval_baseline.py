"""
Promote a reviewed scored eval run to the checked-in baseline.

A baseline is a JSON file (``baselines/golden_scenarios_baseline.json``) that
``run_eval_tasks.py`` compares against during regression checks.  Promoting a
new baseline replaces that file with a reviewed scored run.

Workflow
--------
1. Produce a scored run bundle via ``run_eval_tasks.py --score --history-dir``.
2. Review the score deltas and rationale manually.
3. If the run is acceptable, run this script to promote it::

       python promote_eval_baseline.py \\
           --candidate tests/evals/history/runs/<timestamp>.json \\
           --dataset tests/evals/datasets/golden_scenarios.json \\
           --output tests/evals/baselines/golden_scenarios_baseline.json \\
           --note "improved reference X"

The script validates that the candidate covers exactly the same set of scenario
IDs as the dataset before writing anything.

Do not promote a baseline without a manual review — the checked-in baseline is
the regression gate that CI compares against on every change.
"""

import argparse
import json
from pathlib import Path

from judge_migration_advice import load_scenarios
from run_eval_tasks import summarize_scored_results, validate_scored_results


def load_candidate_payload(path: Path) -> dict:
    """Load and normalise a candidate scored-run file into a promotion payload.

    Accepts either a full run bundle (``{"results": [...], "summary": {...}}``)
    or a bare results list (``[...]``).  In both cases the results are
    re-validated through :func:`~run_eval_tasks.validate_scored_results` and a
    fresh summary is computed if one is absent.

    Args:
        path: Path to the candidate scored-run file.

    Returns:
        Dict with keys ``summary``, ``results``, and ``source_run_metadata``.

    Raises:
        ValueError: If the file shape is not recognised.
    """
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        results = validate_scored_results(payload["results"])
        summary = payload.get("summary") or summarize_scored_results(results)
        metadata = payload.get("run_metadata", {})
    elif isinstance(payload, list):
        results = validate_scored_results(payload)
        summary = summarize_scored_results(results)
        metadata = {}
    else:
        raise ValueError(f"Unsupported candidate payload shape in {path}")

    return {
        "summary": summary,
        "results": results,
        "source_run_metadata": metadata,
    }


def validate_candidate_against_dataset(candidate: dict, dataset_path: Path) -> None:
    """Assert that the candidate covers exactly the scenarios in the dataset.

    Checks for missing scenarios (dataset IDs not in candidate results) and
    extra scenarios (candidate result IDs not in the dataset).  Also verifies
    that ``summary.scenario_count`` matches the dataset size.

    Raises:
        ValueError: If the candidate has missing or extra scenarios, or if the
                    scenario count in the summary does not match the dataset.
    """
    scenarios = load_scenarios(dataset_path)
    dataset_ids = {item["id"] for item in scenarios}
    result_ids = {item["scenario_id"] for item in candidate["results"]}

    missing = dataset_ids - result_ids
    extra = result_ids - dataset_ids
    if missing:
        raise ValueError(f"Candidate baseline is missing scenarios: {sorted(missing)}")
    if extra:
        raise ValueError(f"Candidate baseline has unknown scenarios: {sorted(extra)}")

    if candidate["summary"]["scenario_count"] != len(scenarios):
        raise ValueError(
            "Candidate baseline summary scenario_count does not match dataset size"
        )


def build_promoted_baseline(candidate: dict, source_path: Path, note: str | None) -> dict:
    """Assemble the baseline dict that will be written to the output file.

    Adds ``baseline_metadata`` with provenance info (source path, promotion
    note, and the original run metadata if available) so that future readers
    can trace where the baseline came from.

    Args:
        candidate:   Normalised candidate payload from :func:`load_candidate_payload`.
        source_path: Path the candidate was loaded from (recorded as provenance).
        note:        Optional short description of why the baseline is changing.

    Returns:
        Dict with keys ``baseline_metadata``, ``summary``, and ``results``.
    """
    promoted = {
        "baseline_metadata": {
            "promoted_from": str(source_path),
            "promotion_note": note,
        },
        "summary": candidate["summary"],
        "results": candidate["results"],
    }
    if candidate.get("source_run_metadata"):
        promoted["baseline_metadata"]["source_run_metadata"] = candidate["source_run_metadata"]
    return promoted


def main():
    parser = argparse.ArgumentParser(description="Promote a reviewed scored run to the checked-in eval baseline.")
    parser.add_argument("--candidate", type=Path, required=True, help="Path to a scored run bundle or results file.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).resolve().parent / "datasets" / "golden_scenarios.json",
        help="Dataset used to validate baseline scenario coverage.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "baselines" / "golden_scenarios_baseline.json",
        help="Output baseline file path.",
    )
    parser.add_argument(
        "--note",
        default=None,
        help="Optional short note describing why the baseline is being refreshed.",
    )
    args = parser.parse_args()

    candidate = load_candidate_payload(args.candidate)
    validate_candidate_against_dataset(candidate, args.dataset)
    promoted = build_promoted_baseline(candidate, args.candidate, args.note)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(promoted, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
