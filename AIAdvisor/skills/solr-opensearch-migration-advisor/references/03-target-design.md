# Target Design: OpenSearch Architecture and Modeling Decisions
**Scope:** Designing the OpenSearch target before implementation: index strategy, field modeling, analyzer posture, shard and replica planning, alias patterns, and readiness review criteria. Covers what the target should look like and why. Does not cover migration execution mechanics or cutover validation.
**Audience:** O19s consultants, architects, search engineers, and platform owners
**Last reviewed:** 2026-03-20 | **Reviewer:** AI draft — expanded for Phase 1/2 design use

---

## Key Judgements

- **The target design should reflect information needs, not the source schema.** Solr field names and dynamic suffixes are historical evidence, not sacred architecture. Translate intent, not XML.
- **Aliases are not optional.** If the application points directly at concrete index names, you are making every future reindex, blue/green swap, and rollback harder than it needs to be.
- **One bad field model can poison an otherwise good migration.** The most common design failures are choosing `text` where `keyword` is needed, flattening relationships that should stay structured, and enabling overly permissive dynamic mapping.
- **Oversharding is a design bug, not an ops inconvenience.** Many migrations arrive in OpenSearch already compromised because the team designed for imaginary future scale instead of current workload shape.
- **A good target design is explicit about non-survivors.** Some Solr features should be re-expressed differently, some should move into the application layer, and some should be dropped. Pretending everything survives 1:1 creates hidden defects.
- **Analyzer design deserves first-class review.** Many search regressions blamed on OpenSearch are really analyzer mismatches introduced during hurried target design.
- **Index templates and mapping versioning are part of the design, not implementation details.** If the team cannot say how it will evolve mappings safely, the design is incomplete.
- **Target design should reduce ambiguity, not preserve it.** If the Solr deployment is messy, the OpenSearch design should simplify and clarify. Rebuilding the mess in JSON is not a win.

---

## Design Objectives

A target design should answer:

1. How many indexes do we need and why?
2. How will reads and writes be routed safely?
3. How are fields modeled for search, filter, sort, facet, and highlight behavior?
4. How are analyzers and synonyms represented?
5. What shard and replica posture fits the workload?
6. What parts of the source behavior are redesigned rather than copied?

If those answers are not explicit, the design is still incomplete.

---

## Index Strategy

### Single Index vs Multiple Indexes

Use a **single index** when:

- the content model is coherent
- ranking logic is broadly shared
- security boundaries are the same
- lifecycle/retention needs are similar

Use **multiple indexes** when:

- content types have materially different analyzers or ranking needs
- security models differ
- retention/lifecycle differs sharply
- teams need operational independence

Do not split into many indexes just because Solr had many collections. Some Solr estates over-partitioned for historical or organizational reasons rather than real search needs.

### Time-Based Indexes / Data Streams

Consider time-based patterns only when:

- the content is truly append-heavy or log-like
- retention and rollover are central concerns
- query patterns align with time windows

For most application-search migrations, a conventional versioned index plus aliases is more appropriate than a data-stream posture.

---

## Alias Strategy

Use aliases from day one.

### Default Pattern

- `<domain>_read`
- `<domain>_write`
- concrete versioned indexes such as `<domain>_v001`

### Why This Matters

- safe reindexing
- blue/green swaps
- cleaner rollback
- less application coupling to index lifecycle

### Recommended Rule

Applications should never know the concrete index version. They should only know the stable alias names.

If the design lacks an alias plan, stop and add one before implementation begins.

---

## Field Modeling Rules

### Text vs Keyword

Use `text` for:

- full-text relevance
- analyzed user-facing search

Use `keyword` for:

- filters
- facets
- exact matching
- sorting
- identifiers and enumerations

When a field needs both behaviors, use a multi-field pattern rather than forcing one type to do both jobs.

### Multi-Fields

Default example:

- `title` as `text`
- `title.keyword` as `keyword`

This is safer than enabling `fielddata` on `text`, which is usually the wrong fix.

### Numeric and Date Fields

Prefer explicit numeric/date types for:

- range filters
- sorting
- aggregations

Do not carry string-typed numerics forward just because the source system got away with it.

---

## Dynamic Mapping and Templates

### Recommended Default

For production migrations, prefer:

- explicit mappings for known fields
- narrow dynamic templates where naming conventions are truly intentional
- avoid open-ended dynamic mapping unless the domain genuinely requires it

### Design Warning

Dynamic templates are useful when they encode real business conventions. They are dangerous when they are used to preserve a mysterious suffix system no one can explain.

If the source relies heavily on dynamic fields:

1. identify the real patterns
2. decide which survive
3. make templates explicit
4. reject the rest

---

## Relationship Modeling

### Nested vs Flattened vs Join

Use `nested` when:

- related subobjects must preserve tuple semantics
- filters and scoring depend on relationships within repeated structures

Use `flattened` when:

- the structure is sparse and irregular
- you need simple search/filter behavior over unknown keys
- strict tuple semantics are not required

Use `join` only when:

- parent/child behavior is truly necessary
- you have validated that nested or denormalized models will not work

### Default Bias

Prefer:

1. denormalized documents
2. `nested`
3. `join`

in that order, unless the domain clearly demands otherwise.

`join` is usually the last resort because it complicates both performance and reasoning.

---

## Analyzer Strategy

### Design Review Questions

- What fields are full-text searchable?
- Which analyzers differ between index and query time?
- Where do synonyms live and who owns them?
- Which Solr analyzer components do not map cleanly?
- Which analyzer choices are core to ranking quality?

### Recommended Practice

- name analyzers explicitly
- separate index and search analyzers only when there is a real reason
- keep synonym strategy reviewable and versioned
- test analyzer outputs with representative text before indexing large corpora

### Common Design Failure

Teams often copy Solr analyzer intent incompletely, then compensate with boosts or query rewrites. Fix the analyzer design first before piling on ranking patches.

---

## Query Architecture Implications

Target design is not just mappings. It also needs a query posture.

Decide early:

- main query family (`multi_match`, `bool`, `function_score`, etc.)
- filter strategy
- facet strategy
- sort strategy
- deep pagination strategy
- highlight strategy

If the design does not name the expected query shapes, mapping choices will be made in a vacuum.

### Deep Pagination

If the application paginates deeply:

- design for `search_after`
- avoid assuming `from/size` will scale

### Highlighting

If large body fields are highlighted:

- design for fragment use
- avoid returning oversized source blobs casually

---

## Shard and Replica Planning

### Default Shard Guidance

Start smaller than you think.

Rules of thumb:

- small datasets often need only 1 primary shard
- design around expected shard size, not round numbers
- avoid creating many shards "for future growth"

### Replica Guidance

Replicas are driven by:

- availability needs
- read concurrency
- failure tolerance

Remember that OpenSearch will not colocate primary and replica on the same node. Designs copied from undersized Solr clusters often fail here operationally.

### Design Inputs Required

You need:

- expected data volume
- growth rate
- indexing rate
- search concurrency
- recovery expectations

Without those inputs, shard planning is guesswork wearing architecture clothing.

---

## Template and Versioning Strategy

A mature target design includes:

- index template strategy
- mapping/settings versioning approach
- alias swap plan
- reindex posture for incompatible changes

### Recommended Principle

Assume mappings will change. Design for safe versioned rollout instead of hoping the first mapping is final.

If the design assumes in-place schema evolution for breaking field changes, it is brittle.

---

## AWS Service and Environment Choices

At design time, decide:

- managed AWS OpenSearch Service vs self-managed
- VPC and auth model
- relevant availability posture
- environment separation
- snapshot/restore expectations

Do not leave these as "ops details" if they constrain analyzers, plugins, cost, or access patterns.

---

## Design Review Checklist

Use this before implementation begins.

### Architecture

- [ ] Index count justified
- [ ] Alias strategy defined
- [ ] Concrete index naming/versioning pattern defined
- [ ] Non-surviving Solr features identified

### Mapping

- [ ] Critical fields mapped explicitly
- [ ] Text vs keyword decisions reviewed
- [ ] Dynamic templates justified
- [ ] Sort/filter/facet fields validated for exact-match behavior

### Relationships

- [ ] Nested vs flattened vs join decisions explained
- [ ] Denormalization opportunities considered first

### Analysis

- [ ] Analyzer set named and documented
- [ ] Synonym ownership identified
- [ ] Index vs search analyzer differences justified

### Query Posture

- [ ] Primary query families identified
- [ ] Facet strategy identified
- [ ] Deep pagination plan identified
- [ ] Highlighting/source retrieval behavior identified

### Operations

- [ ] Initial shard/replica posture justified
- [ ] Template/versioning strategy documented
- [ ] Reindex plan for breaking changes understood

If more than a few boxes are unchecked, the team is probably still in assessment rather than ready for implementation.

---

## Decision Heuristics

- **If a field is used in filters, facets, or sorts, design an exact-match representation for it explicitly.** Do not hope the team remembers this later.
- **If the source schema is messy, bias toward simplification in the target.** Migration is a redesign opportunity, not a preservation exercise.
- **If document relationships are causing debate, prototype with representative queries before locking the model.** This is cheaper than rewriting after indexing millions of documents.
- **If future index evolution is not described, the design is incomplete.** Reindexability is part of the architecture.
- **If shard planning is based on fear rather than measured workload, cut the shard count down.** Most teams overestimate scale and underestimate the cost of oversharding.

---

## Common Mistakes

- Porting source collections 1:1 without questioning why they exist
- Letting applications depend on concrete index names
- Mapping everything as `text` and fixing the fallout later
- Preserving dynamic-field conventions no one understands
- Using `join` because it feels relationally correct rather than operationally sensible
- Treating analyzer design as an implementation detail
- Designing shards and replicas without actual workload inputs

---

## Open Questions / Evolving Guidance

- What target-design patterns should be added for hybrid/vector search scenarios as that becomes more common?
- Which field-modeling patterns deserve worked examples in the repo’s spec demos?
- What lightweight templates or starter artifacts should accompany this reference in future iterations?
