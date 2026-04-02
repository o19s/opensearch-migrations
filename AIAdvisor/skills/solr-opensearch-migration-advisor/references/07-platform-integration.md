# Platform Integration: Application Refactors, Client Swaps, and Cutover-Safe Code Paths

**Scope:** Application-layer migration guidance for code that talks to Solr and must be adapted to OpenSearch. Covers consumer inventory, client-library changes, query-construction refactors, response mapping, auth, dual-write patterns, code-review expectations, and test posture. Deliberately excludes engine-side mapping design and operational runbook detail.
**Audience:** Application engineers, architects, migration leads, and consultants coordinating the last-mile code changes of a search migration
**Last reviewed:** 2026-03-20  |  **Reviewer:** AI draft — expanded to support companion-style planning and approval

---

## Key Judgements

- **Application code is where migrations stop being theoretical.** Schema and cluster work can look healthy while the real product path is still deeply coupled to Solr-specific behavior.
- **The client-library swap is the easy part; query meaning is the hard part.** Replacing `SolrClient` is mostly mechanical. Replacing implicit Solr query behavior with explicit OpenSearch Query DSL is a design exercise.
- **Inventory hidden consumers before touching the primary app.** Reporting jobs, cron tasks, admin tools, and autocomplete services often outnumber the obvious web application path in migration risk.
- **Do not let OpenSearch types spread unchecked through the codebase.** A migration that hardcodes new engine details everywhere only trades one legacy for another.
- **Dual-write lives in application and data pipeline code, so ownership must be explicit.** The search team can advise, but application teams usually own the correctness of write routing and fallback behavior.
- **Authentication changes are often the first real blocker.** AWS SigV4, new credentials, and network boundaries should be proven early, before deep query work starts.
- **A good application migration leaves the code easier to reason about than before.** If the end result is more engine-specific branching, more copy-pasted JSON, and weaker tests, the migration is not done.
- **Code review matters more than code generation.** AI-generated query rewrites are useful, but human reviewers still need clear abstractions, test evidence, and rollback-safe behavior.

---

## What This Workstream Owns

Platform integration covers:

- client library replacement
- search-service interfaces
- query builder refactors
- response mapping changes
- indexing and write-path changes
- auth and connection management
- fallback and error handling
- migration-specific test harnesses

It does not own:

- target mapping design
- relevance signoff by itself
- cluster scaling and operational policy

Those inputs must already exist or be coordinated with other workstreams.

---

## Step 1: Inventory Search Consumers

Before changing code, identify every meaningful consumer of Solr.

Typical categories:

- customer-facing search APIs
- autocomplete services
- browse and facet endpoints
- indexing and update pipelines
- admin or support tools
- reporting or analytics jobs
- one-off scripts and cron jobs

### Why This Matters

The main product UI is rarely the only consumer. Forgotten consumers are a classic post-cutover failure mode.

### Minimum Inventory Questions

- Which services or jobs call Solr directly?
- Which ones use shared search libraries?
- Which ones depend on Solr response shape or XML/JSON fields directly?
- Which ones perform writes vs reads?
- Which ones are business-critical on day one of cutover?

Create a consumer list before promising application cutover dates.

---

## Step 2: Isolate Search Behind A Stable Interface

Do this before large-scale query rewrites whenever possible.

### Good Pattern

- one domain-oriented search service interface
- one or more engine-specific implementations behind it
- engine-agnostic DTOs crossing service boundaries

### Bad Pattern

- controller code constructing engine queries directly
- business logic parsing raw search-engine response objects
- search client imports scattered through many files

### Why This Matters

A stable interface helps with:

- dual-run validation
- targeted refactors
- easier tests
- future engine changes

If you skip this step, every query change becomes a codebase-wide hunt.

---

## Step 3: Refactor Query Construction Intentionally

Solr query construction often relies on accumulated shorthand:

- query strings
- handler parameters
- eDisMax settings
- ad hoc boost rules
- implicit parser defaults

OpenSearch makes more of that explicit.

### Refactor Goal

Move from:

- string assembly and parameter bags

To:

- named query-building functions with bounded inputs and explicit outputs

### Review Checklist For Query Refactors

- Does the code express business intent clearly?
- Are boosts and filters named, not hidden in string fragments?
- Are defaults explicit?
- Is pagination handled safely?
- Is fallback behavior defined?

If the reviewer cannot tell what a query is trying to do, the refactor is not finished.

---

## Step 4: Normalize Response Mapping

Do not let UI or API layers consume raw OpenSearch hits directly.

Map to domain objects such as:

- `ProductResult`
- `SearchPage`
- `FacetBucket`
- `AutocompleteSuggestion`

This prevents response-shape churn from leaking outward and makes side-by-side comparison easier during migration.

### Common Mapping Risks

- assuming score meaning is identical
- depending on raw highlight structures
- exposing aggregation internals directly to callers
- mixing engine metadata with product-facing DTOs

---

## Step 5: Prove Auth And Connectivity Early

Authentication and connectivity changes should be treated as an early milestone.

Typical changes:

- HTTP endpoint model instead of ZooKeeper discovery
- SigV4 signing for AWS OpenSearch Service
- new IAM or secret-management dependencies
- TLS and certificate validation differences

### Early Success Criteria

- application can authenticate to the target environment
- one read query succeeds
- one write succeeds if the workload writes directly
- logs show actionable failures when auth breaks

Do this before deep migration coding if possible.

---

## Step 6: Design Dual-Write And Fallback Paths Carefully

Dual-write belongs in this workstream when the application owns writes.

### Dual-Write Checklist

- clearly define source of truth
- log write failures separately for each target
- decide whether write failure is blocking or compensating
- record divergence so it can be reconciled
- define how and when dual-write ends

### Fallback Checklist

- can reads return to Solr cleanly during rollout?
- is the feature flag or route switch tested?
- are failures observable to operators?
- can the application degrade safely if one search path fails?

If these answers are vague, the code path is not cutover-ready.

---

## Platform-Specific Notes

### JVM: SolrJ To `opensearch-java`

Common migration tasks:

- replace `SolrQuery` construction with explicit request builders or bounded query factories
- replace raw `QueryResponse` handling with typed mapping from hits and aggs
- prove connection lifecycle and retry behavior under the new client

Watch for:

- legacy Elasticsearch clients used "because they mostly work"
- client imports spread through controllers and services
- retry behavior assumed rather than configured

### Python: `pysolr` To `opensearch-py`

Common migration tasks:

- replace query-string calls with structured request bodies
- move bulk indexing to helper-based pipelines
- isolate request/response dict handling behind a thin adapter

Watch for:

- raw DSL dicts duplicated across modules
- broad exception handling that hides query bugs
- brittle assumptions about hit structure

### Node.js

Common migration tasks:

- centralize client construction
- centralize DSL object creation
- normalize response mapping before data reaches route handlers

Watch for:

- object-literal DSL duplicated across many files
- convenience wrappers that hide failures or swallow timeouts

### Ruby, PHP, .NET, Other Platforms

The exact library differs, but the same structural rules apply:

- inventory consumers
- isolate engine details
- centralize query building
- normalize response mapping
- test fallback behavior

The client choice matters, but architecture matters more.

---

## Suggested Refactor Patterns

### Search Service Interface

Have the domain ask for search outcomes, not engine syntax.

Useful shape:

- search by intent
- autocomplete by intent
- indexing by domain payload
- delete by domain identifier

### Query Factory

Keep query-building logic in one place per major domain.

Examples:

- product search query factory
- autocomplete query factory
- category browse query factory

This is where business intent becomes Query DSL.

### Migration Adapter Layer

During migration, an adapter layer can help compare source and target behavior without leaking both engines across the codebase.

Useful responsibilities:

- fan-out reads for comparison
- normalize results
- emit structured diff logs
- support feature-flagged routing

---

## Code Scanning Checklist

Use this checklist when reviewing an app before implementation:

- locate all Solr client imports
- locate all raw Solr endpoint URLs
- locate query-string construction helpers
- locate direct parsing of Solr responses
- locate indexing and delete paths
- locate retry, timeout, and circuit-breaker policies
- locate feature flags or routing controls that can support staged rollout
- locate background jobs and scheduled consumers

This is often more useful than jumping straight into code generation.

---

## Test Expectations

At minimum, expect:

- unit tests for query factory output or normalized query intent
- integration tests for primary read flows
- integration tests for write paths if the app owns indexing
- response-mapping tests for key DTOs
- fallback-path tests where rollout logic exists

For higher-risk workloads, add:

- side-by-side comparison tests against source and target
- replay tests using captured queries
- error-path tests for auth, timeout, and partial failures

If the app layer changed materially and only manual smoke tests exist, the migration is under-tested.

---

## Code Review Checklist

- Are engine-specific imports contained?
- Is query construction centralized?
- Are domain DTOs preserved?
- Are auth and connectivity failures observable?
- Is dual-write or fallback logic explicit and testable?
- Are hidden consumers accounted for?
- Are reviewers able to tell which code paths are temporary migration scaffolding?

The best migration reviews remove accidental complexity while adding execution safety.

---

## Decision Heuristics

- If search client imports exist across many files, refactor behind an interface before large-scale query rewrites.
- If auth changes are still unproven, treat that as the first implementation milestone.
- If the app cannot switch read paths cleanly, do not promise staged cutover behavior yet.
- If query logic is duplicated across services, centralize intent before tuning engine behavior.
- If a consumer is low-visibility but business-relevant, pull it into the migration plan early rather than treating it as a cleanup task.
- If the AI can generate a patch quickly but the code becomes less reviewable, reject the patch and refactor first.

---

## Common Failure Modes

- Swapping clients without redesigning query construction
- Treating application changes as minor compared to cluster work
- Hardcoding large blocks of Query DSL in controllers or route handlers
- Forgetting background jobs, admin tools, or hidden consumers
- Ignoring auth and connection management until late
- Building dual-write with no divergence reporting
- Returning raw engine response objects outside the search layer

---

## Open Questions

- Which platform-specific worked examples would be most useful next: Spring Boot, Python service, or Node API?
- Should the repo include a compact “consumer inventory” template artifact for platform integration reviews?
- Which of the current demos should be extended with side-by-side adapter patterns for mirrored reads?
