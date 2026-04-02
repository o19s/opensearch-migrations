# Testing Overview

This repository uses a layered testing approach because it is not just a code repo and
not just a markdown repo. We are testing helper scripts, structured knowledge assets,
companion-style migration artifacts, and scenario-based evaluation scaffolding.

## The Four Layers

### Layer 1: Unit tests

**Location:** `tests/`
**What it catches:** Incorrect converter logic, malformed data files, broken skill metadata.

Covers:
- Python helper logic in `scripts/` (schema converter, query converter, report generator)
- Skill metadata and reference-file structure (`test_skill.py`, `test_skill_structure.py`)
- Structured JSON data files used by converters and workflow logic (`test_data_files.py`)
- MCP server tool contracts (`test_mcp_server.py`)

Run: `pytest tests/unit -q`

---

### Layer 2: Functional tests

**Location:** `tests/functional/`
**What it catches:** Output that violates format rules (e.g. missing YOLO banner, missing assumption markers).

Currently this is format validation, not full execution. `test_yolo_mode.py` validates a sample
Express/YOLO response against the spec's required structure. It does not generate output from a
live scenario.

Run: `pytest tests/functional -q`

---

### Layer 3: Integration tests

**Location:** `tests/integration/`
**What it catches:** Artifact drift, broken cross-document references, converter gaps against known scenarios.

Covers:
- JSON/NDJSON syntax for worked artifacts under `examples/`
- Markdown link integrity for worked examples
- Companion-demo artifact chain completeness
- Assessment-kit template and index integrity
- Top-level document consistency as filenames evolve
- **Bridge tests**: compare current converter behavior against golden scenario expectations
  (`test_bridge_golden_scenarios.py`)

The bridge tests are the most important integration layer. They bind real scenario inputs
(TechProducts, Drupal) to expected converter outputs. Failures here mean the advisor would
produce wrong output for a known client situation.

Run: `pytest tests/integration -q`

---

### Layer 4: Qualitative evaluation

**Location:** `tests/scenario-evals/`
**What it catches:** Advice quality, expert judgment alignment, artifact completeness — things that
pass/fail assertions cannot measure.

Core artifacts:
- `datasets/golden_scenarios.json` — structured scenarios with expected behavior
- `golden-scenario-techproducts.md`, `golden-scenario-drupal.md` — narrative scenario references
- `judge_migration_advice.py` — LLM-as-judge prompt (8 scoring dimensions)
- `run_eval_tasks.py` — task runner (emit, score, persist, compare)
- `run_end_to_end_skill_eval.py` — drives a live skill flow and routes output to the judge
- `promote_eval_baseline.py` — promotes a reviewed scored run to the checked-in baseline
- `baselines/golden_scenarios_baseline.json` — checked-in baseline for CI comparison

Scoring dimensions: methodology alignment, expert judgement, heuristics, risk identification,
artifact completeness, approval-discipline quality, consumer-impact awareness, cutover-readiness
clarity.

See `advanced-testing-roadmap.md` for governance status and open policy questions.

Run (emit tasks only): `python tests/scenario-evals/run_eval_tasks.py --dataset tests/scenario-evals/datasets/golden_scenarios.json`

---

## Common Eval/Improve Cycles

Different kinds of changes need different feedback loops. Here are the three cycles used
most in practice.

### Cycle A: Converter improvement (unit → bridge → promote)

Use when adding or fixing schema/query converter behavior.

```
1. Write or fix converter logic in scripts/
2. Run unit tests: pytest tests/test_schema_converter.py -q (or test_query_converter)
3. Run bridge tests: pytest tests/integration/test_bridge_golden_scenarios.py -q
   → Passing xfail becomes a pass; failing expected case is caught here
4. If new behavior is now correct, remove the xfail marker from the bridge test
5. Run full suite: pytest -q — confirm no regressions
```

When a converter gap is known but not yet fixed:
- Add or keep an `xfail` in `test_bridge_golden_scenarios.py`
- Document the gap in `testing-status.md` under "Remaining limits"

---

### Cycle B: Skill content improvement (eval → score → compare → promote)

Use when improving skill references, adding gotchas, or tuning advice quality.

```
1. Make changes to skills/solr-to-opensearch-migration/references/ or SKILL.md
2. Collect advisor responses for the golden scenarios (manually or via e2e runner):
   python tests/scenario-evals/run_end_to_end_skill_eval.py \
     --scenario-id techproducts-full-workflow \
     --output /tmp/responses.json
3. Score the responses:
   python tests/scenario-evals/run_eval_tasks.py \
     --dataset tests/scenario-evals/datasets/golden_scenarios.json \
     --responses /tmp/responses.json \
     --score \
     --use-optional-scores-in-regression \
     --history-dir tests/scenario-evals/history \
     --run-label my-change
4. Compare to baseline:
   python tests/scenario-evals/run_eval_tasks.py \
     --dataset tests/scenario-evals/datasets/golden_scenarios.json \
     --results-file /tmp/scored-results.json \
     --baseline tests/scenario-evals/baselines/golden_scenarios_baseline.json \
     --fail-on-regression
5. If scores are better (or equal) and the change is intentional:
   python tests/scenario-evals/promote_eval_baseline.py \
     --candidate tests/scenario-evals/history/<run-bundle>.json \
     --dataset tests/scenario-evals/datasets/golden_scenarios.json \
     --output tests/scenario-evals/baselines/golden_scenarios_baseline.json \
     --note "improved X reference"
```

**Do not promote a baseline without manual review of score deltas and rationale.**

---

### Cycle C: Artifact/template improvement (integration → fix → validate)

Use when adding a new spec template, updating assessment-kit files, or changing worked examples.

```
1. Add or update artifact files in examples/ or playbook/assessment-kit/
2. Run integration tests: pytest tests/integration -q
   → test_artifact_integrity.py checks JSON/NDJSON syntax
   → test_companion_artifacts.py checks artifact chain completeness
   → test_assessment_kit_index.py checks template and index integrity
   → test_repo_doc_consistency.py catches stale references
3. Fix any failures (usually a missing file or broken link)
4. Run full suite: pytest -q
```

---

## Layer × Cycle Matrix

| Change type | Unit | Functional | Integration | Eval/judge |
|---|---|---|---|---|
| Converter logic fix | ✓ | | ✓ (bridge) | |
| New converter feature | ✓ | | ✓ (bridge) | |
| Skill reference content | | | | ✓ (score cycle) |
| Express/YOLO format rules | | ✓ | | |
| New worked example (examples) | | | ✓ (artifact) | |
| Assessment-kit template | | | ✓ (kit index) | |
| Data file structure (JSON) | ✓ | | | |
| Advisor advice quality | | | | ✓ (score cycle) |

---

## Current Status

See `testing-status.md` for the live pass/fail count, current known gaps,
open policy questions, and recommended next steps.

## Quick Reference

```bash
# Full suite
pytest -q

# Unit only
pytest tests/unit -q

# Integration only
pytest tests/integration -q

# Bridge tests only
pytest tests/integration/test_bridge_golden_scenarios.py -q

# Emit eval tasks
python tests/scenario-evals/run_eval_tasks.py \
  --dataset tests/scenario-evals/datasets/golden_scenarios.json

# End-to-end skill eval
python tests/scenario-evals/run_end_to_end_skill_eval.py \
  --scenario-id techproducts-full-workflow \
  --output /tmp/e2e-out.json

# Score + persist
python tests/scenario-evals/run_eval_tasks.py \
  --dataset tests/scenario-evals/datasets/golden_scenarios.json \
  --responses /path/to/responses.json \
  --score \
  --use-optional-scores-in-regression \
  --history-dir tests/scenario-evals/history \
  --run-label local

# Compare to baseline
python tests/scenario-evals/run_eval_tasks.py \
  --dataset tests/scenario-evals/datasets/golden_scenarios.json \
  --results-file /path/to/scored-results.json \
  --baseline tests/scenario-evals/baselines/golden_scenarios_baseline.json \
  --use-optional-scores-in-regression \
  --fail-on-regression

# Promote a reviewed run to checked-in baseline
python tests/scenario-evals/promote_eval_baseline.py \
  --candidate /path/to/run-bundle.json \
  --dataset tests/scenario-evals/datasets/golden_scenarios.json \
  --output tests/scenario-evals/baselines/golden_scenarios_baseline.json \
  --note "reason for update"
```
