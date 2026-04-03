# Eval Baseline — Solr to OpenSearch Migration Advisor

**Baseline date:** 2026-04-03
**Established by:** Sean O'Connor

---

## Summary

The advisor is evaluated at three tiers, from fast/deterministic to slow/agentic:

| Tier | What it tests | Scenario count | Pass rate | Run time |
|------|--------------|----------------|-----------|----------|
| 1 — Unit tests | Deterministic converters, skill logic, session state | 25+ tests | 100% | ~10s |
| 2 — Guidance impact | Steering content measurably changes LLM output | 3 tests | 100% (3/3) | ~60s |
| 3a — Conversational eval | Full 8-step workflow via Claude agent | 12 scenarios | Not yet baselined | ~30 min |
| 3b — Basic eval | Steps 0–2 via Claude Agent SDK | 3 scenarios | Not yet baselined |  ~10 min |
| 3c — Golden scenarios | Judge-scored migration advice quality | 7 scenarios | 100% (7/7) | ~20 min |

**Total eval scenarios:** 22+ across all tiers (target: ≥10 ✅)

---

## Tier 1: Unit Tests (Deterministic)

Run via `pytest` in CI (`python-tests` job in `CI.yml`).

| Module | Tests | Status |
|--------|-------|--------|
| `test_schema_converter.py` | XML→mapping, JSON→mapping, invalid input | ✅ All pass |
| `test_query_converter.py` | match_all, field:value, phrase, wildcard, range, boolean, fallback | ✅ All pass |
| `test_skill.py` | Message routing, session persistence, progress advancement | ✅ All pass |
| `test_storage.py` | InMemory/File backends, save/load/delete/list | ✅ All pass |
| `test_report.py` | Report sections, incompatibility grouping, blocker surfacing | ✅ All pass |
| `test_skill_structure.py` | SKILL.md structure, tool declarations | ✅ All pass |
| `test_data_files.py` | Reference/steering file integrity | ✅ All pass |

**Coverage target:** ≥85% on `scripts/` (tracked via Codecov).

---

## Tier 2: Guidance Impact Tests

Run via `pytest tests/test_guidance_impact.py`. Uses a local LLM (ollama) to prove
that steering content measurably improves model output.

**Latest run:** 2026-04-03T040004Z

| Test | Result | What it checks |
|------|--------|----------------|
| `bare_lacks_guided_terms` | ✅ | Bare model misses ≥1 expected term (missed 2/4) |
| `guided_hits_most_terms` | ✅ | Guided model produces ≥3/4 expected terms (hit 3/4) |
| `guidance_improves_term_coverage` | ✅ | Guided > Bare term count (Delta: +1) |

**Expected term scorecard:**

| Term | Bare | Guided | Source |
|------|------|--------|--------|
| `script_score` | miss | ✅ | `incompatibilities.md` |
| `rebuild_handlers` | ✅ | ✅ | `incompatibilities.md` |
| `nested_mapping` | ✅ | ✅ | `incompatibilities.md` |
| `join_replacement` | miss | miss | `incompatibilities.md` |

**Known gap:** `join_replacement` not surfaced even with steering. Diagnosis suggests
strengthening the join section in `incompatibilities.md`.

---

## Tier 3a: Conversational Eval (Full 8-Step Workflow)

Config: `tests/conversational-eval/eval.yaml`
Run via: `tests/conversational-eval/run_eval.sh`
Provider: `claude_sequential_provider.py` (maintains session continuity)

12 sequential scenarios covering all 8 workflow steps:

| Step | Scenario | Metrics | Assertion types |
|------|----------|---------|-----------------|
| 0 | Role clarification | `step0_role_clarification` | llm-rubric |
| 1 | Schema request | `step1_schema_request` | llm-rubric |
| 1b | Mapping quality | `step1_mapping_quality`, `step1_spatial_mapping`, `step1_string_mapping` | llm-rubric, icontains |
| 2 | Incompatibility analysis | `step2_incompatibility_analysis`, `step2_copyfield_flagged` | llm-rubric, icontains |
| 3 | Query translation | `step3_query_translation`, `step3_range_query`, `step3_edismax_translation` | llm-rubric, icontains, icontains-any |
| 4 | Customization inquiry | `step4_customization_inquiry` | llm-rubric |
| 4b | Customization mapping | `step4_customization_mapping`, `step4_auth_mapping`, `step4_urp_mapping` | llm-rubric, icontains-any |
| 5 | Infrastructure inquiry | `step5_infra_inquiry` | llm-rubric |
| 5b | Sizing recommendation | `step5_sizing_recommendation` | llm-rubric |
| 6 | Client inquiry | `step6_client_inquiry` | llm-rubric |
| 6b | Client mapping | `step6_client_mapping`, `step6_solrj_replacement`, `step6_endpoint_migration` | llm-rubric, icontains |
| 7 | Migration report | `step7_report_completeness`, `step7_has_incompatibilities`, `step7_has_client_section`, `step7_has_plan` | llm-rubric, icontains-any |

**Baseline pass rate:** Not yet established. Requires Claude API credentials to run.

---

## Tier 3b: Basic Eval (Steps 0–2)

Config: `tests/evals/eval.yaml`
Run via: `tests/scripts/run_evals.sh`
Provider: `claude_requests.py` (Claude Agent SDK)

| Scenario | Metric | Assertion |
|----------|--------|-----------|
| Role clarification | `clarify-role` | ≥6 role examples |
| Schema request | `clarify-schema` | Asks for schema |
| Migration plan | `clarify-migration-steps` | Plausible OpenSearch schema in plan |

**Baseline pass rate:** Not yet established. Requires Claude API credentials to run.

---

## Tier 3c: Golden Scenarios (Judge-Scored)

Config: `tests/scenario-evals/promptfoo_scenarios.yaml`
Baseline: `tests/scenario-evals/baselines/golden_scenarios_baseline.json`
Run via: `tests/scenario-evals/run_eval_tasks.py`

**Pass threshold:** average score > 3.5, no major technical errors.

| Scenario | Avg Score | Decision | Rationale |
|----------|-----------|----------|-----------|
| Legacy Solr 4.x with Custom Java | 4.75 | PASS | Strong on refactor risk, staged validation |
| Drupal Search API Low Resource | 4.00 | PASS | Appropriately bounded, cost-aware, Drupal-aware |
| Relevance-Critical Commerce | 4.75 | PASS | Strong on judged relevance process, BM25 framing |
| Enterprise Hidden Consumers | 4.50 | PASS | Covers consumer inventory, hidden integration risks |
| NRT Freshness Sensitive | 4.25 | PASS | Separates freshness from backfill, rollback guardrails |
| TechProducts Full 8-Step | 4.00 | PASS | Covers major technical expectations |
| Drupal Module Swap Strategy | 4.75 | PASS | Strong strategic judgment on module swap, cost, framing |

**Aggregate scores:**

| Dimension | Average |
|-----------|---------|
| methodology_alignment | 4.43 |
| expert_judgement | 4.43 |
| heuristics | 4.14 |
| risk_identification | 4.71 |
| **overall** | **4.43** |

**Pass rate: 7/7 (100%)**

---

## P0 Coverage Matrix

Status of required eval scenarios from the deliverables tracker:

| P0 Requirement | Covered? | Where |
|----------------|----------|-------|
| Incompatibility detection (Step 2) | ✅ | conversational-eval Step 2 |
| Query translation — standard (Step 3) | ✅ | conversational-eval Step 3 |
| Query translation — edismax (Step 3) | ✅ | conversational-eval Step 3 |
| Full migration report (Step 7) | ✅ | conversational-eval Step 7 |
| Session resumption | ⚠️ | Implicit via `continue:true`; no explicit stop/resume test |
| Accuracy / no hallucination | ❌ | No negative test for fabricated claims |

## P1 Coverage Matrix

| P1 Requirement | Covered? | Where |
|----------------|----------|-------|
| Customization assessment (Step 4) | ✅ | conversational-eval Steps 4, 4b |
| Sizing recommendation (Step 5) | ✅ | conversational-eval Steps 5, 5b |
| Client integration mapping (Step 6) | ✅ | conversational-eval Steps 6, 6b |
| Stakeholder tailoring (Step 0) | ⚠️ | Only "Search Engineer" persona tested |

---

## Known Gaps & Next Steps

1. **Hallucination test (P0)** — Add a scenario that asks about a nonexistent Solr feature
   and asserts the advisor responds with uncertainty rather than fabricating an answer.

2. **Session resumption test (P0)** — Add explicit stop/resume test, or document that
   `continue:true` mechanism satisfies the requirement.

3. **Stakeholder tailoring (P1)** — Add conversational eval variants for Manager and
   DevOps personas to test depth calibration.

4. **CI integration (D3.3)** — Wire eval runs into GitHub Actions. Blocked on API
   credentials in CI secrets.

5. **Conversational eval baseline** — Run Tier 3a and 3b evals, record initial pass rates,
   and update this document.

---

## How to Run

```bash
# Tier 1: Unit tests
cd AIAdvisor/skills/solr-opensearch-migration-advisor
uv sync && pytest tests/ -x

# Tier 2: Guidance impact
pytest tests/test_guidance_impact.py --mode=demo

# Tier 3a: Conversational eval (requires Claude API)
cd tests/conversational-eval && bash run_eval.sh

# Tier 3b: Basic eval (requires Claude API)
cd tests/scripts && bash run_evals.sh

# Tier 3c: Golden scenarios
cd tests/scenario-evals && python run_eval_tasks.py --dataset datasets/golden_scenarios.json --score
```
