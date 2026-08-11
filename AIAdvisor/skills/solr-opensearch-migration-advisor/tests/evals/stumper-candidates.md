# Stumper Candidates: Solr→OpenSearch Migration

20 questions designed to stump a bare LLM (no steering/reference content).
Use these to manually test bare Haiku from `/tmp`, then craft assertions
and steering/reference content for the ones that genuinely fail.

Test with: `cd /tmp && claude --model claude-haiku-4-5-20251001 --print "QUESTION"`

---

## Querqy / SMUI (niche o19s tools — highest stumper confidence)

### 1. Querqy OpenSearch class names
**Question:** What is the exact fully-qualified Java class name for registering a CommonRules rewriter in the OpenSearch Querqy plugin REST API? Give just the class string.
**Challenge:** OpenSearch Querqy uses different package prefix and Factory suffix vs Solr. LLMs guess the Solr class name or refuse.
**Criterion A:** `icontains: "CommonRulesRewriterFactory"`
**Criterion B:** `icontains: "querqy.opensearch.rewriter"`

### 2. Querqy infoLogging field names
**Question:** In the OpenSearch Querqy plugin, what is the exact JSON field name you add inside a querqy query clause to enable debug logging of which rules fired? And what is the exact field name in the response that contains the decoration/rule-match data? Give just the two field names.
**Challenge:** Bare LLMs refuse to guess or give wrong field names. This is barely documented.
**Criterion A:** `contains-any: ["info_logging", "infoLogging"]`
**Criterion B:** `contains-any: ["querqy_decorations", "decorations"]`

### 3. Querqy rewriter chain order mechanism
**Question:** In Solr, Querqy rewriter chain order is defined in querqy.xml. In the OpenSearch Querqy plugin, where is the chain order defined? Is it in a config file, the cluster state, or per-query? Give the exact mechanism.
**Challenge:** The answer is per-query (in the `rewriters` array). LLMs often guess config file or cluster state.
**Criterion A:** `contains-any: ["per-query", "per query", "query time", "in the query"]`
**Criterion B:** `contains-any: ["rewriters array", "rewriters list"]`

### 4. SMUI deployment mechanism change
**Question:** SMUI deploys Querqy rules to Solr by copying a rules text file to Solr's config directory and triggering a config reload. When targeting OpenSearch instead, what specific mechanism replaces the file-copy deployment? Name the exact API endpoint.
**Challenge:** LLMs know the concept but may not know the exact endpoint `/_plugins/_querqy/rewriter/<id>`.
**Criterion A:** `contains-any: ["_querqy/rewriter", "_plugins/_querqy"]`
**Criterion B:** `icontains: "PUT"`

### 5. SMUI v4.0.11 OpenSearch scope (labelling vs deployment)
**Question:** SMUI v4.0.11 added OpenSearch support according to the release notes. As a migration consultant, what specifically did v4.0.11 add — full OpenSearch deployment parity with Solr, or something narrower? What does this mean for a team planning to use SMUI as their rules-management UI on OpenSearch?
**Challenge:** Original "minimum version" framing was based on a guess (3.14) that turned out to be wrong. Audit of querqy/smui releases (2026-05-10) shows v4.0.11 (Mar 2024) is the only release mentioning OpenSearch, and PR #139 only changed UI labels — not deployment behavior. The real consultant insight is that SMUI lacks first-class OpenSearch deployment parity.
**Criterion A:** `contains-any: ["label", "labelling", "labeling", "UI", "front-end", "frontend", "button", "cosmetic"]` (must identify the change as UI-level)
**Criterion B:** `contains-any: ["not", "narrow", "limited", "no deployment", "doesn't deploy", "does not deploy", "manual", "still", "additional", "outside"]` (must flag the deployment gap)

### 6. Querqy DOWN weight → negative_boost conversion
**Question:** In Querqy, a DOWN(500) rule penalizes matches. To translate this to OpenSearch's boosting query with negative_boost, what is the exact formula to convert the DOWN weight to a negative_boost value? Show the formula and the result for DOWN(500).
**Challenge:** LLMs guess at formulas or refuse. The conversion is `1/(1+weight)` = 0.001998.
**Criterion A:** `icontains: "negative_boost"`
**Criterion B:** `contains-any: ["0.002", "0.001", "1/(1+"]` (approximate result)

### 7. SMUI rule export format
**Question:** What is the format of a SMUI rules export file? Is it JSON, XML, or something else? Show an example of what the export looks like for a term with SYNONYM and UP rules.
**Challenge:** LLMs fabricate JSON formats. SMUI exports Querqy Common Rules plain text with `=>` syntax.
**Criterion A:** `contains-any: ["plain text", "Common Rules", "text format"]`
**Criterion B:** `icontains: "=>"`

## Schema and Field Migration (subtle behavioral differences)

### 8. copyField → multi-fields vs copy_to
**Question:** In our TMDB Solr schema, we have copyField rules that copy title to title_en (English analyzer) and title_bidirect_syn (bidirectional synonym analyzer). How should we represent these in OpenSearch? Should we use copy_to or multi-fields? Explain why.
**Challenge:** LLMs often recommend copy_to, but copy_to doesn't re-analyze with a different analyzer chain. Multi-fields is correct.
**Criterion A:** `contains-any: ["Use multi-fields", "use multi-fields", "multi-fields"]`
**Criterion B:** `contains-any: ["copy_to does not re-analyze", "copy_to copies raw", "not copy_to"]`

### 9. positionIncrementGap default difference
**Question:** Solr's default positionIncrementGap is 0. What is OpenSearch's default position_increment_gap value? A client migrating from Solr has multi-valued text fields where they INTENTIONALLY allow phrase matches across value boundaries (positionIncrementGap=0). What specific OpenSearch mapping change preserves this behavior?
**Challenge:** The default difference (Solr 0 vs OpenSearch 100) means silently broken phrase matching after migration. Most guides miss this.
**Criterion A:** `contains-any: ["100", "default is 100", "defaults to 100"]`
**Criterion B:** `icontains: "position_increment_gap"`

### 10. Dynamic field mapping explosion limit
**Question:** Our Solr schema uses 800+ dynamic fields (*_s, *_i, *_txt, *_dt). What specific OpenSearch setting will we hit, what is its default value, and what are the risks of increasing it?
**Challenge:** LLMs may know the setting name but not the default (1000) or the risks (cluster instability, slow mapping updates).
**Criterion A:** `contains-any: ["total_fields.limit", "total_fields"]`
**Criterion B:** `contains-any: ["1000", "1,000"]`

## Query Translation (where "close enough" breaks things)

### 11. LocalParams replacement architecture
**Question:** We use Solr LocalParams extensively: {!boost b=recip(ms(NOW,date),3.16e-11,1,1) v=$qq} and {!type=edismax qf='title^2 body' v=$qq}. OpenSearch has no LocalParams. Give the specific architectural pattern we should use to replace this — not just "rewrite as Query DSL".
**Challenge:** LLMs give generic "rewrite" advice. The specific pattern is search templates with mustache variables + application-layer query assembly.
**Criterion A:** `contains-any: ["search template", "search_template", "mustache"]`
**Criterion B:** `contains-any: ["application layer", "application-layer", "query builder"]`

### 12. Search Pipelines for conditional query rewrite
**Question:** Querqy's DELETE rule conditionally removes terms from a query (e.g., 'cheap laptop => DELETE: cheap'). Without the Querqy plugin in OpenSearch, name the specific OpenSearch 2.x feature that can intercept and modify queries before execution. What is it called and when was it introduced?
**Challenge:** LLMs often don't know Search Pipelines by name or give wrong introduction dates.
**Criterion A:** `contains-any: ["search pipeline", "Search Pipeline"]`
**Criterion B:** `contains-any: ["request processor", "script processor"]`

### 13. bf additive vs boost multiplicative
**Question:** In Solr eDisMax, what is the exact difference between bf and boost in terms of how they combine with the relevance score? For each, give the exact OpenSearch function_score boost_mode value.
**Challenge:** LLMs conflate these. bf is additive (boost_mode: sum), boost is multiplicative (boost_mode: multiply).
**Criterion A:** `contains-any: ["additive", "adds to"]`
**Criterion B:** `contains-any: ["multiplicative", "multiplies", "multiply"]`

### 14. TF-IDF to BM25 on short fields
**Question:** When migrating from Solr 6.x (ClassicSimilarity/TF-IDF) to OpenSearch (BM25), what specific ranking behavior changes on short text fields like product titles? Name the exact BM25 parameter that controls term frequency saturation and what value approximates TF-IDF behavior.
**Challenge:** The parameter is k1 (default 1.2). Setting k1 very high (~100) approximates TF-IDF's linear TF behavior.
**Criterion A:** `icontains: "k1"`
**Criterion B:** `contains-any: ["saturation", "term frequency"]`

## Operational / AWS Managed Service

### 15. Querqy NOT on AWS OpenSearch Service
**Question:** We use Querqy in Solr for query rewriting. We're migrating to AWS OpenSearch Service (the managed service). Can we install the Querqy plugin? If not, what must we do instead?
**Challenge:** LLMs sometimes say yes. AWS does not allow custom plugin installation.
**Criterion A:** `contains-any: ["cannot", "can't", "not available", "not supported", "No."]`
**Criterion B:** `contains-any: ["native", "bool", "should", "synonym"]` (native replacement approach)

### 16. Collection aliases write routing
**Question:** Our Solr uses collection aliases that route writes to the latest time-partitioned collection while searching across all. OpenSearch index aliases can search multiple indices but can only write to one. How do we handle our rolling-window architecture?
**Challenge:** The answer involves ISM (Index State Management) policies with rollover action. LLMs may give generic alias advice.
**Criterion A:** `contains-any: ["ISM", "Index State Management", "rollover"]`
**Criterion B:** `icontains: "is_write_index"`

### 17. Atomic updates without _source
**Question:** Our Solr index has stored=false on most fields but supports atomic updates via docValues. We're migrating to OpenSearch. What specific problem will we hit with partial updates?
**Challenge:** OpenSearch requires _source for partial updates. No _source = no partial updates. Must re-architect.
**Criterion A:** `icontains: "_source"`
**Criterion B:** `contains-any: ["cannot", "not possible", "requires", "must"]`

## Consultant-Grade Judgment (from stump-the-chumps)

### 18. Lucene-underneath fallacy
**Question:** A client says "It's all Lucene underneath, so most of it ports directly." As a migration consultant, give your response. Be specific about where this assumption breaks.
**Challenge:** LLMs give decent general answers but may not name all key divergence areas (query parsers, scoring defaults, operational model).
**Criterion A:** `contains-any: ["query parser", "parser"]`
**Criterion B:** `contains-any: ["BM25", "scoring", "similarity"]`

### 19. Mechanical translation fantasy
**Question:** A client says their Solr-to-OpenSearch migration is "mostly config conversion work." Name 3 specific areas that require genuine redesign, not just translation.
**Challenge:** Must name specific areas (not just "relevance" but e.g., "analyzer behavior audit", "custom handler decomposition", "aggregation semantics").
**Criterion A:** `contains-any: ["redesign", "re-design", "rethink"]`
**Criterion B:** `contains-any: ["analyzer", "handler", "scoring", "relevance"]`

### 20. Plugin/custom handler dependency audit
**Question:** A client says "We didn't think any custom Solr components were important." What specific component types should be inventoried, and why is this claim dangerous?
**Challenge:** Must insist on systematic inventory of request handlers, update processors, search components, custom query parsers.
**Criterion A:** `contains-any: ["request handler", "RequestHandler"]`
**Criterion B:** `contains-any: ["update processor", "UpdateProcessor", "search component", "SearchComponent"]`

---

## Usage

1. Test each question bare: `cd /tmp && claude --model claude-haiku-4-5-20251001 --print "QUESTION"`
2. Mark which ones genuinely fail (LLM says "I don't know", gives wrong answer, or misses the key point)
3. For each fail, write steering + reference content that would make it pass
4. Add to `eval-guidance-impact.yaml` with the criteria above (adjust based on what you see)
5. Re-test to confirm the red→green flip
