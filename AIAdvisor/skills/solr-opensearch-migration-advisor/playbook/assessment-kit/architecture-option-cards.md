# Architecture Option Cards

Use these cards during intake support, interviews, and readouts. They are short explainers for common migration decision areas so respondents can answer questions with better context.

## 1. Migration Posture

### Option A: Parity-First

When it fits:
- strong pressure to preserve current user-visible behavior
- low tolerance for change during initial migration

Advantages:
- easier stakeholder framing
- clearer short-term comparison target

Disadvantages:
- can waste effort preserving bad legacy behavior
- often collides with real engine differences

Use this if:
- the client must preserve regulated or tightly controlled search behavior

Respondent shortcut:
- Not sure? Choose this if the main concern is “do not surprise users.”

## 2. Migration Posture

### Option B: Redesign-First

When it fits:
- current search quality is already weak
- platform change is meant to unlock improvements

Advantages:
- better long-term search quality potential
- avoids expensive parity theater

Disadvantages:
- harder stakeholder alignment
- requires stronger product and measurement discipline

Use this if:
- the client wants a better search product, not just a new engine

Respondent shortcut:
- Not sure? Choose this if the team already knows the current search experience needs improvement.

## 3. Cutover Model

### Option A: Dual-Write / Shadow Validation

When it fits:
- higher risk environments
- critical search experiences
- need for measured comparison and rollback confidence

Advantages:
- safer rollout
- better parity evidence

Disadvantages:
- more engineering effort
- temporary operational complexity

Use this if:
- the client cannot tolerate large cutover surprises

Respondent shortcut:
- Not sure? Choose this if search is production-critical or politically sensitive.

## 4. Cutover Model

### Option B: Batch Reindex / Harder Cutover

When it fits:
- smaller workloads
- lower business criticality
- simpler integration environment

Advantages:
- lower short-term engineering overhead

Disadvantages:
- less validation evidence
- higher cutover risk

Use this if:
- the client can tolerate more migration risk and simpler rollback posture

Respondent shortcut:
- Not sure? Choose this only if search is relatively non-critical and the data model is simple.

## 5. Data Model

### Option A: Denormalize

When it fits:
- read performance matters more than update elegance
- nested relationships are limited or manageable

Advantages:
- simpler search queries
- often easier operationally

Disadvantages:
- data duplication
- more expensive updates

Use this if:
- the current hierarchy can be flattened without losing critical behavior

Respondent shortcut:
- Not sure? Choose this unless the application truly depends on deep hierarchical query semantics.

## 6. Data Model

### Option B: Nested / Relationship Modeling

When it fits:
- relationships are core to the search experience
- query semantics depend on contained object boundaries

Advantages:
- preserves more structural meaning

Disadvantages:
- more complex mappings and queries
- easier to get wrong in migration

Use this if:
- search behavior depends on related subdocuments being queried correctly

Respondent shortcut:
- Not sure? Choose this only if the team can name concrete nested-query use cases.

## 7. Transformation Location

### Option A: Application-Side Transform

When it fits:
- transformation logic already lives in application code
- strong engineering ownership exists

Advantages:
- clearer version control and testing
- fewer engine-specific surprises

Disadvantages:
- more application work
- can spread logic across services

Respondent shortcut:
- Not sure? Choose this if transformations are already business-logic-heavy.

## 8. Transformation Location

### Option B: Ingest Pipeline Transform

When it fits:
- transformations are simple and index-local
- the team wants less application-layer complexity

Advantages:
- centralizes search-specific enrichment

Disadvantages:
- can hide logic in the platform
- may be weaker than existing custom Solr processing

Respondent shortcut:
- Not sure? Choose this only for simple, well-bounded transforms.

## 9. Platform Model

### Option A: Provisioned OpenSearch

When it fits:
- predictable workload
- stronger control requirements
- 24/7 usage

Advantages:
- more predictable cost and capacity planning

Disadvantages:
- more sizing work
- idle capacity risk

Respondent shortcut:
- Not sure? Choose this for steady production workloads.

## 10. Platform Model

### Option B: Serverless OpenSearch

When it fits:
- variable demand
- simpler operational preference
- workload economics favor elastic scaling

Advantages:
- less infrastructure management

Disadvantages:
- cost surprises for steady workloads
- feature and control differences may matter

Respondent shortcut:
- Not sure? Treat this as an option to evaluate, not a default.

## 11. Authorization Strategy

### Option A: Application-Enforced Filtering

When it fits:
- access rules are already owned in the app
- engine-level access controls are limited or unnecessary

Advantages:
- may align with existing architecture

Disadvantages:
- easier to leak data through snippets, autocomplete, or alternate APIs

Respondent shortcut:
- Not sure? Do not assume this is safe enough without explicit review.

## 12. Authorization Strategy

### Option B: Engine-Enforced Filtering

When it fits:
- tenant separation or regulated access matters
- auditability matters

Advantages:
- stronger centralized protection

Disadvantages:
- more setup and design discipline

Respondent shortcut:
- Not sure? Choose this as the safer default for sensitive or multi-tenant search.

## Suggested Clarifying Questions

Respondents should feel free to ask:
- `What is the practical difference between these two options?`
- `Which option is the safer default?`
- `Which option usually costs more time or money?`
- `Which option gives us better rollback or debugging posture?`
- `Are we choosing a final answer now, or just signaling direction?`

