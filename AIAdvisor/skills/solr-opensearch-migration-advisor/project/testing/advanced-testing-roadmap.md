# Advanced Testing Roadmap

This document focuses on the repo's "advanced" testing layer: LLM-as-judge evals, scored run history, baseline comparison, and the next steps needed to turn those pieces into a durable team practice.

## Current State

As of 2026-03-23, the repo already has a working advanced-testing foundation:

- structured golden scenarios in `tests/evals/datasets/golden_scenarios.json`
- richer scenario references in `tests/evals/golden-scenario-techproducts.md` and `tests/evals/golden-scenario-drupal.md`
- an LLM-as-judge prompt in `tests/evals/judge_migration_advice.py`
- a runnable eval harness in `tests/evals/run_eval_tasks.py`
- optional live scoring against an OpenAI-compatible backend via `--score`
- scored-run bundling and local history persistence via `--history-dir`
- baseline comparison with threshold checks via `--baseline` and `--fail-on-regression`
- a checked-in deterministic baseline fixture in `tests/evals/baselines/golden_scenarios_baseline.json`
- CI wiring for the baseline-comparison path in `.github/workflows/tests.yml`

This means the advanced-testing layer is no longer hypothetical. It is operational infrastructure.

## What It Does Well Today

The current advanced-testing setup can already answer these questions:

- Can we turn scenarios and responses into structured eval tasks?
- Can we score those tasks with a judge backend?
- Can we persist scored runs for later comparison?
- Can we compare one run to a prior baseline and fail on regression?
- Can we validate malformed imported judge results instead of silently trusting them?

That is enough to support local experiments, manual baseline refreshes, and deterministic CI checks of the comparison machinery.

## What It Still Does Not Do

The missing pieces are mostly process and policy, not raw mechanics.

We still do not have:

- a fully socialized team policy for baseline refresh ownership and review
- a documented decision rule for when a baseline should be updated
- a CI job that calls a live judge backend on every change
- multiple end-to-end scenario flows through the judge pipeline

## Recommended Next Steps

## Provisional Default Policy

Status: assistant best guess only, not team-reviewed.

This repo now has enough eval machinery that it needs a default operating posture. The recommendations below are intentionally provisional and should be treated as a starting point for team review, not as a final governance decision.

Recommended provisional defaults:

- include optional artifact-oriented scores in baseline regression checks
- allow up to `0.5` drop for any shared optional artifact score
- fail a scored run on judge instability when repeated judging is enabled
- allow up to `0.75` average-score spread across repeated judge runs
- do not allow PASS/FAIL decision disagreement across repeated judge runs
- use these defaults for live-scored runs and baseline refresh candidates, not for the deterministic fixture-baseline CI wiring

Why these are best guesses:

- this repo cares about migration artifacts, not only prose advice, so artifact-score regressions should not remain invisible by default
- large judge spread or decision disagreement is a practical sign that a candidate baseline needs manual review
- the thresholds are deliberately loose enough to avoid noisy failures while still catching obvious drift

What remains unreviewed:

- whether `0.5` and `0.75` are the right thresholds
- whether all optional artifact dimensions should be treated equally
- whether instability should block every scored run or only baseline-promotion candidates

### 1. Baseline refresh workflow

Status: implemented in basic form.

The repo now has:

- a promotion utility in `tests/evals/promote_eval_baseline.py`
- integration coverage for that promotion path
- a documented promotion command

What remains is the team policy layer:

- who is allowed to refresh the checked-in baseline
- what responses are judged to produce that baseline
- when threshold changes are acceptable
- what PR note is required when the baseline is intentionally updated

Current workflow:

1. Generate or collect candidate advisor responses in a JSON file keyed by scenario ID.
2. Run the live judge harness with `--score`.
3. Persist the run bundle in a local history directory.
4. Review score deltas and rationale manually.
5. If approved, promote the reviewed run into the checked-in baseline artifact in `tests/evals/baselines/`.

### 2. Add artifact-quality scoring dimensions

Status: implemented in basic form.

The judge still has four core advice-quality dimensions, and the pipeline now also supports optional artifact-oriented dimensions:

- methodology alignment
- expert judgement
- heuristics
- risk identification
- artifact completeness
- approval-discipline quality
- consumer-impact awareness
- cutover-readiness clarity

What remains:

- decide whether optional artifact scores should be included in regression gates by default rather than by opt-in flag
- define the exact policy for when artifact scores matter vs when they are observational only
- add more than one artifact-heavy scored scenario

### 3. Add one live-scored end-to-end scenario flow

Status: implemented and expanded.

The repo now has an end-to-end eval script in `tests/evals/run_end_to_end_skill_eval.py` for:

- `techproducts-full-workflow`
- `drupal-full-workflow`

What remains:

- decide whether end-to-end scored flows should feed the checked-in baseline
- decide whether end-to-end scored flows should become CI-gated or remain manual

### 4. Add judge-stability checks

Status: implemented in basic form.

The runner now supports repeated judge calls and stability summaries.
It can also fail on instability with configurable spread/disagreement thresholds.

What remains:

- run a second judge model on the same payloads
- decide which spread/disagreement thresholds the team wants to enforce by default
- decide whether repeat-judge should be a default part of live baseline refreshes

### 5. Recommended next implementation target

The next best technical step is to deepen the advanced-testing layer rather than widen it.

Recommended order:

1. Decide whether artifact-oriented scores should participate in regressions by default.
2. Decide whether judge instability should warn or fail by default.
3. Add a second-judge or alternate-model comparison path.
4. Decide whether end-to-end scored flows should be CI-gated or remain manual.

## Recommended Commands

### Generate eval tasks only

```bash
python tests/evals/run_eval_tasks.py \
  --dataset tests/evals/datasets/golden_scenarios.json
```

### Score responses with a live judge backend

```bash
python tests/evals/run_eval_tasks.py \
  --dataset tests/evals/datasets/golden_scenarios.json \
  --responses /path/to/responses.json \
  --score \
  --use-optional-scores-in-regression \
  --fail-on-instability \
  --history-dir tests/evals/history \
  --run-label local
```

### Compare a scored-results file to the current baseline

```bash
python tests/evals/run_eval_tasks.py \
  --dataset tests/evals/datasets/golden_scenarios.json \
  --results-file /path/to/scored-results.json \
  --baseline tests/evals/baselines/golden_scenarios_baseline.json \
  --use-optional-scores-in-regression \
  --fail-on-regression
```

### Promote a reviewed scored run to the checked-in baseline

```bash
python tests/evals/promote_eval_baseline.py \
  --candidate /path/to/reviewed-run-bundle.json \
  --dataset tests/evals/datasets/golden_scenarios.json \
  --output tests/evals/baselines/golden_scenarios_baseline.json \
  --note "refresh after manual review"
```

Recommended rule:

- only promote a candidate after manual review of score deltas, scenario coverage, and rationale
- include a short promotion note in the PR describing why the baseline changed
- until the team says otherwise, treat the provisional policy above as a working default rather than a final standard

## Practical Interpretation

The advanced-testing story is now:

- good enough for engineering iteration
- good enough for manual scoring runs
- good enough for deterministic CI verification of the regression path
- capable of scoring two real end-to-end scenario flows
- capable of optional artifact-score regression checks
- capable of optional instability-based failures

It is not yet:

- a fully governed evaluation program
- a mature release gate
- a robust measure of artifact quality across the whole repo

That is the right framing for the team right now.

Testing note:

- the bridge suite no longer carries intentional `xfail` cases for the request-level query-conversion placeholders; those checks now pass against `convert_request()`
