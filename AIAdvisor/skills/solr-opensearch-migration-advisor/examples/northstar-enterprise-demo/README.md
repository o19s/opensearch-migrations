# Solr → OpenSearch Migration: Northstar Enterprise Demo

## What This Is

This is a worked migration specification for Northstar Industrial Systems' fictional
Atlas Knowledge Hub platform: a medium-complexity enterprise search application moving
from in-house Solr 8.11 to Amazon OpenSearch Service 2.x.

This sample is intended to be demo-worthy rather than production-complete. It is more
realistic than `techproducts-demo` because it includes:

- multiple document types in one search experience
- enterprise access-control filters
- business-critical support and parts lookup journeys
- richer query behavior, including boosts, filters, facets, and freshness ranking

## How To Use This

1. Start with `steering/` docs to understand business context and technical constraints.
2. Review `requirements.md` for the target behaviors that must survive migration.
3. Study `design.md` for the target OpenSearch architecture and query translation patterns.
4. Execute `tasks.md` as the implementation and demo-preparation checklist.

## File Structure

```text
northstar-enterprise-demo/
├── README.md
├── INDEX.md
├── MANIFEST.txt
├── steering/
│   ├── product.md
│   ├── tech.md
│   └── structure.md
├── requirements.md
├── design.md
└── tasks.md
```

## Migration Complexity Score

**Northstar: 3/5 (Medium Complexity)**

Why:

- one primary collection but several logical content types
- query-time entitlements and region filters
- moderate relevance complexity with field boosts and freshness
- no custom Solr plugins or other extreme migration blockers

## Demo Goal

Produce a credible starter migration plan and implementation skeleton that can drive a
test migration for a representative enterprise Solr application on AWS.

## Source Material

This spec is based on:

- `sources/samples/northstar-enterprise-search/project-description.md`
- `sources/samples/northstar-enterprise-search/client-team.md`
- `sources/samples/northstar-enterprise-search/source-system-overview.md`
- `sources/samples/northstar-enterprise-search/sample-queries.md`
- `sources/samples/northstar-enterprise-search/conf/schema.xml`
- `sources/samples/northstar-enterprise-search/conf/solrconfig.xml`
- `sources/samples/northstar-enterprise-search/sample-docs.json`

## Expected Outcome

After completing this demo spec, the next practical step is a test migration using a reduced
Northstar sample corpus and a minimal application/API layer that exercises the top search flows.
