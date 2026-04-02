# Testing Artifacts To Share

This file is the short index to send teammates when you want to explain the current testing setup without dropping them into the whole repo.

## Best Starting Points

- `project/testing/testing-overview.md`
- `project/testing/testing-status.md`

Use `testing-overview.md` for the fast explanation. Use `testing-status.md` for the more detailed current-state record.

## Core Automated Test Assets

### Main test entry point

- `pytest -q`

### Unit and structure coverage

- `tests/unit/test_schema_converter.py`
- `tests/unit/test_query_converter.py`
- `tests/unit/test_storage.py`
- `tests/unit/test_report.py`
- `tests/unit/test_skill.py`
- `tests/unit/test_skill_structure.py`
- `tests/unit/test_data_files.py`

These show that we are not only testing code logic, but also the structure and integrity of the skill package and its JSON backing data.

### Integration coverage

- `tests/integration/test_artifact_integrity.py`
- `tests/integration/test_companion_artifacts.py`
- `tests/integration/test_assessment_kit_index.py`
- `tests/integration/test_repo_doc_consistency.py`
- `tests/integration/test_bridge_golden_scenarios.py`
- `tests/integration/test_eval_scaffold.py`

These are the best files to share when explaining that the repo now tests companion artifacts, assessment templates, top-level document drift, and scenario scaffolding in addition to script behavior.

## Qualitative Eval Assets

### Dataset

- `tests/evals/datasets/golden_scenarios.json`

This is the structured set of scenario prompts and expected qualities.

### Rich scenario references

- `tests/evals/golden-scenario-techproducts.md`
- `tests/evals/golden-scenario-drupal.md`

These are the most concrete examples of what we mean by a "golden scenario."

### Judge and runner

- `tests/evals/judge_migration_advice.py`
- `tests/evals/run_eval_tasks.py`

These show the current LLM-as-a-judge flow, scored-run bundling, and baseline-comparison logic.

### Promptfoo fixture and config

- `promptfooconfig.yaml`
- `tests/evals/promptfoo_scenarios.yaml`

These are the lighter-weight advisor-eval artifacts for promptfoo-based experimentation.

## Companion Artifact Examples

If the team wants to understand why testing moved beyond script coverage, point them at:

- `examples/migration-companion-demo/README.md`
- `examples/migration-companion-demo/success-definition.md`
- `examples/migration-companion-demo/consumer-inventory.csv`
- `examples/migration-companion-demo/go-no-go-review.md`
- `examples/migration-companion-demo/approval-record.md`
- `examples/migration-companion-demo/cutover-checklist.md`

These are the artifact types the newer integration tests are protecting.

## Suggested Sharing Sequence

If someone has 5 minutes:

1. `project/testing/testing-overview.md`
2. `project/testing/testing-status.md`

If someone wants the actual testing mechanics:

1. `tests/integration/test_companion_artifacts.py`
2. `tests/integration/test_bridge_golden_scenarios.py`
3. `tests/evals/datasets/golden_scenarios.json`
4. `tests/evals/run_eval_tasks.py`

If someone wants the "why" behind the artifact tests:

1. `examples/migration-companion-demo/README.md`
2. `tests/integration/test_companion_artifacts.py`
