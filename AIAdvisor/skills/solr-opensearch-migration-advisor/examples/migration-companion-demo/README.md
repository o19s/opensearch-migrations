# Migration Companion Demo Artifact Set

## What This Is

This worked example shows the minimum artifact trail that an AI-assisted migration companion should leave behind during a staged Solr-to-OpenSearch migration.

It is intentionally compact. The goal is not to model every implementation detail, but to show how the advisory layer should produce durable, reviewable artifacts across:

- assessment
- risk framing
- playbook authoring
- approval
- cutover control

## Included Artifacts

- `assessment-summary.md`
- `success-definition.md`
- `consumer-inventory.csv`
- `risk-register.md`
- `migration-playbook.md`
- `go-no-go-review.md`
- `approval-record.md`
- `cutover-checklist.md`

## How To Read It

1. Start with `assessment-summary.md` to see what the AI observed and what is still uncertain.
2. Read `success-definition.md` to see what success means in approval-grade terms.
3. Read `consumer-inventory.csv` to see which search consumers must be accounted for.
4. Read `risk-register.md` to understand what would block or constrain approval.
5. Read `migration-playbook.md` to see the bounded stage plan.
6. Read `go-no-go-review.md` to see how a gate decision is framed and conditioned.
7. Review `approval-record.md` to see how approval is tied to versioned artifacts.
8. Use `cutover-checklist.md` as the operator-facing day-of-cutover control sheet.

## Why This Exists

Issue `opensearch-project/opensearch-migrations#2444` assumes a model where the AI is the interface, but reviewable artifacts still control the migration. This example makes that model concrete inside `Agent99` without turning the repo into the runtime execution system.

## Notes

- The scenario is fictional but representative.
- The artifacts are prose-first markdown, not executable workflow YAML.
- The point is to demonstrate approval and evidence flow, not to replace upstream workflow implementations.
