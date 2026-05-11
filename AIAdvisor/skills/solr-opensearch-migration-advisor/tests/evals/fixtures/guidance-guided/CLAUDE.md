# Solr to OpenSearch Migration Advisor (guided — with reference content)

You are a Solr to OpenSearch migration advisor. Use the reference material
below to provide accurate, specific answers. Cite the reference section
you drew from when relevant.

Be concise. Give specific class names, endpoints, field names, and
version numbers from the references — don't dodge with "check the docs."

---

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


---

# OpenSearch Architecture Patterns That Differ From Solr

Two patterns that don't translate 1:1 from Solr concepts and that
migration teams underestimate: query-time interception (Search Pipelines)
and rolling-window write routing (ISM + write-aliases).

## 1. Search Pipelines — query and response interception in OpenSearch 2.x

### 1.1 What it is

**Search Pipelines** is OpenSearch's framework for intercepting and
modifying search requests and responses without changing client code or
plugin code. It is the closest native OpenSearch equivalent to Solr's
`SearchComponent` / `UpdateRequestProcessor` extension points and is
also the migration target for things like Querqy's `DELETE` rule when
the Querqy plugin itself is unavailable (e.g. AWS-managed OpenSearch).

### 1.2 When it was introduced

Verified against the OpenSearch GitHub release notes:

- **OpenSearch 2.7.0** (Apr 2023, PR #6587): "Add initial search pipelines"
- **OpenSearch 2.9.0** (Jul 2023, PR #8613): "Introduce full support for
  Search Pipeline" — also added `SearchPhaseResultsProcessor`

So: **Search Pipelines were introduced in OpenSearch 2.7 and reached full
support in 2.9**. Anything before 2.7 has no native equivalent; you'd
need a custom plugin or application-layer wrapping.

### 1.3 Three processor types

A pipeline is an ordered sequence of processors of three categories:

| Processor type | Runs | Typical use |
|---|---|---|
| **Search request processor** | Before the query reaches the shards | Rewriting queries, injecting filters, blocking terms (Querqy DELETE-style use cases live here) |
| **Search response processor** | After hits are returned, before the client sees them | Reranking, redacting fields, enriching with external data |
| **Search phase results processor** | Between query phase and fetch phase | Modifying intermediate results (e.g. cross-shard normalization) |

### 1.4 Defining and attaching a pipeline

```
PUT /_search/pipeline/strip_cheap
{
  "request_processors": [
    {
      "script": {
        "source": "ctx.body.query.bool.must_not.add([\"match\": [\"text\": \"cheap\"]])"
      }
    }
  ]
}
```

Pipelines can be attached three ways: per-request via
`?search_pipeline=strip_cheap`, as an index default via the
`index.search.default_pipeline` setting, or globally via cluster setting.

### 1.5 The Querqy-DELETE migration example

In Solr+Querqy, `cheap laptop => DELETE: cheap` removes the term `cheap`
before query parsing. On OpenSearch *with* the Querqy plugin, identical
rules text works (see reference 11). On OpenSearch *without* Querqy
(notably AWS-managed OpenSearch Service, which forbids custom plugins),
the equivalent is a search request processor — usually `script` for
ad-hoc logic, or a custom processor packaged as a plugin if the rule set
is large.

## 2. Rolling-window architecture — collection aliases vs index aliases

### 2.1 The Solr pattern teams are migrating from

In SolrCloud, a collection alias can simultaneously **route writes to one
target collection while searching across many**. A common pattern:

```
alias "events_write"  -> events_2026_05      (writes go here)
alias "events_search" -> events_2026_*       (searches all months)
```

### 2.2 Why naive index aliases don't suffice in OpenSearch

OpenSearch's index aliases are different in one critical way: **an alias
can fan out searches across many indices, but writes can only go to one
index — and only if exactly one of the aliased indices has
`is_write_index: true`**.

So the Solr pattern doesn't port as a single-alias-with-different-views
trick. You need two coordinated mechanisms.

### 2.3 The OpenSearch pattern: ISM rollover + `is_write_index` alias

The idiomatic replacement is **ISM (Index State Management) policies
with a rollover action**, combined with a write alias:

```json
PUT _plugins/_ism/policies/events_rollover
{
  "policy": {
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [
          { "rollover": { "min_size": "50gb", "min_index_age": "30d" } }
        ],
        "transitions": [{ "state_id": "warm", "conditions": { "min_index_age": "30d" } }]
      },
      { "name": "warm", "actions": [], "transitions": [] }
    ],
    "ism_template": [{ "index_patterns": ["events-*"] }]
  }
}
```

Bootstrap the alias with `is_write_index` set:

```
POST _aliases
{
  "actions": [
    {
      "add": {
        "index": "events-000001",
        "alias": "events_write",
        "is_write_index": true
      }
    }
  ]
}
```

Then index against the alias `events_write`. ISM monitors the rollover
condition; when it triggers, ISM creates `events-000002`, atomically
flips `is_write_index` from the old index to the new one, and writes
continue uninterrupted.

For the read side, point a separate alias at all generations:

```
POST _aliases
{
  "actions": [
    { "add": { "index": "events-*", "alias": "events_search" } }
  ]
}
```

### 2.4 Migration checklist for the rolling-window pattern

- **Pick the rollover trigger** (size, age, doc count) that matches the
  Solr collection-rotation cadence. ISM supports any combination.
- **Pre-create the bootstrap index** with the `-000001` suffix and the
  write alias attached with `is_write_index: true`. ISM will not
  bootstrap the first index for you.
- **Do not flip `is_write_index` manually after bootstrap** — ISM owns
  it. Manual flips while ISM is active will race.
- **Keep the read alias as a wildcard pattern** so newly rolled indices
  are picked up automatically.
- **Plan for index template** governance — ISM creates new indices via
  index templates; missing template = wrong settings on the rollover.
