---
name: solr-to-opensearch-guided
displayName: "Solr to OpenSearch Migration Advisor (guided — with steering)"
description: >
  Migrates Apache Solr collections to OpenSearch indexes.
  Translates Solr schemas to OpenSearch mappings and converts
  Solr query syntax into OpenSearch DSL.
  Uses steering documents and reference material for accurate,
  expert-level migration guidance.
---

# Apache Solr to OpenSearch Migration Advisor

An agent skill for migrating from Apache Solr to OpenSearch.

## Capabilities
- Translate Solr XML schemas to OpenSearch index mappings
- Convert Solr query syntax (Standard, DisMax, eDisMax) to OpenSearch Query DSL
- Identify migration incompatibilities

## Guidance
Always read the steering documents in `steering/` before responding.
Cross-reference with detailed examples in `references/` when available.
