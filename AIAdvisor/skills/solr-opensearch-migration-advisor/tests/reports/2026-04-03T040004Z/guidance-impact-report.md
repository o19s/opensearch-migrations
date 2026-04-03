# Guidance Impact Report

| Backend | Session | Bare | Guided | Delta | Tests |
|---------|---------|------|--------|-------|-------|
| ollama (llama3.2:latest) | 2026-04-03T040004Z | 2/4 terms | 3/4 terms | +1 | ✅ 3 passed, 0 failed |

## Test Results

| # | Test | Result | What it checks | Evidence | Next Step |
|---|------|--------|----------------|----------|-----------|
| 1 | bare_lacks_guided_terms | ✅ | Bare model misses at least one expected term, proving guidance adds knowledge | Bare missed 2/4: ['script_score', 'join_replacement'] | No action — guidance is adding value the bare model lacks. |
| 2 | guided_hits_most_terms | ✅ | Guided model produces >= 3/4 expected terms | Hit 3/4: ['script_score', 'rebuild_handlers', 'nested_mapping'] | missed: ['join_replacement'] | Steering is effective. Review scorecard for per-term detail. |
| 3 | guidance_improves_term_coverage | ✅ | Guided response produces more expected terms than bare | Guided: 3, Bare: 2, Delta: +1 | Guidance adds measurable value. Ready for PR/review. |

## Expected Term Scorecard

Each row is a technical term the steering content should cause the model to produce.

| Term | Bare | Guided | Matched Phrase | Source | Next Step |
|------|------|--------|----------------|--------|-----------|
| script_score | ➖ miss | ✅ `script_score` | `script_score` | `incompatibilities.md` | ✅ Guidance is adding this term. No action needed. |
| rebuild_handlers | ✅ `not directly equivalent` | ✅ `no direct equivalent` | `no direct equivalent` | `incompatibilities.md` | ⚙️ Model already knows this. Consider a harder variant. |
| nested_mapping | ✅ `nested` | ✅ `nested` | `nested` | `incompatibilities.md` | ⚙️ Model already knows this. Consider a harder variant. |
| join_replacement | ➖ miss | ❌ **miss** | `—` | `incompatibilities.md` | ❌ See Diagnosis below for LLM analysis. |

## Diagnosis: Missed Terms

For each expected term the guided model missed, the LLM was asked: *"Why didn't you mention this, and what change to the steering would fix it?"*

### join_replacement

**Steering says:** Joins: Solr `!join` maps to `terms` lookup query or flattened index design.

**Looked for:** `terms lookup`, `terms query`, `flattened`, `denormalize`, `denormaliz`

**LLM self-diagnosis:**

> I might have omitted the "terms lookup" and related concepts because they were not explicitly mentioned in the steering guidance, which focused on joins. To be more likely to include these concepts, I would need a steering guidance that specifically mentions Solr's `!join` mapping as equivalent to OpenSearch's terms query or flattened index design. Alternatively, if the prompt was revised to ask about migrating specific features from Solr to OpenSearch, such as "How do we migrate our Solr 'terms' lookup queries to OpenSearch?" I would be more likely to include these concepts in my response.

**Suggested next step:** Strengthen the `join_replacement` section in `incompatibilities.md` based on the diagnosis above, then re-run this test.

---

## Appendix A: Scenario

> A client is migrating from Solr to OpenSearch. They have function queries for custom scoring, filter queries (fq) for faceted navigation, custom request handlers with business logic, Solr join queries between collections, and nested child documents. They say: 'It's all Lucene underneath, so most of it ports directly.' Respond as a migration consultant in 2-3 paragraphs.

## Appendix B: Bare Response (no steering)

I understand your client's confidence in the idea that "it's all Lucene underneath," but I'd like to caution them against assuming a seamless porting process. While OpenSearch is built on top of Apache Lucene, there are significant differences between Solr and OpenSearch that may require additional effort to migrate successfully.

Function queries, for example, work similarly in both Solr and OpenSearch, but the implementation details differ. In Solr, function queries use a specific syntax and are executed at query time. In OpenSearch, function queries are implemented using OpenSearch's scripting language, which has its own set of features and limitations. Similarly, filter queries (fq) may need to be adjusted as OpenSearch uses a different syntax for faceted navigation. Custom request handlers with business logic will also require adaptation, as OpenSearch's request handling is more modular and flexible than Solr's.

Additionally, the join query functionality in Solr is not directly equivalent to OpenSearch's join queries, which are designed for more complex data relationships. And while nested child documents can be handled in both Solr and OpenSearch, the implementation details may differ. Given these differences, I would recommend a thorough evaluation of each specific use case to ensure a smooth migration process. It may also be beneficial to engage with the OpenSearch community or seek guidance from experienced users to minimize potential issues during the transition.

## Appendix C: Guided Response (with steering)

I understand the client's optimism about the similarity between Solr and OpenSearch, but I must temper their enthusiasm with a dose of reality. While it's true that both Solr and OpenSearch are built on top of Lucene, there are significant differences in their underlying architectures, APIs, and design philosophies.

Function queries, for example, have different syntax and semantics in OpenSearch compared to Solr. In OpenSearch, you'll need to use the `script_score` query type with a script that defines your custom scoring function, whereas in Solr, you can use the `function_query` query type. Similarly, filter queries (fq) are handled differently in OpenSearch, where you'll need to use the `filter` query type within a `bool` query, rather than relying on Solr's `fq` syntax.

Furthermore, custom request handlers with business logic will require significant rework in OpenSearch, as there is no direct equivalent. Similarly, join queries between collections and nested child documents have different APIs and design considerations in OpenSearch compared to Solr. While it's true that Lucene provides a solid foundation for both platforms, the nuances of each platform's API and design patterns can't be ignored. A thorough understanding of these differences is essential to ensure a successful migration.
