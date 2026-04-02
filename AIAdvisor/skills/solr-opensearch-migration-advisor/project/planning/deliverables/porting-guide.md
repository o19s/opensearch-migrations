# Porting Guide: Agent99 → O19s Fork

Generated 2026-03-22. Staged for execution after Eric's PR #5 lands on `main`.

**Prerequisite:** PR #5 (`mimic_launchpad_dir_structure`) merged, giving us:
```
AIAdvisor/
├── cursor/
├── kiro/migration_advisor/
├── skills/migration_planner/
├── skills/solr/
└── tests/
```

**Approach:** Small, reviewable PRs. Each is independent and can be merged on its own.
Target reviewer time: 10-15 minutes per PR.

---

## PR A: Solr-Specific References (6 files)

**Branch name:** `add-solr-references`
**Estimated diff:** ~900 lines added

Copy from `agent99/skills/solr-to-opensearch-migration/references/` into
`AIAdvisor/skills/solr/references/`:

| Source (agent99) | Target (fork) | What it covers |
|---|---|---|
| `02-pre-migration.md` | `skills/solr/references/02-pre-migration.md` | Auditing a Solr deployment, readiness scoring |
| `03-target-design.md` | `skills/solr/references/03-target-design.md` | Mapping Solr schemas to OpenSearch |
| `07-platform-integration.md` | `skills/solr/references/07-platform-integration.md` | SolrJ, pysolr, Drupal Search API patterns |
| `08-edge-cases-and-gotchas.md` | `skills/solr/references/08-edge-cases-and-gotchas.md` | 30+ Solr-specific pitfalls, no-equivalents |
| `solr-concepts-reference.md` | `skills/solr/references/solr-concepts-reference.md` | Solr feature audit, equivalence map, complexity matrix |
| `scenario-drupal.md` | `skills/solr/references/scenario-drupal.md` | Drupal Search API Solr migration scenario |

**Why these 6 together:** They're all Solr-specific source-side knowledge. They directly
fill the placeholder in `skills/solr/references/` and enhance Jeff's schema_converter
and query_converter with the domain knowledge they need.

**PR description template:**
```
## Summary
- Add 6 expert reference files covering Solr-specific migration knowledge
- These fill skills/solr/references/ (replacing the placeholder)
- Content authored in agent99 knowledge base, ported to match launchpad layout

## What's in each file
- 02-pre-migration: Solr deployment audit, readiness scoring
- 03-target-design: Schema mapping (schema.xml → OS mappings)
- 07-platform-integration: SolrJ, pysolr, Drupal patterns
- 08-edge-cases: 30+ pitfalls and no-equivalent features
- solr-concepts-reference: Feature audit and equivalence map
- scenario-drupal: Drupal Search API scenario
```

---

## PR B: Migration Planner References (12 files)

**Branch name:** `add-planner-references`
**Estimated diff:** ~2,500 lines added

Copy from `agent99/skills/solr-to-opensearch-migration/references/` into
`AIAdvisor/skills/migration_planner/references/`:

| Source (agent99) | Target (fork) | What it covers |
|---|---|---|
| `01-strategic-guidance.md` | `skills/migration_planner/references/` | When/why/when-not to migrate |
| `04-migration-execution.md` | same | Dual-write, cutover, pipeline patterns |
| `05-validation-cutover.md` | same | Relevance validation, judgment sets, go/no-go |
| `06-operations.md` | same | Monitoring, ISM, DR |
| `09-approval-and-safety-tiers.md` | same | Observe/Propose/Execute governance |
| `10-playbook-artifact-and-review.md` | same | Migration playbook artifacts, approval gates |
| `aws-opensearch-service.md` | same | AWS sizing, auth, cost, networking |
| `consulting-methodology.md` | same | OSC process, roles, reporting culture |
| `consulting-concerns-inventory.md` | same | 200-item discovery risk matrix |
| `migration-strategy.md` | same | Strategy decision trees, ETL patterns |
| `roles-and-escalation-patterns.md` | same | Team shape, escalation triggers |
| `sample-catalog.md` | same | Sample datasets and demo apps |

**Why these 12 together:** They're all engine-agnostic migration methodology. They
could apply to any search engine migration, not just Solr. They populate the
`migration_planner` skill that Eric's PR #5 creates.

**Note:** This is the larger PR (~2,500 lines). If the team prefers, it could be
split further:
- **PR B1** (core methodology, 5 files): 01-strategic, 04-execution, 05-validation,
  06-operations, migration-strategy
- **PR B2** (governance + consulting, 4 files): 09-approval, 10-playbook,
  consulting-methodology, consulting-concerns-inventory
- **PR B3** (supporting, 3 files): aws-opensearch-service,
  roles-and-escalation-patterns, sample-catalog

---

## PR C: Kiro + Cursor IDE Configs

**Branch name:** `add-ide-configs`
**Estimated diff:** ~200 lines added

Copy from agent99:

| Source (agent99) | Target (fork) |
|---|---|
| `kiro/solr-to-opensearch-migration/POWER.md` | `AIAdvisor/kiro/migration_advisor/POWER.md` |
| `kiro/solr-to-opensearch-migration/mcp.json` | `AIAdvisor/kiro/migration_advisor/mcp.json` |
| `kiro/solr-to-opensearch-migration/README.md` | `AIAdvisor/kiro/migration_advisor/README.md` |
| `cursor/plugins/solr-to-opensearch-migration/.cursor-plugin/*` | `AIAdvisor/cursor/.cursor-plugin/` |
| `cursor/plugins/solr-to-opensearch-migration/README.md` | `AIAdvisor/cursor/README.md` |

**Adjustments needed:**
- Update symlink paths (agent99 paths → fork-relative paths)
- POWER.md may need steering path updated to point to new `skills/` layout
- mcp.json server command path may need updating

**Why this is separate:** IDE configs are self-contained and easy to review.
They don't affect the Python code or reference content.

---

## PR D: Assessment Kit (future, after core content lands)

**Branch name:** `add-assessment-kit`
**Estimated diff:** ~1,200 lines added

Copy from `agent99/playbook/assessment-kit/` into
`AIAdvisor/skills/migration_planner/references/assessment-kit/`
(or a new `assets/` directory per agentskills.io convention):

| Source (agent99) | Content |
|---|---|
| `assessment-kit-index.md` | Usage sequence and index |
| `architecture-option-cards.md` | Design decision cards |
| `artifact-request-checklist.md` | What to ask clients for |
| `assessment-intake-questionnaire.md` | Client questionnaire |
| `assessment-respondent-guidance.md` | How to answer questionnaire |
| `consumer-inventory-template.md` | Map of all search API consumers |
| `go-no-go-review-template.md` | Gate review template |
| `risk-and-readiness-rubric.md` | Readiness scoring scale |
| `strategic-readout-template.md` | Executive summary template |
| `success-definition-template.md` | Client success criteria |
| `stump-the-chumps.md` | Red-team design review checklist |

**Why later:** This is consulting methodology, not core advisor functionality.
Useful but not blocking. Could also stay in agent99 if the team decides the
fork should only contain what ships as the advisor product.

---

## PR E: Eval Suite (future, after agent code is enhanced)

**Branch name:** `add-eval-suite`
**Estimated diff:** ~500 lines added

Copy from `agent99/tests/evals/` into `AIAdvisor/tests/`:

| Source (agent99) | Content |
|---|---|
| `judge_migration_advice.py` | LLM-as-a-judge evaluation harness |
| `run_eval_tasks.py` | Eval task runner |
| `datasets/golden_scenarios.json` | 5 golden test scenarios |

**Why later:** The eval suite tests the advisor's *output quality*, which
matters most after the `handle_message()` workflow is fleshed out. Running
evals against the current keyword router would just confirm it's thin.

---

## Naming Note

Eric's PR #5 uses underscores (`migration_planner`, `solr`). The agentskills.io
spec requires hyphens. If the team decides to fix this before merging PR #5,
the target paths above would change:
- `skills/migration_planner/` → `skills/migration-planner/`
- `skills/solr/` stays `skills/solr/` (no underscore to fix)

The file contents don't change — just the directory names in the copy commands.

---

## Quick Reference: Execution Commands

After PR #5 is merged and you have a fresh checkout:

```bash
# PR A: Solr references
cd /opt/work/OSC/o19s-opensearch-migrations
git checkout main && git pull
git checkout -b add-solr-references

mkdir -p AIAdvisor/skills/solr/references
cp /opt/work/OSC/agent99/skills/solr-to-opensearch-migration/references/02-pre-migration.md \
   /opt/work/OSC/agent99/skills/solr-to-opensearch-migration/references/03-target-design.md \
   /opt/work/OSC/agent99/skills/solr-to-opensearch-migration/references/07-platform-integration.md \
   /opt/work/OSC/agent99/skills/solr-to-opensearch-migration/references/08-edge-cases-and-gotchas.md \
   /opt/work/OSC/agent99/skills/solr-to-opensearch-migration/references/solr-concepts-reference.md \
   /opt/work/OSC/agent99/skills/solr-to-opensearch-migration/references/scenario-drupal.md \
   AIAdvisor/skills/solr/references/

git add AIAdvisor/skills/solr/references/
git commit -m "Add 6 Solr-specific expert references to skills/solr"
git push -u origin add-solr-references
gh pr create --title "Add Solr-specific expert references" --body "..."
```

Repeat pattern for PRs B through E.
