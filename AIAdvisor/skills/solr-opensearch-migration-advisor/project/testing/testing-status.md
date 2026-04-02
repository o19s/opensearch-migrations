# Testing Status: Solr -> OpenSearch Migration Advisor

**Last Updated:** 2026-03-23
**Current Version:** 0.2.1
**Objective:** Keep the repository honest by checking helper-script behavior, skill/data-file integrity, companion-artifact integrity, cross-document consistency, and scenario-eval scaffolding.

---

## 1. Current Snapshot

### Verified current run

Command last run:

```bash
pytest -q
```

Current result on 2026-03-23:

- 313 tests passed
- 0 tests xfailed
- 0 tests failed

The suite currently has no intentional `xfail` cases.

### What the repo has today

- unit tests for helper scripts and structured data files
- structural tests for `SKILL.md` and reference-file conformance
- a functional-format validator for Express Mode output
- integration tests for companion artifacts, assessment-kit templates, spec artifact syntax, and repo-doc consistency
- bridge tests that compare current converter behavior against golden scenario expectations
- an eval scaffold with:
  - judge prompt
  - golden-scenario dataset
  - task runner
  - optional live scoring against an OpenAI-compatible backend
  - persisted scored run bundles
  - baseline comparison with simple regression thresholds
- a checked-in fixture baseline for deterministic regression-check wiring
- repeat-judge stability summaries
- repeat-judge instability checks with configurable fail thresholds
- end-to-end scored skill flows for TechProducts and Drupal
- a baseline-promotion workflow
- optional artifact-quality scoring dimensions
- optional artifact-score regression checks

### What the repo does not have yet

- a fully socialized team policy for baseline refresh and review
- a mature, team-agreed regression policy beyond the initial threshold-based checks
- a second-judge or alternate-model comparison path

### Provisional default policy in the repo right now

These are working defaults by assistant recommendation, not team-approved policy:

- artifact-oriented scores should be included in scored baseline comparisons
- a shared optional artifact score should be allowed to drop by at most `0.5`
- judge instability should fail a repeated-judge run by default
- repeated judge runs should allow at most `0.75` average-score spread
- repeated judge runs should not allow PASS/FAIL disagreement by default

This should be read as a practical starting point for the team, not as settled governance.

---

## 2. Testing Architecture

### Tier 1: Unit Tests

**Location:** `tests/`

This tier covers:

- helper-script behavior in `scripts/`
- skill metadata and reference-file structure
- structured JSON data files used by converters and workflow logic

Representative files:

- `tests/test_schema_converter.py`
- `tests/test_query_converter.py`
- `tests/test_storage.py`
- `tests/test_report.py`
- `tests/test_skill.py`
- `tests/test_mcp_server.py`
- `tests/test_skill_structure.py`
- `tests/test_data_files.py`
- `tests/test_solr_to_opensearch.py`

Important note:

- this tier is stronger than the older project summary implied; it now covers much more than one schema-translation helper

### Tier 2: Functional Tests

**Location:** `tests/functional/`

Current file:

- `tests/functional/test_yolo_mode.py`

What it actually does:

- validates a sample Express/YOLO response against format rules

What it does not do:

- execute the advisor
- generate output from a real scenario
- validate companion-artifact generation

This tier should be described as **format validation**, not full functional execution.

### Tier 3: Integration Tests

**Location:** `tests/integration/`

This tier covers repo-level integrity and behavior across artifact sets.

Representative files:

- `tests/integration/test_artifact_integrity.py`
- `tests/integration/test_companion_artifacts.py`
- `tests/integration/test_assessment_kit_index.py`
- `tests/integration/test_repo_doc_consistency.py`
- `tests/integration/test_eval_scaffold.py`
- `tests/integration/test_bridge_golden_scenarios.py`

Current emphasis:

- JSON and NDJSON syntax for worked artifacts under `examples/`
- markdown link integrity for worked examples
- expected companion-demo artifact chain
- assessment-kit index and template completeness
- top-level document consistency for current filenames and artifact references
- bridge coverage for TechProducts and Drupal golden scenarios

### Tier 4: Qualitative Evaluation

**Location:** `tests/scenario-evals/`

Core artifacts:

- `tests/scenario-evals/datasets/golden_scenarios.json`
- `tests/scenario-evals/golden-scenario-techproducts.md`
- `tests/scenario-evals/golden-scenario-drupal.md`
- `tests/scenario-evals/judge_migration_advice.py`
- `tests/scenario-evals/run_eval_tasks.py`
- `tests/scenario-evals/run_end_to_end_skill_eval.py`
- `tests/scenario-evals/promote_eval_baseline.py`

Current status:

- the dataset and runner are implemented
- the runner can emit structured eval tasks
- the runner can optionally call an OpenAI-compatible backend with `--score`
- scored results can be imported or generated, summarized, and persisted as run bundles
- baseline comparison is available with configurable thresholds for overall score, pass rate, and per-scenario score drop
- a checked-in baseline file exists for deterministic comparison-path checks in CI
- repeat-judge stability summaries are available
- one end-to-end skill flow can generate a real report and send it through the judge path
- two end-to-end skill flows can generate real reports and send them through the judge path
- baseline promotion from a reviewed scored run is scripted and tested
- optional artifact-oriented scores are supported when the judge provides them
- optional artifact-oriented scores can be included in regression checks
- repeat-judge instability can be treated as a failure with configurable thresholds

This tier should be described as **operational and expanding, but still early-stage in policy/governance**.

---

## 3. Remaining Query-Converter Limits

The request-level placeholder API in `scripts/query_converter.py` now covers:

- `defType=edismax` plus `qf` to `multi_match`
- `fq` wrapping into `bool.filter`
- `facet.field` to `terms` aggregations

What still remains limited is the single-string `convert()` API. It still does not pretend to parse full Solr request semantics from a lone `q` string, which is the right boundary for now.

---

## 4. Recommended Commands

### Run the full automated suite

```bash
pytest -q
```

### Run only integration tests

```bash
pytest tests/integration -q
```

### Emit structured eval tasks from the golden dataset

```bash
python tests/scenario-evals/run_eval_tasks.py --dataset tests/scenario-evals/datasets/golden_scenarios.json
```

### Score eval tasks with a live judge backend

```bash
python tests/scenario-evals/run_eval_tasks.py \
  --dataset tests/scenario-evals/datasets/golden_scenarios.json \
  --responses /path/to/responses.json \
  --score \
  --use-optional-scores-in-regression \
  --fail-on-instability
```

### Persist a scored run into eval history

```bash
python tests/scenario-evals/run_eval_tasks.py \
  --dataset tests/scenario-evals/datasets/golden_scenarios.json \
  --responses /path/to/responses.json \
  --score \
  --history-dir tests/scenario-evals/history \
  --run-label local
```

### Compare a scored-results file against a saved baseline

```bash
python tests/scenario-evals/run_eval_tasks.py \
  --dataset tests/scenario-evals/datasets/golden_scenarios.json \
  --results-file /path/to/scored-results.json \
  --baseline tests/scenario-evals/baselines/golden_scenarios_baseline.json \
  --use-optional-scores-in-regression \
  --fail-on-regression
```

### Run the minimal end-to-end scored skill flow

```bash
python tests/scenario-evals/run_end_to_end_skill_eval.py \
  --scenario-id techproducts-full-workflow \
  --output /tmp/e2e-techproducts.json
```

### Promote a reviewed scored run to the checked-in baseline

```bash
python tests/scenario-evals/promote_eval_baseline.py \
  --candidate /path/to/reviewed-run-bundle.json \
  --dataset tests/scenario-evals/datasets/golden_scenarios.json \
  --output tests/scenario-evals/baselines/golden_scenarios_baseline.json \
  --note "refresh after manual review"
```

Expected env/config for live scoring:

- `JUDGE_API_KEY` or `--api-key`
- optional `JUDGE_API_BASE`
- optional `JUDGE_MODEL`

---

## 5. Priority Follow-Up Work

1. Review and either ratify or replace the provisional default eval policy.
2. Add a second-judge or alternate-model comparison path.
3. Expand the remaining single-query converter gaps beyond placeholder support.
4. Decide whether end-to-end scored flows should be CI-gated or remain manual.

---

## 6. Bottom Line

The testing setup is materially ahead of the older status summary.

Today the repo has:

- broad automated pytest coverage
- explicit integrity checks for companion artifacts and repo docs
- golden-scenario bridge tests that track known converter gaps
- a usable qualitative-eval system with optional live judging, run history, baseline comparison, stability summaries, end-to-end scoring, and baseline-promotion workflow

What it still lacks is a settled team policy for advanced eval governance and broader end-to-end scenario coverage.
