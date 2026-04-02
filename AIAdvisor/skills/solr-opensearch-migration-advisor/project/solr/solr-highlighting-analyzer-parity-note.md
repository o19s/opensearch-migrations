# Solr Highlighting / Analyzer Parity Note

Date: 2026-03-23

This note covers the Solr-specific migration risk around highlighting and analyzer parity.
It is related to query translation, but it is not reducible to request-parameter translation.

That distinction matters.

## Why This Topic Matters

Highlighting is one of the most user-visible parts of search behavior.

When it looks wrong, users often experience the migration as:

- "search is broken"
- "results are weird"
- "the right result is there but the snippet looks wrong"

And many highlighting failures are not caused by the highlight request syntax itself.
They are caused by differences in:

- analyzers
- search analyzers vs index analyzers
- copyField / aggregate text field design
- term-vector strategy
- passage selection behavior

So OSC should treat highlighting as a combined **query + mapping + analyzer** problem.

## What Upstream `#2383` Already Tells Us

The current upstream highlighting PR is [#2383](https://github.com/opensearch-project/opensearch-migrations/pull/2383).

Useful signals from that PR:

- it maps `hl.*` request params into OpenSearch `highlight`
- it translates response shape back into Solr-style top-level `highlighting`
- it explicitly notes that highlight fragment boundaries may differ slightly even when the data is
  identical
- it now routes `hl.q` through the shared query parsing path rather than raw passthrough
- it warns on unsupported or unrecognized highlighting params/methods

OSC read:

- this is the right direction for request/response translation
- but it does not remove the underlying parity risk from analyzer and mapping differences

## OSC View

The correct top-line message is:

- highlighting request translation is necessary
- highlighting parity depends heavily on analyzer and field-design parity

A migration can have a technically correct `hl=true` translation and still produce user-visible
snippet drift for perfectly understandable reasons.

That is not automatically a failure, but it does need to be called out and tested deliberately.

## What OSC Should Care About

### 1. Index analyzer vs search analyzer parity

Our repo already treats this as a core migration topic.

Examples in local material:

- TechProducts has distinct `text_general_index` and `text_general_query`
- the schema converter now carries analyzer names forward into OpenSearch settings
- the repo references repeatedly stress that analyzer mismatches drive many relevance issues

OSC concern:

- if highlighting is evaluated without confirming index/search analyzer parity, teams may blame the
  highlighter for what is really an analyzer mismatch

### 2. Synonyms and analyzer-chain behavior

This is especially important when query-time synonym expansion exists.

Examples from local fixtures:

- Solr `SynonymGraphFilterFactory`
- stopword + lowercase + synonym pipelines

OSC concern:

- highlighted snippets can differ if query expansion behaves differently
- this can show up even when the main hit list looks approximately correct

### 3. Field design and copyField intent

Highlighting quality depends on which field is actually searched and highlighted.

Examples:

- copied aggregate fields like `_text_` / `text_all`
- multi-field mappings
- exact vs analyzed variants

OSC concern:

- if Solr relied on `copyField` patterns and OpenSearch uses different aggregate/search fields,
  highlight behavior may drift even with good request translation

### 4. Highlight method and term-vector assumptions

The upstream PR maps:

- `hl.method=unified` -> `unified`
- `original` -> `plain`
- `fastVector` -> `fvh`

Local source material also notes term vector mapping:

- Solr `termVectors="true"` -> OpenSearch `term_vector: "with_positions_offsets"`

OSC concern:

- if a workload depends on FVH-style behavior, request translation alone is not enough
- the mapped fields must also carry compatible term-vector settings

### 5. Fragment boundary drift

The upstream PR explicitly calls out that Solr and OpenSearch may choose slightly different
highlight windows even when both use Lucene-derived highlighters.

OSC concern:

- exact snippet-string parity may be the wrong success criterion
- but teams still need a test policy for what counts as acceptable drift

## Questions OSC Should Ask While Reviewing Highlighting Work

- Is this request/response translation only, or does the test setup also validate analyzer parity?
- What highlight methods are considered fully supported vs approximate?
- How is `hl.q` translated today, and how will it evolve as query coverage improves?
- Are copied aggregate fields and multi-field designs represented in test fixtures?
- What evidence will distinguish acceptable fragment drift from analyzer/mapping regressions?

## Recommended Test Shapes

### Basic highlight on analyzed field

```text
q=title:solr&hl=true&hl.fl=title,body
```

Goal:

- verify request/response shape
- establish baseline fragment behavior

### Highlight with custom tags

```text
q=title:solr&hl=true&hl.fl=title&hl.simple.pre=<b>&hl.simple.post=</b>
```

Goal:

- verify tag customization
- allow boundary drift while keeping tag semantics correct

### Highlight with translated `hl.q`

```text
q=*:*&hl=true&hl.q=title:solr&hl.fl=title,body
```

Goal:

- verify that highlight query semantics track the evolving query translation path

### Highlight on copyField-driven search field

```text
q=laptop&defType=edismax&qf=title^3 description^1 tags^0.5&hl=true&hl.fl=title,description
```

Goal:

- verify the interaction among aggregate search behavior, source fields, and snippet rendering

### Highlight with analyzer-sensitive synonyms

Representative expectation:

- query term expands through query-time synonym graph
- highlighted output still surfaces explainable matches

Goal:

- verify that analyzer parity work and highlighting work are not assessed independently

## Good vs Weak Signals From Amazon

Good signals:

- they explicitly distinguish request translation from analyzer/mapping parity
- they test `hl.q` through the shared query path
- they allow non-exact fragment boundaries while still validating meaningful highlight behavior
- they can say how FVH / term-vector-dependent cases are handled

Weak signals:

- they present highlighting as solved because `hl.*` params map cleanly
- they rely only on exact snippet string equality
- they do not discuss analyzer parity, copied fields, or term vectors
- they cannot explain how `hl.q` relates to the broader query translation roadmap

## OSC Bottom Line

Highlighting is one of the clearest examples of why migration confidence cannot come from request
translation alone.

The right OSC stance is:

- support the upstream highlighting PR as useful progress
- insist that highlighting parity be discussed together with analyzer and field-design parity
- treat snippet drift as a governed testing question, not as proof that request translation is enough
