# Relevance Tuning: Solr to OpenSearch

## BM25 Scoring Parameters

OpenSearch defaults to BM25. The two tunable parameters:

- **k1** (term frequency saturation, default 1.2): Controls how much repeated term matches improve score. Lower (0.8) for short fields like title; higher (1.5-2.0) for keyword-heavy fields (tags, categories). k1=0 means only IDF matters.
- **b** (length normalization, default 0.75): Controls penalty for long documents. Lower (0.5) for title fields where length is uniform; higher (0.9) for body fields with high length variance. b=0 disables normalization entirely.

**When to tune:** Only after establishing a baseline measurement. Default BM25 parameters are reasonable for most use cases. Tune when analysis shows specific field types are over- or under-weighted.

## Per-Field Similarity Settings

Define custom similarity per field at index creation time:

```json
PUT product-index/_settings
{
  "index.similarity.title_bm25": { "type": "BM25", "k1": 0.8, "b": 0.5 },
  "index.similarity.body_bm25":  { "type": "BM25", "k1": 1.2, "b": 0.75 }
}
```

Then assign in mappings: `"similarity": "title_bm25"`. This is more precise than global parameter changes and is the recommended approach for multi-field search.

## function_score for Business Signals

BM25 handles text relevance. Use `function_score` to blend in business metrics:

- **Popularity:** `field_value_factor` with `modifier: "log1p"` on sales/views/ratings fields
- **Freshness:** `gauss` decay on date fields (e.g., `scale: "30d"`, `decay: 0.5`)
- **Geo proximity:** `gauss` decay on `geo_point` fields
- **Inventory/availability:** `filter` + `weight` for conditional boost (e.g., in-stock x2.0)

**boost_mode** controls how function score combines with query score:
- `multiply` (default): Preserves relevance ordering, amplifies/dampens
- `sum`: Additive; can elevate low-relevance docs if function score is high
- `replace`: Ignores query relevance entirely (rarely appropriate)

## Solr TF-IDF to OpenSearch BM25 Migration

Solr historically defaulted to ClassicSimilarity (TF-IDF). OpenSearch uses BM25 exclusively. Key differences:

- TF-IDF uses raw term frequency; BM25 saturates (diminishing returns via k1)
- TF-IDF length normalization is simpler; BM25's b parameter gives finer control
- Documents that ranked well due to high term repetition in Solr may rank differently under BM25
- **Expect score values to change.** Do not compare raw scores across engines. Compare ranked output using metrics.
- Solr `bf` (boost function) and `bq` (boost query) map to OpenSearch `function_score` and `bool.should` respectively

## The Baseline-Tune Loop

This is the core methodology. Never skip the baseline.

```
Measure (run scoring tool against judgment set)
  -> Log (record score + config state)
  -> Analyze (identify worst-performing queries)
  -> Hypothesize (one change at a time)
  -> Test (compare score delta vs. baseline)
  -> Decide (promote / discard)
  -> Report -> Measure (repeat)
```

**Constraints:**
- One hypothesis per experiment. Do not bundle changes.
- Always compare against the original logged baseline, not the prior iteration.
- Run at sprint cadence. Burst tuning before cutover is a red flag.
- Maintain a decision log: "Tried synonym expansion on [cluster], hurt nDCG by 0.03 -- discarded."

## Relevance Metrics

| Metric | Use When |
|--------|----------|
| **nDCG@10** | Default for most migrations. Handles graded relevance (0-3 scale), position-weighted. |
| **P@k** | Simpler to explain to stakeholders. Good sanity check alongside nDCG. |
| **MRR** | "Find the right answer" tasks. Measures rank of first relevant result. |
| **ERR** | Navigational queries where user stops at first perfect result. |

**For Solr-to-OpenSearch migrations:** Use nDCG@10 as primary metric, P@5 as secondary.

## Judgment Methodology

- Use a 4-point scale: Perfect (3) / Good (2) / Fair (1) / Bad (0). Document what each level means for this product.
- Select query set from actual analytics: top 100-200 queries by frequency plus representative samples per information-need category.
- Calibrate with a pilot round (2-3 judges, 20-30 queries). Measure Fleiss' Kappa. If Kappa < 0.4, clarify the rubric before scaling.
- Separate annotation from hypothesis formation. Judges should not propose tuning changes.
- Customer analytics decide *which* queries to judge, not *how* to judge them.

## Tooling

| Tool | Role | When |
|------|------|------|
| **Quepid** | Interactive relevance exploration, building judgment sets, stakeholder demos | During migration (offline measurement) |
| **RRE** | Automated regression testing in CI/CD pipelines | Once new engine is in staging |
| **A/B testing** | Live traffic comparison post-cutover | After migration, not during |

**Quepid workflow:** Create case -> configure search endpoint -> import query set -> set scorer (nDCG@10) -> rate results (0-3) -> export baseline -> clone case for experiments -> compare deltas.

**Export and version-control Quepid case JSON.** Losing it means losing reproducibility.

## Decision Heuristics

- nDCG on new engine < old engine after 3 tuning sprints: escalate. May be schema, scoring, or judgment set problem.
- Single experiment moves nDCG by > 0.05: verify. That delta is large -- likely a confounding variable.
- Stakeholders ask for A/B testing before cutover: reframe. A/B is post-cutover. Pre-cutover answer is Quepid + offline judgments.
- Client has no query analytics: don't start judgments yet. First deliverable is analytics instrumentation.
- Use the Explain API (`GET index/_explain/doc_id`) to debug why specific documents score unexpectedly.
