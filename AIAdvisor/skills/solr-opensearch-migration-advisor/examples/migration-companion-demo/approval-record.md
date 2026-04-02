# Approval Record

**Record ID:** `northwind-approval-record-v1`
**Date:** 2026-03-20

## Artifact Under Review

- `migration-playbook.md`
- version: `northwind-search-migration-v1`
- bounded stage: offline validation through shadow traffic readiness

## Approvers

| Name | Role | Decision |
|---|---|---|
| Priya N. | Search lead | Approved with conditions |
| Marcus L. | Product owner | Approved with conditions |

## Conditions

- A gold query set covering top 50 search journeys must be completed before Stage 2 is marked successful.
- Replay lag threshold must be documented numerically before Stage 3 begins.
- Rollback owner must be named before any cutover recommendation is drafted.

## Evidence Reviewed

- `assessment-summary.md`
- `risk-register.md`
- target design review notes
- initial dashboard plan for latency, error rate, replay lag, and indexing freshness

## Explicitly Not Approved

- production traffic cutover
- destructive target reindex actions outside this playbook
- changes to credentials, IAM, or network controls

## Reviewer Notes

Approval is limited to the stages and boundaries named in the playbook. Any scope expansion, unresolved critical regression, or operational instability requires a new approval review.
