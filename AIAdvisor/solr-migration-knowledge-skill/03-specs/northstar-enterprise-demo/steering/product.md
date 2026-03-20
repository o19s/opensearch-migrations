# Product Steering: Northstar Enterprise Demo

## Project Goal

Create a realistic demo migration plan for Northstar Industrial Systems' Atlas Knowledge Hub,
an enterprise search application currently backed by in-house Solr and targeted for Amazon
OpenSearch Service.

The purpose of this spec is to demonstrate:

- how to frame a medium-complexity enterprise search migration
- how to preserve core business-critical search flows
- how to translate Solr query and schema behavior into OpenSearch-native design

## In Scope

- one primary collection: `atlas_search`
- five logical content types: product, part, manual, bulletin, case
- top search flows for support, parts lookup, manuals, and bulletins
- query translation for eDisMax, filters, facets, and freshness boost logic
- target AWS OpenSearch domain design for a demo environment
- starter implementation structure for a test migration

## Out Of Scope

- full production cutover
- semantic/vector retrieval
- full enterprise IAM redesign
- migration of secondary legacy collections
- analytics and click-model migration
- deep UI redesign

## Primary Users

- support agents
- field technicians
- dealer portal users
- parts specialists
- engineering support staff

## Success Criteria

1. The target spec supports the top enterprise search journeys without losing key behavior.
2. The demo design preserves entitlement filtering and region scoping.
3. Query translations are credible and demo-ready for the top sample queries.
4. The implementation plan is realistic for a small migration team running a proof-of-concept.
5. The resulting spec can drive a test migration without needing major restructuring.

## Key Business Constraints

- no relevance reset for business-critical search journeys
- dealer visibility rules must remain correct
- infrastructure must align with AWS-managed-service expectations
- the demo must be understandable by both engineering and product stakeholders

## Open Questions For Later Demo Iterations

- whether support cases should stay in the same target index as product and manual content
- whether dealer-tier filtering should remain query-time only or also influence index design
- whether collapse/grouping behavior needs explicit redesign for product-family rollups

## Delivery Target

**Status:** Planning  
**Phase:** Demo setup  
**Target outcome:** test migration starter specification
