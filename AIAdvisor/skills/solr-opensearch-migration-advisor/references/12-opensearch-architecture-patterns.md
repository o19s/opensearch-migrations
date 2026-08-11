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
