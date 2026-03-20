# Source System Overview: Atlas Knowledge Hub

## Current Environment

Northstar runs Atlas Knowledge Hub on an internally managed Solr 8.11 deployment hosted on
Kubernetes in two on-premises data centers. The application tier is a Spring Boot service
used by internal operations teams and dealer portals.

## Solr Topology

- 1 primary business collection: `atlas_search`
- 6 shards
- 2 replicas per shard
- ZooKeeper ensemble of 3 nodes
- separate non-production Solr cluster for QA and training

## Application Pattern

- UI and API are backed by a custom Spring Boot search service
- most traffic goes through one `/search` endpoint
- the service builds eDisMax queries plus a stack of `fq` filters
- entitlement filters are applied at query time based on caller context

## Indexed Content Model

The `atlas_search` collection mixes several logical content types:

- `product`
- `part`
- `manual`
- `bulletin`
- `case`

The current approach uses one denormalized index with type flags instead of separate
collections per content family.

## Important Solr Features In Use

- eDisMax with `qf`, `pf`, `mm`, `bq`, and `bf`
- `copyField` into a catch-all text field
- dynamic fields for metadata and per-type attributes
- field collapsing for duplicate product families in some result sets
- faceting on content type, product line, region, language, and entitlement tier
- freshness boosting for bulletins and cases

## Pain Points

1. Solr schema changes require careful coordination and have become slow to ship.
2. Cluster maintenance and patching consume time from the application team.
3. Relevance behavior is poorly documented outside the current search lead.
4. Field sprawl has grown over time and naming conventions are inconsistent.
5. Partner access rules are correct today but difficult to audit.

## Current Query Characteristics

- average query length: 2.8 tokens
- many queries are part numbers, model numbers, or error codes
- support users often mix free text with filters
- bulletin searches depend heavily on recent content boosts

## Access Control Model

Search results are filtered by:

- `visibility_level`
- `region`
- `dealer_tier`
- `business_unit`

These values are applied as filters rather than index-per-audience separation.

## Migration-Relevant Risks

- hidden ranking logic in the application layer may not be fully documented
- some fields were added for one-off reporting use cases and may not belong in the target index
- collapse behavior will need redesign in OpenSearch
- synonym coverage for product aliases is business-critical

## Recommended Audit Focus

1. Inventory the top 50 real queries by business value, not just by volume.
2. Identify every query-time filter tied to identity or entitlements.
3. Validate which document types truly need one shared index.
4. Review freshness boosts with business owners before copying them forward.
5. Confirm whether case summaries belong in phase one or should be deferred.
