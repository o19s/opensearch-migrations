# Migration Playbook

**Playbook ID:** `northwind-search-migration-v1`
**Status:** In review
**Owner:** Migration lead
**Source environment:** Production SolrCloud
**Target environment:** AWS OpenSearch staging, then production
**Bounded stage:** Offline validation through shadow traffic readiness

## Goal

Prepare Northwind Commerce product search for staged OpenSearch migration without exposing production users until quality, freshness, and rollback controls are demonstrated.

## Scope Boundaries

- Included:
  - product search
  - autocomplete
  - browse facets
  - backfill and mirrored read validation
- Excluded:
  - production traffic cutover
  - source-side destructive changes
  - IAM or network topology changes

## Preconditions

- source schema and configset snapshot captured
- target index template reviewed
- replay path available for mirrored reads
- monitoring dashboards created for latency, error rate, replay lag, and indexing freshness

## Stage 1: Target Validation

**Objective:** Confirm target mappings, analyzers, and query translation are fit for sample data.

**Actions**

- load 250k representative documents
- run smoke-query set across keyword, facet, autocomplete, and filter flows
- inspect mapping exceptions and analyzer output

**Success criteria**

- no critical functional errors
- no unexpected dynamic mapping creation in protected fields
- sample query results are explainable and stable

**Stop conditions**

- target mappings require structural redesign
- critical query class cannot be represented safely

## Stage 2: Offline Relevance Validation

**Objective:** Establish judged baseline and tune the OpenSearch query layer to acceptable quality.

**Actions**

- create gold query set from top-volume and top-value queries
- collect judgments with search lead and merch lead
- compare source and target runs
- document accepted regressions and required fixes

**Success criteria**

- all critical query classes judged
- unexplained critical regressions reduced to zero
- stakeholders sign off on remaining non-critical differences

**Stop conditions**

- query abstraction layer cannot support required ranking controls
- judged results reveal unacceptable drift without a credible fix path

## Stage 3: Shadow Traffic Readiness

**Objective:** Prove operational readiness before requesting production cutover approval.

**Actions**

- mirror 10% read traffic for 24 hours
- compare latency, errors, freshness, and sampled result diffs
- rehearse rollback communications and ownership

**Success criteria**

- latency and error rates stay within agreed thresholds
- replay lag stays within freshness tolerance
- no unresolved critical result regressions
- rollback owner and cutover approver confirmed

**Stop conditions**

- sustained replay lag beyond threshold
- repeated target instability
- unresolved critical regressions under real traffic mix

## Evidence Required Before Moving Beyond This Playbook

- judged relevance report
- shadow traffic findings
- updated risk register
- operator-approved cutover checklist draft

## Approval Gates

| Gate | Decision | Approver |
|---|---|---|
| Assessment gate | proceed to design and target validation | Search lead |
| Validation gate | proceed to shadow traffic | Search lead + product owner |
| Shadow readiness gate | request cutover review package | Product owner + platform lead |

## Rollback Posture

This playbook does not authorize production cutover. If any stage is halted:

- stop mirrored-read expansion
- keep Solr as system of record
- preserve target findings and incident notes
- open human-led review before the next execution attempt
