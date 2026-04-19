# Stakeholder Roles and Per-Step Guidance

## Roles

### Search Relevance Engineer
- **Focus:** Schema design, analyzers, query translation, relevance tuning, scoring behavior
- **Depth:** Full technical detail — show complete JSON mappings, Query DSL, field-by-field annotations
- **Priority steps:** Step 2 (Schema), Step 3 (Incompatibilities), Step 4 (Query Translation)

### Application Developer
- **Focus:** Client library migration, API changes, integration code updates
- **Depth:** Concrete before/after code snippets, dependency changes, constructor differences
- **Priority steps:** Step 7 (Client Integration)

### DevOps / Platform Engineer
- **Focus:** Cluster sizing, deployment, operations, authentication, monitoring
- **Depth:** Instance types, storage, node roles, auto-scaling, deployment automation
- **Priority steps:** Step 5 (Customizations — auth/security), Step 6 (Infrastructure)

### Data Engineer
- **Focus:** Ingest pipelines, schema evolution, indexing throughput, data transformation
- **Depth:** Field types affecting ingest, date formats, numeric precision, bulk indexing configuration
- **Priority steps:** Step 2 (Schema — ingest impact), Step 5 (Customizations — URP/ingest processors)

### Architect
- **Focus:** System design, integration surface area, risk assessment, build-vs-buy decisions
- **Depth:** Structural summaries, risk matrices, sequencing recommendations, long-term maintainability
- **Priority steps:** Step 5 (Customizations), Step 6 (Infrastructure — topology), Step 8 (Report)

### Product Manager / Business Stakeholder
- **Focus:** Business impact, timelines, cost estimates, milestones, plain-language summaries
- **Depth:** Skip raw JSON and Query DSL; translate everything into business terms
- **Priority steps:** Step 8 (Report), Step 6 (Infrastructure — cost)

## Per-Step Tailoring Summary

| Step | Search Relevance Engineer | Application Developer | DevOps / Platform | Data Engineer | Architect | Product Manager |
|------|--------------------------|----------------------|-------------------|---------------|-----------|-----------------|
| 0 — Role ID | Confirm technical depth | Confirm code focus | Confirm ops focus | Confirm ingest focus | Confirm strategic focus | Confirm plain-language mode |
| 2 — Schema | Full mapping JSON, field annotations | Field names/types affecting queries | Index settings (shards, replicas) | Field types affecting ingest | Structural summary, design decisions | Plain-language field summary |
| 3 — Incompatibilities | Deep per-finding analysis | Incompatibilities affecting query results | Breaking issues causing failures | Field type gaps, stored-vs-source | Risk summary (blocker counts) | Business impact per finding |
| 4 — Query Translation | Full before/after Query DSL | Before/after code examples | Resource-intensive query patterns | Queries requiring schema changes | Patterns needing app redesign | Search features that change |
| 5 — Customizations | Plugin internals, analysis chains | Request/response contract changes | Auth, security, operational constraints | URP → ingest pipeline mapping | Build-vs-buy surface area | Capabilities and effort estimates |
| 6 — Infrastructure | Shard sizing, JVM, ILM | Summarise briefly, move on | Instance types, storage, monitoring | Indexing throughput capacity | Topology, DR, cost model | Cost and SLA terms |
| 7 — Client Integration | Query/response shape differences | Before/after code snippets, deps | Auth changes, network/firewall | Write integrations (/update) | Integration breadth, sequencing | Systems needing updates |
| 8 — Report | Lead with incompatibilities + DSL | Lead with client/front-end impact | Lead with sizing + ops runbook | Lead with ingest pipeline changes | Lead with executive risk summary | Lead with plain-language summary |
