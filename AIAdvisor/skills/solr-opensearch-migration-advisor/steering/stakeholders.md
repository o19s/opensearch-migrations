# Stakeholder Roles and Per-Step Guidance

## Roles

### Search Engineer
- **Focus:** Schema design, analyzers, query translation, relevance tuning, scoring behavior
- **Depth:** Full technical detail — show complete JSON mappings, Query DSL, field-by-field annotations
- **Priority steps:** Step 1 (Schema), Step 2 (Incompatibilities), Step 3 (Query Translation)

### Application Developer
- **Focus:** Client library migration, API changes, integration code updates
- **Depth:** Concrete before/after code snippets, dependency changes, constructor differences
- **Priority steps:** Step 6 (Client Integration)

### DevOps / Platform Engineer
- **Focus:** Cluster sizing, deployment, operations, authentication, monitoring
- **Depth:** Instance types, storage, node roles, auto-scaling, deployment automation
- **Priority steps:** Step 4 (Customizations — auth/security), Step 5 (Infrastructure)

### Data Engineer
- **Focus:** Ingest pipelines, schema evolution, indexing throughput, data transformation
- **Depth:** Field types affecting ingest, date formats, numeric precision, bulk indexing configuration
- **Priority steps:** Step 1 (Schema — ingest impact), Step 4 (Customizations — URP/ingest processors)

### Architect
- **Focus:** System design, integration surface area, risk assessment, build-vs-buy decisions
- **Depth:** Structural summaries, risk matrices, sequencing recommendations, long-term maintainability
- **Priority steps:** Step 4 (Customizations), Step 5 (Infrastructure — topology), Step 7 (Report)

### Product Manager / Business Stakeholder
- **Focus:** Business impact, timelines, cost estimates, milestones, plain-language summaries
- **Depth:** Skip raw JSON and Query DSL; translate everything into business terms
- **Priority steps:** Step 7 (Report), Step 5 (Infrastructure — cost)

## Per-Step Tailoring Summary

| Step | Search Engineer | DevOps / Platform | Data Engineer | Architect | Product Manager |
|------|----------------|-------------------|---------------|-----------|-----------------|
| 0 — Role ID | Confirm technical depth | Confirm ops focus | Confirm ingest focus | Confirm strategic focus | Confirm plain-language mode |
| 1 — Schema | Full mapping JSON, field annotations | Index settings (shards, replicas) | Field types affecting ingest | Structural summary, design decisions | Plain-language field summary |
| 2 — Incompatibilities | Deep per-finding analysis | Breaking issues causing failures | Field type gaps, stored-vs-source | Risk summary (blocker counts) | Business impact per finding |
| 3 — Query Translation | Full before/after Query DSL | Resource-intensive query patterns | Queries requiring schema changes | Patterns needing app redesign | Search features that change |
| 4 — Customizations | Plugin internals, analysis chains | Auth, security, operational constraints | URP → ingest pipeline mapping | Build-vs-buy surface area | Capabilities and effort estimates |
| 5 — Infrastructure | Shard sizing, JVM, ILM | Instance types, storage, monitoring | Indexing throughput capacity | Topology, DR, cost model | Cost and SLA terms |
| 6 — Client Integration | Query/response shape differences | Auth changes, network/firewall | Write integrations (/update) | Integration breadth, sequencing | Systems needing updates |
| 7 — Report | Lead with incompatibilities + DSL | Lead with sizing + ops runbook | Lead with ingest pipeline changes | Lead with executive risk summary | Lead with plain-language summary |
