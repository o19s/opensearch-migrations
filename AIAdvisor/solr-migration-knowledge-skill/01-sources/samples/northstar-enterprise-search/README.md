# Northstar Enterprise Search Sample

## Scenario

This sample represents a medium-complexity Fortune 500 migration from an in-house Solr
application to Amazon OpenSearch Service.

- **Company:** Northstar Industrial Systems
- **Program name:** Atlas Knowledge Hub
- **Source:** Solr 8.11 running in-house on Kubernetes
- **Target:** Amazon OpenSearch Service 2.x in a private VPC
- **Complexity:** 3/5

## What This Sample Is For

Use this folder when you need a more realistic enterprise demo than `techproducts`, but do
not want a very high-complexity migration with custom plugins or extreme data volumes.

This sample is designed to support:

- migration planning workshops
- source-system audits
- starter Kiro specs
- query translation demos
- schema translation demos
- stakeholder and team-planning exercises

## Included Files

- `project-description.md`: business context, scope, constraints, and success metrics
- `client-team.md`: sample client-side migration team with roles and responsibilities
- `source-system-overview.md`: current Solr architecture, collections, traffic, and pain points
- `sample-queries.md`: representative Solr queries and expected migration challenges
- `conf/schema.xml`: realistic sample schema for the primary search collection
- `conf/solrconfig.xml`: request handlers, commit settings, and caching defaults
- `sample-docs.json`: representative documents from the source system

## Search Domain

Atlas Knowledge Hub powers internal and partner-facing search across:

- product catalog records
- technical manuals
- service bulletins
- support cases
- parts compatibility content

The search experience is used by call-center agents, field technicians, parts specialists,
dealer portals, and internal engineering staff.

## Complexity Notes

This sample is intentionally medium complexity because it includes:

- multiple document types in one logical search experience
- eDisMax queries with field boosts and phrase boosts
- faceting and filtered navigation
- access-control trimming via entitlement fields
- freshness boosting for service bulletins
- synonym-driven technical vocabulary

It intentionally excludes very high-complexity features such as:

- custom Java plugins
- nested documents at large scale
- streaming expressions
- cross-datacenter Solr replication requirements
- online dual-write implementation details

## Recommended Next Step

Use `project-description.md` and `source-system-overview.md` as the input set for creating a
new worked migration spec under `03-specs/`.
