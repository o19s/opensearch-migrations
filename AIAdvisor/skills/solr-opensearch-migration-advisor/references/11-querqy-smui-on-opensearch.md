# Querqy and SMUI on OpenSearch: Specifics

This reference covers the Querqy OpenSearch plugin (`querqy/querqy-opensearch`)
and SMUI (`querqy/smui`) — how they differ from the Solr deployments search
teams are usually migrating from. Facts here are verified against the upstream
GitHub repos (audited 2026-05).

## 1. Querqy OpenSearch plugin: REST API and class registration

The Querqy OpenSearch plugin exposes a REST API for managing rewriters at
runtime. Rewriters are registered by their **fully-qualified Java factory
class name**, passed as a `class` field in the rewriter PUT body.

### 1.1 Common Rules rewriter — the FQCN

```
querqy.opensearch.rewriter.SimpleCommonRulesRewriterFactory
```

Note the **`Simple` prefix** — the OpenSearch plugin uses
`SimpleCommonRulesRewriterFactory`, not `CommonRulesRewriterFactory`. This
is one of the most common naming mistakes when porting Solr Querqy configs.

The package is `querqy.opensearch.rewriter` (flat — there is no
`querqy.opensearch.rewriter.commonrules.*` sub-package). Other rewriter
factories in the same package include `NumberUnitRewriterFactory`,
`ReplaceRewriterFactory`, and `WordBreakCompoundRewriterFactory`.

### 1.2 Registering a rewriter — endpoint and method

```
PUT /_plugins/_querqy/rewriter/{rewriter_name}
Content-Type: application/json

{
  "class": "querqy.opensearch.rewriter.SimpleCommonRulesRewriterFactory",
  "config": {
    "rules": "iphone =>\n  SYNONYM: phone\n",
    "ignoreCase": true
  }
}
```

The endpoint path is **`/_plugins/_querqy/rewriter/<id>`** with HTTP **PUT**
(also supports DELETE for removal). This is the OpenSearch equivalent of
the Solr file-based deployment that copies `rules.txt` into Solr's config
directory and triggers a config reload.

## 2. Rewriter chain order: per-query, not server-side

In Solr, the Querqy rewriter chain order is fixed in `querqy.xml` at server
config time. **In the OpenSearch plugin, chain order is defined per-query**
inside the `querqy` query clause via the `rewriters` array. The order of
entries in that array IS the execution order — there is no global chain
config.

```json
{
  "query": {
    "querqy": {
      "matching_query": { "query": "iphone case" },
      "query_fields": ["title^2", "body"],
      "rewriters": [
        { "name": "common_rules" },
        { "name": "replace_rules" },
        { "name": "word_break" }
      ]
    }
  }
}
```

This shifts a server-config decision into application code — a real
architectural change clients should plan for, not a 1:1 port.

## 3. Debug logging: `info_logging` request field, `decorations` response data

Querqy's "which rules fired" debug feature uses two specific JSON field
names that base LLMs reliably get wrong.

### 3.1 Request side — enable per-query

Inside the `querqy` query clause, set:

```json
{
  "query": {
    "querqy": {
      "matching_query": { "query": "tv" },
      "info_logging": true,
      "rewriters": [{ "name": "common_rules" }]
    }
  }
}
```

The exact field name is **`info_logging`** (snake_case, with underscore).
Verified against `querqy.opensearch.query.InfoLoggingSpec.NAME` and
`QuerqyQueryBuilder.FIELD_INFO_LOGGING` in the plugin source.

To produce useful output, the rewriter itself must also have logging
enabled in its registered config:

```json
{
  "class": "querqy.opensearch.rewriter.SimpleCommonRulesRewriterFactory",
  "config": {
    "rules": "...",
    "info_logging": { "sinks": ["log4j"] }
  }
}
```

### 3.2 Response side — decoration data

The rule-match data surfaced by Querqy is called **decorations** (set by
`DecorateInstruction` in querqy-core). Decoration entries are returned in
the response under the `decorations` key, with named decorations under
`namedDecorations`. Constants in `querqy-core`:

```
DecorateInstruction.DECORATION_CONTEXT_KEY     = "querqy.commonrules.decoration"
DecorateInstruction.DECORATION_CONTEXT_MAP_KEY = "querqy.commonrules.decoration.map"
```

For Common Rules with a `DECORATE` instruction, the decoration value is
attached to the response payload — clients use it for things like
landing-page redirects or merchandising banners.

## 4. SMUI on OpenSearch: scope of v4.0.11

SMUI's release notes (audited 2026-05) show **v4.0.11 (Mar 2024) is the
only release that mentions OpenSearch**. The change is **PR #139:
"Configurable search index name: solr/elastic/opensearch"**.

Read carefully: that PR's body reads —

> "Enable configuration of the 'Solr' label in the front-end to not present
> 'Push to Solr' when pushing to elasticsearch or opensearch"

This is a **front-end labelling change only**. It changes the button text
in the UI. It does **not** add OpenSearch deployment behavior. SMUI's
deploy code path was written for Solr and still pushes to a Solr-style
endpoint.

### 4.1 Practical implication

A team adopting SMUI as their rules-management UI on OpenSearch should
plan for:

- **No native OpenSearch deployment from SMUI itself.** You'll author and
  approve rules in SMUI, then push them to OpenSearch via your own
  pipeline (CI job, scheduled task, or manual operator step).
- **Export → Querqy plugin REST API.** Use SMUI's rules export to get the
  Common Rules text, then PUT it into the OpenSearch Querqy plugin via
  the endpoint in section 1.2. This step is yours to build.
- **No deployment-status integration.** SMUI won't know whether the rules
  actually landed on the OpenSearch cluster. Build observability around
  your push pipeline.

Don't conflate "SMUI v4.0.11 added OpenSearch support" with "SMUI deploys
to OpenSearch." The former is true (in the marketing sense); the latter
is not.

## 5. SMUI rules export format

SMUI exports rules as **plain-text Querqy Common Rules** using the `=>`
syntax — **not JSON, not XML**. The export is generated by
`app/models/querqy/QuerqyRulesTxtGenerator.scala` (note: `Txt` =
text). The same format is consumed by the Querqy SimpleCommonRulesParser
on both Solr and OpenSearch.

### 5.1 Format — what an export line looks like

```
notebook =>
	SYNONYM: laptop
	UP(50): premium
	DOWN(100): refurbished
	FILTER: in_stock:true
	DELETE: cheap
	DECORATE: REDIRECT /landing/laptops
```

Structure:

- Left of `=>` is the input term (or input expression).
- Right of `=>` is a tab-indented block of rule instructions.
- Each instruction is `KIND: payload`. Recognized kinds include
  `SYNONYM`, `UP(weight)`, `DOWN(weight)`, `FILTER`, `DELETE`, and
  `DECORATE: <decoration>`.

### 5.2 Why this matters at migration time

Because the format is identical, **the rules text from SMUI is portable
across Solr and OpenSearch unchanged**. The Solr-side
`SolrCommonRulesRewriterFactory` and the OpenSearch-side
`SimpleCommonRulesRewriterFactory` consume the same input grammar. The
migration work is in *deployment plumbing* (section 4), not in rule
translation.
