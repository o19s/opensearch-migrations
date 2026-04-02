"""
Eval task runner for the Solr-to-OpenSearch migration advisor.

This script drives the full eval pipeline from golden scenarios to scored
results, baseline comparison, and history persistence. It can be used in
three distinct modes:

**Task-emit mode** (default, no ``--score`` or ``--results-file``)
    Generates structured eval tasks from the golden dataset and prints them
    as JSON. Placeholder advisor responses are used unless ``--responses``
    points to a real responses file.

**Live-score mode** (``--score``)
    Sends generated eval tasks to an OpenAI-compatible judge backend and
    returns scored results. Requires ``--api-key`` (or ``JUDGE_API_KEY``).
    Supports ``--repeat-judge N`` to call the judge N times per task and
    measure scoring stability.

**Import mode** (``--results-file``)
    Loads pre-scored results from a file, validates them, and builds a run
    bundle — useful when scoring happens outside this script.

In both live-score and import modes the script can:

* **Compare against a baseline** (``--baseline``) and optionally fail on
  regression (``--fail-on-regression``).
* **Persist a run bundle** (``--history-dir``) as a timestamped JSON file
  alongside ``history/latest.json``.
* **Check judge stability** when ``--repeat-judge > 1`` and optionally fail
  on excessive score spread (``--fail-on-instability``).

Typical usage
-------------
Emit tasks::

    python run_eval_tasks.py --dataset datasets/golden_scenarios.json

Score with a live judge and persist::

    python run_eval_tasks.py \\
        --dataset datasets/golden_scenarios.json \\
        --responses /path/to/responses.json \\
        --score \\
        --history-dir history \\
        --run-label my-change

Compare against baseline::

    python run_eval_tasks.py \\
        --dataset datasets/golden_scenarios.json \\
        --results-file /path/to/scored.json \\
        --baseline baselines/golden_scenarios_baseline.json \\
        --fail-on-regression

Environment variables
---------------------
``JUDGE_API_KEY``
    API key for the judge backend (overridden by ``--api-key``).
``JUDGE_API_BASE``
    Base URL for the OpenAI-compatible backend (default: OpenAI).
``JUDGE_MODEL``
    Model name to use for judging (default: ``gpt-4o-mini``).
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError

from judge_migration_advice import (
    DATASET_PATH,
    generate_eval_task_from_scenario_record,
    load_scenarios,
)

SCORE_FIELDS = (
    "methodology_alignment",
    "expert_judgement",
    "heuristics",
    "risk_identification",
)
OPTIONAL_SCORE_FIELDS = (
    "artifact_completeness",
    "approval_discipline",
    "consumer_impact_awareness",
    "cutover_readiness",
    "follow_up_quality",
    "persona_appropriateness",
    "scope_discipline",
)
ALLOWED_FINAL_DECISIONS = {"PASS", "FAIL"}


def build_placeholder_response(record: dict) -> str:
    """Return a stub advisor response for a scenario record.

    Used when no real responses file is provided. The stub text is
    recognisable as a placeholder so accidental judge scoring of unreal
    responses is obvious in results.
    """
    return (
        "Placeholder advisor response for eval scaffolding. "
        f"Scenario: {record['title']}. "
        "Replace this with a real advisor output before sending to an LLM judge."
    )


def build_eval_tasks(dataset_path: Path):
    scenarios = load_scenarios(dataset_path)
    tasks = []
    for record in scenarios:
        tasks.append(
            generate_eval_task_from_scenario_record(
                record=record,
                advisor_response=build_placeholder_response(record),
            )
        )
    return tasks


def load_advisor_responses(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_eval_tasks_with_responses(dataset_path: Path, responses_path: Path | None = None):
    scenarios = load_scenarios(dataset_path)
    responses = load_advisor_responses(responses_path)
    tasks = []
    for record in scenarios:
        advisor_response = responses.get(record["id"], build_placeholder_response(record))
        tasks.append(
            generate_eval_task_from_scenario_record(
                record=record,
                advisor_response=advisor_response,
            )
        )
    return tasks


def build_judge_messages(task: dict) -> list[dict]:
    expectations = "\n".join(f"- {item}" for item in task.get("expectations", []))
    keywords = "\n".join(f"- {item}" for item in task.get("keyword_assertions", []))
    artifact_expectations = "\n".join(f"- {item}" for item in task.get("artifact_expectations", []))
    anti_patterns = "\n".join(f"- {item}" for item in task.get("anti_patterns", []))

    # Build context section for persona/response-type metadata
    context_parts = []
    if task.get("persona"):
        context_parts.append(f"Persona: {task['persona']}")
    if task.get("expected_response_type"):
        context_parts.append(f"Expected response type: {task['expected_response_type']}")
    if task.get("category"):
        context_parts.append(f"Category: {task['category']}")
    context_section = "\n".join(context_parts)

    user_prompt = (
        f"Scenario ID: {task.get('scenario_id')}\n"
        f"Title: {task.get('title')}\n\n"
    )
    if context_section:
        user_prompt += f"Context:\n{context_section}\n\n"
    user_prompt += (
        f"Scenario:\n{task['input_scenario']}\n\n"
        f"Advisor Response:\n{task['advisor_response']}\n\n"
        f"Expected qualities:\n{expectations or '- None provided'}\n\n"
        f"Keyword assertions:\n{keywords or '- None provided'}\n\n"
        f"Artifact expectations:\n{artifact_expectations or '- None provided'}\n\n"
    )
    if anti_patterns:
        user_prompt += f"Anti-patterns (the advisor must NOT do these):\n{anti_patterns}\n\n"
    user_prompt += (
        "Return ONLY valid JSON matching this exact schema — no markdown, no extra text:\n"
        "{\n"
        '  "methodology_alignment": <integer 1-5>,\n'
        '  "expert_judgement": <integer 1-5>,\n'
        '  "heuristics": <integer 1-5>,\n'
        '  "risk_identification": <integer 1-5>,\n'
        '  "final_decision": "PASS" or "FAIL",\n'
        '  "rationale": "<one paragraph explanation>"\n'
        "}\n"
        "If the response is artifact-heavy, also include any relevant optional integer fields: "
        "artifact_completeness, approval_discipline, consumer_impact_awareness, cutover_readiness.\n"
        "If the scenario tests advisor interaction quality (follow-up questions, persona calibration, "
        "scope management), also include any relevant optional integer fields: "
        "follow_up_quality, persona_appropriateness, scope_discipline."
    )
    return [
        {"role": "system", "content": task["judge_prompt"]},
        {"role": "user", "content": user_prompt},
    ]


def _score_task_once(task: dict, api_base: str, api_key: str, model: str) -> dict:
    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": build_judge_messages(task),
    }
    req = request.Request(
        url=f"{api_base.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            raw = json.load(response)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Judge backend returned HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Judge backend connection failed: {exc}") from exc

    content = raw["choices"][0]["message"]["content"]
    judge_output = normalize_judge_output(json.loads(content))
    return judge_output


def score_task_with_openai_compatible_backend(
    task: dict,
    api_base: str,
    api_key: str,
    model: str,
    repeat_judge: int = 1,
) -> dict:
    judge_runs = [
        _score_task_once(task, api_base, api_key, model)
        for _ in range(repeat_judge)
    ]
    result = {
        "scenario_id": task.get("scenario_id"),
        "title": task.get("title"),
        "judge_output": aggregate_judge_runs(judge_runs),
    }
    if repeat_judge > 1:
        result["judge_runs"] = judge_runs
        result["stability_summary"] = summarize_judge_run_stability(judge_runs)
    return result


def evaluate_tasks(
    tasks: list[dict],
    api_base: str,
    api_key: str,
    model: str,
    repeat_judge: int = 1,
) -> list[dict]:
    return [
        score_task_with_openai_compatible_backend(
            task, api_base, api_key, model, repeat_judge
        )
        for task in tasks
    ]


def coerce_score(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.strip())
    raise ValueError(f"Cannot coerce score value {value!r} to float")


def validate_score_range(field: str, value: float) -> float:
    if not 1.0 <= value <= 5.0:
        raise ValueError(
            f"Judge output field {field} must be between 1 and 5 inclusive, got {value!r}"
        )
    return value


def normalize_judge_output(judge_output: dict) -> dict:
    """Validate and normalise a raw judge response dict.

    Ensures every required score field is present, coerces scores to floats,
    validates that values are in the 1–5 range, normalises ``final_decision``
    to uppercase, and computes ``average_score`` across the four required
    dimensions. Optional artifact-score fields are normalised if present and
    an ``artifact_average_score`` is added when any are found.

    Args:
        judge_output: Raw dict returned by the judge backend's JSON response.

    Returns:
        Normalised dict with guaranteed types and computed averages.

    Raises:
        ValueError: If a required field is missing, a score is out of range, or
                    ``final_decision`` is not ``"PASS"`` or ``"FAIL"``.
    """
    normalized = dict(judge_output)
    for field in SCORE_FIELDS:
        if field not in normalized:
            raise ValueError(f"Judge output missing required field: {field}")
        normalized[field] = validate_score_range(field, coerce_score(normalized[field]))

    optional_scores = {}
    for field in OPTIONAL_SCORE_FIELDS:
        if field in normalized:
            optional_scores[field] = validate_score_range(field, coerce_score(normalized[field]))
            normalized[field] = optional_scores[field]

    final_decision = str(normalized.get("final_decision", "")).strip().upper()
    if final_decision not in ALLOWED_FINAL_DECISIONS:
        raise ValueError(
            "Judge output final_decision must be PASS or FAIL, "
            f"got {normalized.get('final_decision')!r}"
        )
    normalized["final_decision"] = final_decision
    normalized["average_score"] = round(
        sum(normalized[field] for field in SCORE_FIELDS) / len(SCORE_FIELDS),
        4,
    )
    if optional_scores:
        normalized["artifact_average_score"] = round(
            sum(optional_scores.values()) / len(optional_scores),
            4,
        )
    return normalized


def summarize_scored_results(results: list[dict]) -> dict:
    if not results:
        return {
            "scenario_count": 0,
            "scored_scenario_count": 0,
            "pass_count": 0,
            "fail_count": 0,
            "pass_rate": 0.0,
            "average_scores": {field: 0.0 for field in (*SCORE_FIELDS, "overall")},
            "scenario_results": {},
        }

    totals = {field: 0.0 for field in SCORE_FIELDS}
    scenario_results = {}
    pass_count = 0
    fail_count = 0

    for result in results:
        normalized = normalize_judge_output(result["judge_output"])
        scenario_id = result.get("scenario_id") or result.get("title") or f"scenario-{len(scenario_results)+1}"
        scenario_results[scenario_id] = {
            "title": result.get("title"),
            "average_score": normalized["average_score"],
            "final_decision": normalized["final_decision"],
            "scores": {field: normalized[field] for field in SCORE_FIELDS},
        }

        for field in SCORE_FIELDS:
            totals[field] += normalized[field]

        if normalized["final_decision"] == "PASS":
            pass_count += 1
        else:
            fail_count += 1

    scenario_count = len(results)
    average_scores = {
        field: round(totals[field] / scenario_count, 4)
        for field in SCORE_FIELDS
    }
    average_scores["overall"] = round(
        sum(scenario["average_score"] for scenario in scenario_results.values()) / scenario_count,
        4,
    )

    return {
        "scenario_count": scenario_count,
        "scored_scenario_count": scenario_count,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": round(pass_count / scenario_count, 4),
        "average_scores": average_scores,
        "average_optional_scores": summarize_optional_scores(results),
        "scenario_results": scenario_results,
    }


def summarize_optional_scores(results: list[dict]) -> dict:
    totals = {field: 0.0 for field in OPTIONAL_SCORE_FIELDS}
    counts = {field: 0 for field in OPTIONAL_SCORE_FIELDS}

    for result in results:
        normalized = normalize_judge_output(result["judge_output"])
        for field in OPTIONAL_SCORE_FIELDS:
            if field in normalized:
                totals[field] += normalized[field]
                counts[field] += 1

    return {
        field: round(totals[field] / counts[field], 4)
        for field in OPTIONAL_SCORE_FIELDS
        if counts[field] > 0
    }


def load_scored_results_payload(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("results"), list):
            return payload["results"]
        if isinstance(payload.get("output"), list):
            return payload["output"]

    raise ValueError(f"Unsupported scored-results payload shape in {path}")


def validate_scored_results(results: list[dict]) -> list[dict]:
    validated = []
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            raise ValueError(f"Scored result at index {index} is not an object")
        if "judge_output" not in result:
            raise ValueError(f"Scored result at index {index} is missing judge_output")
        validated_result = dict(result)
        validated_result["judge_output"] = normalize_judge_output(result["judge_output"])
        validated.append(validated_result)
    return validated


def aggregate_judge_runs(judge_runs: list[dict]) -> dict:
    """Combine multiple judge runs for a single task into one aggregated result.

    Scores are averaged across all runs. The ``final_decision`` is determined
    by majority vote: PASS wins ties. This is used when ``--repeat-judge > 1``
    to produce a stable single result per task.

    Args:
        judge_runs: List of normalised judge output dicts (at least one).

    Returns:
        A single aggregated judge output dict suitable for use as
        ``result["judge_output"]``.

    Raises:
        ValueError: If ``judge_runs`` is empty.
    """
    if not judge_runs:
        raise ValueError("judge_runs must not be empty")

    normalized_runs = [normalize_judge_output(run) for run in judge_runs]
    aggregated = {}
    for field in SCORE_FIELDS:
        aggregated[field] = round(
            sum(run[field] for run in normalized_runs) / len(normalized_runs),
            4,
        )

    pass_count = sum(1 for run in normalized_runs if run["final_decision"] == "PASS")
    fail_count = len(normalized_runs) - pass_count
    aggregated["final_decision"] = "PASS" if pass_count >= fail_count else "FAIL"
    aggregated["rationale"] = f"Aggregated from {len(normalized_runs)} judge runs."
    aggregated["average_score"] = round(
        sum(run["average_score"] for run in normalized_runs) / len(normalized_runs),
        4,
    )
    return aggregated


def summarize_judge_run_stability(judge_runs: list[dict]) -> dict:
    """Compute a stability summary across repeated judge runs for one task.

    Measures how much individual dimension scores varied between runs and
    whether all runs agreed on the PASS/FAIL decision. A high
    ``average_score_spread`` or ``decision_consensus=False`` signals that
    the judge is noisy for this task and the result should be treated with
    caution.

    Args:
        judge_runs: List of normalised judge output dicts.  Returns a trivial
                    summary (zero spread, full consensus) for a single run.

    Returns:
        Dict with keys: ``run_count``, ``decision_consensus``,
        ``decision_set``, ``score_spread`` (per dimension), and
        ``average_score_spread``.
    """
    if len(judge_runs) < 2:
        return {
            "run_count": len(judge_runs),
            "decision_consensus": True,
            "score_spread": {field: 0.0 for field in SCORE_FIELDS},
            "average_score_spread": 0.0,
        }

    normalized_runs = [normalize_judge_output(run) for run in judge_runs]
    score_spread = {}
    for field in SCORE_FIELDS:
        values = [run[field] for run in normalized_runs]
        score_spread[field] = round(max(values) - min(values), 4)

    decisions = {run["final_decision"] for run in normalized_runs}
    return {
        "run_count": len(normalized_runs),
        "decision_consensus": len(decisions) == 1,
        "decision_set": sorted(decisions),
        "score_spread": score_spread,
        "average_score_spread": round(
            max(run["average_score"] for run in normalized_runs)
            - min(run["average_score"] for run in normalized_runs),
            4,
        ),
    }


def load_summary_payload(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict) and isinstance(payload.get("summary"), dict):
        return payload["summary"]
    if isinstance(payload, list):
        return summarize_scored_results(payload)

    raise ValueError(f"Unsupported baseline payload shape in {path}")


def compare_summaries(
    candidate_summary: dict,
    baseline_summary: dict,
    *,
    max_overall_score_drop: float,
    max_pass_rate_drop: float,
    max_scenario_score_drop: float,
    use_optional_scores_in_regression: bool = False,
    max_optional_score_drop: float = 0.5,
) -> dict:
    """Compare a candidate run summary against a baseline and detect regressions.

    Three checks are applied:

    1. **Overall average score drop** — the candidate's average across all
       scenarios must not fall more than ``max_overall_score_drop`` below the
       baseline.
    2. **Pass-rate drop** — the fraction of PASS decisions must not fall more
       than ``max_pass_rate_drop``.
    3. **Per-scenario score drop** — no individual scenario's average score may
       drop more than ``max_scenario_score_drop``; a scenario that was PASS in
       the baseline must not become FAIL.

    When ``use_optional_scores_in_regression=True``, shared optional
    artifact-score averages are also compared against ``max_optional_score_drop``.

    Args:
        candidate_summary:  Summary dict from the current run.
        baseline_summary:   Summary dict from the checked-in baseline.
        max_overall_score_drop:    Maximum tolerated drop in overall average score.
        max_pass_rate_drop:        Maximum tolerated drop in pass rate.
        max_scenario_score_drop:   Maximum tolerated per-scenario score drop.
        use_optional_scores_in_regression: Whether to include optional artifact
                                   scores in regression checks.
        max_optional_score_drop:   Maximum tolerated drop in any optional score.

    Returns:
        Dict with keys: ``regression_detected`` (bool), ``thresholds``,
        ``metrics``, and ``regressions`` (list of human-readable descriptions).
    """
    regressions = []
    candidate_overall = candidate_summary["average_scores"]["overall"]
    baseline_overall = baseline_summary["average_scores"]["overall"]
    overall_drop = round(baseline_overall - candidate_overall, 4)
    if overall_drop > max_overall_score_drop:
        regressions.append(
            f"overall average score dropped by {overall_drop:.4f} "
            f"(allowed {max_overall_score_drop:.4f})"
        )

    candidate_pass_rate = candidate_summary["pass_rate"]
    baseline_pass_rate = baseline_summary["pass_rate"]
    pass_rate_drop = round(baseline_pass_rate - candidate_pass_rate, 4)
    if pass_rate_drop > max_pass_rate_drop:
        regressions.append(
            f"pass rate dropped by {pass_rate_drop:.4f} "
            f"(allowed {max_pass_rate_drop:.4f})"
        )

    candidate_scenarios = candidate_summary.get("scenario_results", {})
    baseline_scenarios = baseline_summary.get("scenario_results", {})

    for scenario_id, baseline_scenario in baseline_scenarios.items():
        candidate_scenario = candidate_scenarios.get(scenario_id)
        if candidate_scenario is None:
            regressions.append(f"scenario missing from candidate run: {scenario_id}")
            continue

        score_drop = round(
            baseline_scenario["average_score"] - candidate_scenario["average_score"],
            4,
        )
        if score_drop > max_scenario_score_drop:
            regressions.append(
                f"scenario {scenario_id} average score dropped by {score_drop:.4f} "
                f"(allowed {max_scenario_score_drop:.4f})"
            )

        if (
            baseline_scenario["final_decision"] == "PASS"
            and candidate_scenario["final_decision"] != "PASS"
        ):
            regressions.append(
                f"scenario {scenario_id} changed decision from PASS to "
                f"{candidate_scenario['final_decision']}"
            )

    optional_metrics = {}
    if use_optional_scores_in_regression:
        candidate_optional = candidate_summary.get("average_optional_scores", {})
        baseline_optional = baseline_summary.get("average_optional_scores", {})
        shared_optional_fields = set(candidate_optional) & set(baseline_optional)
        for field in sorted(shared_optional_fields):
            drop = round(baseline_optional[field] - candidate_optional[field], 4)
            optional_metrics[f"{field}_drop"] = drop
            if drop > max_optional_score_drop:
                regressions.append(
                    f"optional score {field} dropped by {drop:.4f} "
                    f"(allowed {max_optional_score_drop:.4f})"
                )

    return {
        "regression_detected": bool(regressions),
        "thresholds": {
            "max_overall_score_drop": max_overall_score_drop,
            "max_pass_rate_drop": max_pass_rate_drop,
            "max_scenario_score_drop": max_scenario_score_drop,
            "use_optional_scores_in_regression": use_optional_scores_in_regression,
            "max_optional_score_drop": max_optional_score_drop,
        },
        "metrics": {
            "candidate_overall_average": candidate_overall,
            "baseline_overall_average": baseline_overall,
            "overall_score_drop": overall_drop,
            "candidate_pass_rate": candidate_pass_rate,
            "baseline_pass_rate": baseline_pass_rate,
            "pass_rate_drop": pass_rate_drop,
            **optional_metrics,
        },
        "regressions": regressions,
    }


def evaluate_stability(
    results: list[dict],
    *,
    max_average_score_spread: float,
    allow_decision_disagreement: bool,
) -> dict:
    """Check whether repeated judge runs were stable across all scored tasks.

    Iterates over results that have a ``stability_summary`` (populated when
    ``--repeat-judge > 1``) and flags any scenario where the average score
    spread exceeds ``max_average_score_spread`` or where the judge disagreed
    on PASS/FAIL (if ``allow_decision_disagreement=False``).

    Args:
        results:                    List of scored result dicts from the runner.
        max_average_score_spread:   Maximum allowed spread between the highest
                                    and lowest average scores across judge runs.
        allow_decision_disagreement: If False, any PASS/FAIL disagreement across
                                    runs is treated as an instability issue.

    Returns:
        Dict with keys: ``instability_detected`` (bool), ``thresholds``,
        ``scenario_summaries``, and ``issues`` (list of descriptions).
    """
    issues = []
    scenario_summaries = {}
    for result in results:
        stability = result.get("stability_summary")
        if not stability:
            continue
        scenario_id = result.get("scenario_id") or result.get("title")
        scenario_summaries[scenario_id] = stability
        if stability["average_score_spread"] > max_average_score_spread:
            issues.append(
                f"scenario {scenario_id} average judge score spread was "
                f"{stability['average_score_spread']:.4f} "
                f"(allowed {max_average_score_spread:.4f})"
            )
        if not allow_decision_disagreement and not stability["decision_consensus"]:
            issues.append(
                f"scenario {scenario_id} had judge decision disagreement: "
                f"{', '.join(stability.get('decision_set', []))}"
            )

    return {
        "instability_detected": bool(issues),
        "thresholds": {
            "max_average_score_spread": max_average_score_spread,
            "allow_decision_disagreement": allow_decision_disagreement,
        },
        "scenario_summaries": scenario_summaries,
        "issues": issues,
    }


def build_run_bundle(
    results: list[dict],
    *,
    dataset_path: Path,
    responses_path: Path | None,
    model: str | None,
    api_base: str | None,
    run_label: str | None,
    score_mode: str,
) -> dict:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "run_metadata": {
            "created_at": timestamp,
            "dataset_path": str(dataset_path),
            "responses_path": str(responses_path) if responses_path is not None else None,
            "model": model,
            "api_base": api_base,
            "run_label": run_label,
            "score_mode": score_mode,
        },
        "summary": summarize_scored_results(results),
        "results": results,
    }


def persist_run_bundle(history_dir: Path, bundle: dict) -> Path:
    """Write a run bundle to ``history_dir/runs/<timestamp>[-label].json``.

    Also writes ``history_dir/latest.json`` as a stable pointer to the most
    recent run. Both paths are created if they do not exist.

    Args:
        history_dir: Root directory for eval history.
        bundle:      Run bundle dict as returned by :func:`build_run_bundle`.

    Returns:
        Path to the timestamped run file that was written.
    """
    history_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = history_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = bundle["run_metadata"]["created_at"].replace(":", "").replace("+00:00", "Z")
    label = bundle["run_metadata"].get("run_label")
    safe_label = ""
    if label:
        safe_label = "-" + "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in label)

    run_path = runs_dir / f"{timestamp}{safe_label}.json"
    run_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    (history_dir / "latest.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    return run_path


def main():
    parser = argparse.ArgumentParser(description="Build structured eval tasks from golden migration scenarios.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATASET_PATH,
        help="Path to the golden scenarios dataset JSON file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the generated JSON output.",
    )
    parser.add_argument(
        "--responses",
        type=Path,
        default=None,
        help="Optional JSON file mapping scenario IDs to advisor responses.",
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=None,
        help="Optional JSON file containing scored eval results to summarize or compare.",
    )
    parser.add_argument(
        "--score",
        action="store_true",
        help="Send generated tasks to an OpenAI-compatible judge backend for live scoring.",
    )
    parser.add_argument(
        "--api-base",
        default=os.environ.get("JUDGE_API_BASE", "https://api.openai.com/v1"),
        help="Base URL for an OpenAI-compatible chat completions backend.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("JUDGE_API_KEY"),
        help="API key for the judge backend. Defaults to JUDGE_API_KEY.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("JUDGE_MODEL", "gpt-4o-mini"),
        help="Judge model name. Defaults to JUDGE_MODEL or gpt-4o-mini.",
    )
    parser.add_argument(
        "--repeat-judge",
        type=int,
        default=1,
        help="How many times to score each task with the judge to measure stability.",
    )
    parser.add_argument(
        "--history-dir",
        type=Path,
        default=None,
        help="Optional directory to store timestamped scored eval bundles and latest.json.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Optional prior scored-results file or run bundle to compare against.",
    )
    parser.add_argument(
        "--run-label",
        default=None,
        help="Optional short label to include in persisted history filenames.",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit non-zero when baseline comparison detects a regression.",
    )
    parser.add_argument(
        "--max-overall-score-drop",
        type=float,
        default=0.25,
        help="Allowed drop in overall average score before flagging regression.",
    )
    parser.add_argument(
        "--max-pass-rate-drop",
        type=float,
        default=0.05,
        help="Allowed drop in overall pass rate before flagging regression.",
    )
    parser.add_argument(
        "--max-scenario-score-drop",
        type=float,
        default=0.5,
        help="Allowed drop in a single scenario average score before flagging regression.",
    )
    parser.add_argument(
        "--use-optional-scores-in-regression",
        action="store_true",
        help="Include optional artifact-oriented scores when comparing against a baseline.",
    )
    parser.add_argument(
        "--max-optional-score-drop",
        type=float,
        default=0.5,
        help="Allowed drop in a summary optional score before flagging regression.",
    )
    parser.add_argument(
        "--fail-on-instability",
        action="store_true",
        help="Exit non-zero when repeat-judge stability exceeds configured thresholds.",
    )
    parser.add_argument(
        "--max-judge-average-score-spread",
        type=float,
        default=0.75,
        help="Allowed average-score spread across repeated judge runs before flagging instability.",
    )
    parser.add_argument(
        "--allow-judge-decision-disagreement",
        action="store_true",
        help="If set, repeated judge runs may disagree on PASS/FAIL without triggering instability.",
    )
    args = parser.parse_args()

    if args.score and args.results_file is not None:
        raise SystemExit("--score and --results-file are mutually exclusive")
    if args.repeat_judge < 1:
        raise SystemExit("--repeat-judge must be >= 1")

    if args.results_file is not None:
        results = validate_scored_results(load_scored_results_payload(args.results_file))
        bundle = build_run_bundle(
            results,
            dataset_path=args.dataset,
            responses_path=args.responses,
            model=args.model,
            api_base=args.api_base,
            run_label=args.run_label,
            score_mode="imported_results",
        )
    elif args.score:
        if not args.api_key:
            raise SystemExit("--score requires --api-key or JUDGE_API_KEY")
        tasks = build_eval_tasks_with_responses(args.dataset, args.responses)
        results = evaluate_tasks(
            tasks,
            args.api_base,
            args.api_key,
            args.model,
            repeat_judge=args.repeat_judge,
        )
        bundle = build_run_bundle(
            results,
            dataset_path=args.dataset,
            responses_path=args.responses,
            model=args.model,
            api_base=args.api_base,
            run_label=args.run_label,
            score_mode="live_judge",
        )
    else:
        output_obj = build_eval_tasks_with_responses(args.dataset, args.responses)
        output = json.dumps(output_obj, indent=2)

        if args.output is not None:
            args.output.write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return

    if args.baseline is not None:
        bundle["baseline_comparison"] = compare_summaries(
            bundle["summary"],
            load_summary_payload(args.baseline),
            max_overall_score_drop=args.max_overall_score_drop,
            max_pass_rate_drop=args.max_pass_rate_drop,
            max_scenario_score_drop=args.max_scenario_score_drop,
            use_optional_scores_in_regression=args.use_optional_scores_in_regression,
            max_optional_score_drop=args.max_optional_score_drop,
        )

    if args.repeat_judge > 1:
        bundle["stability_check"] = evaluate_stability(
            results,
            max_average_score_spread=args.max_judge_average_score_spread,
            allow_decision_disagreement=args.allow_judge_decision_disagreement,
        )

    if args.history_dir is not None:
        persisted_path = persist_run_bundle(args.history_dir, bundle)
        bundle["run_metadata"]["history_path"] = str(persisted_path)

    output_obj = bundle

    output = json.dumps(output_obj, indent=2)

    if args.output is not None:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    if (
        args.fail_on_regression
        and output_obj.get("baseline_comparison", {}).get("regression_detected")
    ):
        raise SystemExit("Regression detected against baseline")
    if (
        args.fail_on_instability
        and output_obj.get("stability_check", {}).get("instability_detected")
    ):
        raise SystemExit("Judge instability detected")


if __name__ == "__main__":
    main()
