---
name: "solr-to-opensearch-migration"
displayName: "Solr to OpenSearch Migration Advisor"
description: "Expert guidance for migrating Apache Solr (SolrCloud) collections to AWS OpenSearch Service. Covers query translation (DisMax/eDisMax → Query DSL), schema mapping, relevance tuning (TF-IDF → BM25), dual-write migration strategies, AWS configuration, and consulting methodology."
keywords: ["solr", "opensearch", "migration", "solrcloud", "query dsl", "schema mapping", "aws opensearch", "search migration", "relevance", "bm25"]
author: "opensearch-search-consulting"
---

# Onboarding

## Prerequisites

This is a **knowledge-only** power — no scripts, Docker, or MCP servers required.
The power provides expert migration guidance through steering files that Kiro loads
into context as needed.

## Quick Test

After adding this power, try:

> *"I'm migrating a SolrCloud cluster with eDisMax queries and custom analyzers to OpenSearch — where do I start?"*

---

# Overview

An expert advisor for Solr-to-OpenSearch migration engagements. Provides strategic
guidance, query and schema translation patterns, relevance tuning methodology,
AWS configuration decisions, and consulting process frameworks.

## When to Use

Use this power when:

- Planning or executing a Solr → OpenSearch (or Elasticsearch) migration
- Translating Solr queries (DisMax, eDisMax, Standard parser) to OpenSearch Query DSL
- Mapping Solr schema (schema.xml, fieldType, copyField, dynamic fields) to OpenSearch index mappings
- Designing dual-write, shadow-traffic, or cutover migration strategies
- Diagnosing relevance differences after migration (BM25 vs TF-IDF)
- Configuring AWS OpenSearch Service (provisioned or serverless)
- Running a consulting engagement for a search migration

## Core Mental Model

Solr and OpenSearch share Apache Lucene but diverge in every other layer.
**Full refactor beats lift-and-shift** because:

- DisMax/eDisMax has no 1:1 equivalent — queries must be redesigned using Query DSL
- Relevance scoring: Solr defaults to TF-IDF, OpenSearch defaults to BM25 — expect
  30–40% ranking difference without explicit tuning
- XML configsets cannot be mechanically translated to JSON index settings
- ZooKeeper coordination is replaced by embedded Raft — operational model changes significantly

## Steering Files

Read the relevant steering file when the user's question falls in that domain:

| User needs | Steering file |
|------------|---------------|
| Whether to migrate at all, go/no-go decisions | `steering/01-strategic-guidance.md` |
| Inventorying a Solr deployment | `steering/02-pre-migration.md` |
| Designing the OpenSearch solution | `steering/03-target-design.md` |
| Dual-write, cutover, execution pipelines | `steering/04-migration-execution.md` |
| Relevance measurement, go/no-go gates | `steering/05-validation-cutover.md` |
| AWS ops, monitoring, ISM, DR | `steering/06-operations.md` |
| Platform integration (Spring, Python, Drupal) | `steering/07-platform-integration.md` |
| Edge cases, obscure gotchas | `steering/08-edge-cases-and-gotchas.md` |
| AWS service config, sizing, auth, cost | `steering/aws-opensearch-service.md` |
| Solr feature audit, what survives migration | `steering/solr-concepts-reference.md` |
| Migration strategy, phases, timelines | `steering/migration-strategy.md` |
| Consulting methodology, process | `steering/consulting-methodology.md` |
| Team roles, escalation triggers | `steering/roles-and-escalation-patterns.md` |
| Business concerns, risk inventory | `steering/consulting-concerns-inventory.md` |
| Drupal-specific migration | `steering/scenario-drupal.md` |
| Sample data catalog | `steering/sample-catalog.md` |

## Migration Phase Overview

```
Phase 1: Audit & Design (2–4 wks)
  ├─ Inventory: collections, schema, queries, traffic, special features
  ├─ Design: OpenSearch mappings, query equivalents, index strategy
  └─ Provision: AWS OpenSearch Service cluster + Dashboards

Phase 2: Build & Validate (2–4 wks)
  ├─ Implement index mappings and query translation layer
  ├─ Load representative data subset
  └─ Offline relevance comparison (Quepid/RRE) vs Solr baseline

Phase 3: Dual-Write (2–6 wks)
  ├─ Write to both Solr and OpenSearch in production
  ├─ Historical catchup: reindex all existing documents
  └─ Shadow-traffic comparison; tune until relevance KPIs meet SLO

Phase 4: Gradual Cutover (1–2 wks)
  ├─ 5% → 25% → 50% → 100% traffic shift
  ├─ Go/no-go gates: relevance, latency p99, error rate
  └─ Keep Solr warm for 30–60 days rollback window

Phase 5: Cleanup (2–4 wks)
  └─ Remove dual-write, decommission Solr + ZK, finalise docs
```

## Rules

- Load steering files on demand — don't read all 16 files at once
- Primary steering files (01–07) cover 80% of engagements; load secondary (08+) only for edge cases
- When providing query translation examples, show concrete before/after (Solr → OpenSearch)
- Always flag relevance scoring differences (TF-IDF vs BM25) as a top risk
- For AWS decisions, default to: provisioned, r6g.large, 3-AZ, VPC, IAM+SigV4
