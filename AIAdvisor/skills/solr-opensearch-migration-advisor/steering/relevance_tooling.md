# Relevance Tooling Migration Steering

## Querqy

Querqy is an open-source query rewriting library maintained by O19s and the
community.  It runs as a plugin on Solr, Elasticsearch, and OpenSearch.  The
rule engine (`querqy-core`) is platform-agnostic; only the plugin integration
layer changes per engine.

### Rule types (Common Rules Rewriter)

| Rule | What it does | Ports cleanly? |
|------|-------------|----------------|
| SYNONYM | Expand query with equivalent terms | Yes — generic syntax is engine-neutral |
| UP / DOWN | Boost or bury matching documents | Mostly — rules using engine-native boost syntax need rewriting |
| FILTER | Add mandatory filter clauses | Only if using generic syntax; Solr `fq`-style filters must be rewritten to OpenSearch Query DSL |
| DELETE | Remove terms before analysis | Yes |
| DECORATE | Attach metadata (redirects, flags) | Yes |

### Migration path

1. **Generic rules port without changes.** Rules that use Querqy's own syntax
   (not engine-native expressions) transfer as-is.
2. **Engine-native rules need rewriting.** Any rule containing Solr-specific
   syntax (e.g., `fq` filter format, Solr field syntax in boost expressions)
   must be converted to OpenSearch Query DSL equivalents.
3. **Plugin installation differs.** Solr loads Querqy as a JAR via
   `solrconfig.xml`.  OpenSearch uses `bin/opensearch-plugin install`.
   Configuration moves from Solr XML config to OpenSearch REST APIs.
4. **AWS Managed OpenSearch requires custom plugin upload.** Querqy is not
   pre-installed.  Custom plugin support is available on OpenSearch 2.15+ in
   select regions.  Not available on Serverless.
5. **Field name audit.** Solr dynamic field conventions (`*_s`, `*_txt`) often
   change during migration.  Every rule referencing a field name needs checking.

### What to ask during intake

- Is Querqy installed?  Which version?  Which rewriters are configured?
- How many rules exist?  Who maintains them?  How are they deployed?
- Are any rules using engine-native syntax (Solr `fq`, raw Lucene queries)?
- Is there a staging / testing workflow for rule changes, or are they pushed
  directly to production?

## SMUI (Search Management UI)

SMUI is a web frontend for managing Querqy Common Rules.  It lets
merchandisers and search managers maintain synonym, boost, filter, and delete
rules through a UI rather than editing text files.

### Migration path

- SMUI supports OpenSearch as a backend target (feature #139).
- Migration: reconfigure SMUI's connection settings to point at OpenSearch,
  verify rule publishing works, and audit any rules that used Solr-native
  filter/boost syntax.
- If the client manages rules through SMUI, the rule-export format is the
  migration artifact — not the raw rules files.

### What to ask during intake

- Is SMUI in use?  What version?  Who has access?
- How many active rules are managed through SMUI vs. hand-edited files?
- Is SMUI connected to a staging environment or directly to production?

## Learning to Rank (LTR)

Solr's LTR module and OpenSearch's LTR plugin have different APIs, feature
store formats, and model definition syntax.

### Migration path

- Models must be re-exported and re-registered in OpenSearch format.
- Feature stores (feature sets) need manual translation.
- Re-training is often needed because feature values change subtly between
  engines (different scoring, different analyzer behavior).
- The OpenSearch LTR plugin is community-maintained; verify compatibility with
  your target OpenSearch version.

### What to ask during intake

- Is LTR deployed in production?  Which model type (LambdaMART, linear)?
- Where is the training data?  Can it be reproduced?
- How often are models retrained?  Is there a pipeline?

## Querqy + SMUI + LTR: Combined Migration Sequence

When a client uses all three, the recommended order is:

1. **Querqy rules first** — these affect every query and must be validated
   before relevance measurement makes sense.
2. **SMUI reconfiguration** — switch the backend, verify rule publishing.
3. **LTR last** — retrain on the new engine's feature values after Querqy
   rules and analyzers are stable.

Do not attempt relevance baselining (Quepid / RRE) until Querqy rules are
ported and verified.  Otherwise you are measuring a system that does not
represent production behavior.
