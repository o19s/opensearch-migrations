# Project Description: Northstar Industrial Systems

## Executive Summary

Northstar Industrial Systems is a fictional Fortune 500 manufacturer of industrial pumps,
controls, filtration systems, and aftermarket parts. Its internal search platform, Atlas
Knowledge Hub, currently runs on in-house Solr and serves several business-critical workflows.

The company wants to migrate to Amazon OpenSearch Service to reduce operational burden,
improve cloud alignment, and modernize search delivery for product support and dealer
operations.

## Business Drivers

1. Reduce time spent operating and patching self-managed Solr infrastructure.
2. Standardize on AWS-managed services for core application platforms.
3. Improve resiliency and disaster-recovery posture for search.
4. Simplify onboarding of new teams that need search-backed workflows.
5. Create a cleaner path for future semantic and vector search experiments.

## Current Product

Atlas Knowledge Hub is a consolidated search experience used by:

- call-center support teams
- field service technicians
- dealer portal users
- product engineering
- parts operations

The application exposes a single search box with faceting, filters, and type-aware ranking
across several content families.

## In Scope

- migrate the primary `atlas_search` Solr collection to Amazon OpenSearch Service
- preserve query behavior for the top support and parts lookup journeys
- preserve entitlement-based filtering for internal and partner users
- migrate core facets, filters, boosts, and field mappings
- define a cutover-ready target design for one production search experience

## Out of Scope

- full UI redesign
- semantic search rollout
- generative answer features
- migration of low-value legacy collections outside `atlas_search`
- historical analytics backfill
- enterprise-wide identity rearchitecture

## Source Dataset Characteristics

- approximately 18 million indexed documents
- one primary collection supporting five major document types
- average weekday search volume of 2.7 million queries
- peak weekday ingestion bursts tied to parts updates and service bulletins
- English-only for phase one, with French and Spanish planned later

## Major Document Types

1. Product records
2. Parts and compatibility records
3. Technical manuals
4. Service bulletins
5. Support case summaries

## Top User Journeys

1. Find the correct replacement part for a machine model and region.
2. Search for a service bulletin by symptom, error code, or product family.
3. Retrieve the latest technical manual for a product revision.
4. Find support cases similar to the current issue.
5. Filter results by region, product line, entitlement tier, and content type.

## Success Criteria

The demo migration is considered successful when:

1. Core result sets show acceptable parity for the top 25 sample queries.
2. Facets for product line, region, document type, and entitlement tier behave correctly.
3. Query latency is within 15% of the Solr baseline for representative demo traffic.
4. Access-control filters remain correct for internal vs dealer users.
5. The target architecture is credible for a production migration plan.

## Constraints

- the business will not accept a relevance reset during peak service season
- partner access rules must remain intact throughout the migration
- the source app team is capacity-constrained and can only support limited refactoring
- AWS networking and security reviews are mandatory before production cutover

## Demo Assumptions

- use a reduced sample corpus rather than all 18 million documents
- focus on one collection and one API surface
- model the migration as a phased production program, even though the demo uses starter data

## Complexity Assessment

**Overall rating:** 3/5

Reasons:

- richer than a tutorial dataset
- multiple content types and access filters
- real boosting and facet behavior
- no custom Solr plugins or highly specialized linguistics

## Suggested Demo Narrative

"Northstar runs a mature but internally operated Solr platform for parts and support search.
The migration target is Amazon OpenSearch Service, and the challenge is preserving business
critical search behavior without carrying forward years of Solr-specific operational baggage."
