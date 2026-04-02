# Artifact Request Checklist

Use this checklist alongside the intake questionnaire. The assessment should distinguish between claimed system behavior and evidence-backed understanding.

## Required Artifacts

- current architecture diagram
- Solr schema and configset
- collection and core inventory
- request handler inventory
- custom update processor or plugin inventory
- sample documents with field inventory
- top search query logs from the last 30 days
- query analytics or usage reports
- synonym lists
- stopword lists
- stemming or linguistic asset definitions
- taxonomies, dictionaries, or controlled vocabularies
- performance baselines: p50, p95, p99, throughput, index size, document count
- SLA documentation
- backup and DR documentation
- incident summaries or postmortems
- monitoring and alerting overview
- security model documentation
- compliance requirements impacting search
- roadmap or timeline constraints

## Useful Additional Artifacts

- screenshots of critical search flows
- examples of difficult or failed queries
- representative API requests and responses
- search-related support tickets
- relevance tuning notes or past experiments
- prior architecture evaluation documents
- org chart or ownership map for search-related systems

## Tracking Fields

For each artifact, record:
- status: `received`, `partial`, `missing`
- owner
- date requested
- date received
- notes on quality or completeness
- impact if missing

## Evidence Quality Guidance

Mark evidence quality as:
- `Strong`: current, complete, directly relevant
- `Moderate`: usable but incomplete or stale
- `Weak`: anecdotal, partial, or unclear
- `Missing`

Escalate immediately if any of these are missing:
- search logs or equivalent query evidence
- schema/configset
- content ownership
- security model
- current SLA or operational expectations

