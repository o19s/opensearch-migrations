# Solr to OpenSearch Incompatibilities

**Trigger:** When scanning a Solr `schema.xml`, `solrconfig.xml`, or query for migration blockers. Every incompatibility found must be recorded in `SessionState.incompatibilities` before proceeding — never silently skip.

## Checklist (severity tagged)

- **Custom plugins** (Breaking) — custom `RequestHandler` / `SearchComponent` Java plugins.
- **Cross-collection joins** (Breaking) — `{!join fromIndex=...}` not supported.
- **Trie field types** (Breaking) — `TrieIntField`, `TrieLongField`, `TrieFloatField`, `TrieDoubleField`.
- **Function queries** (Warning) — `recip`, `log`, `product`, `bf`; syntax differs significantly.
- **eDisMax `pf`/`pf2`/`pf3`/`mm`/`tie`** (Warning) — no direct equivalents; approximate and validate parity.
- **Dynamic fields** (Warning) — `dynamicField` patterns; rule syntax differs.
- **Nested / block join docs** (Warning) — `_childDocuments_`; query syntax completely different.
- **Spatial fields** (Warning) — `LatLonPointSpatialField`, `SpatialRecursivePrefixTreeFieldType`.
- **Date math syntax** (Warning) — `NOW-1DAY/DAY` vs `now-1d/d`.
- **Default query operator** (Warning) — verify `minimum_should_match` and `operator` match intended behavior.
- **Similarity / scoring** (Info) — both default to BM25 since Solr 7 / OpenSearch 1.0; parameter defaults differ.
- **ZooKeeper removed** (Info) — decommission after migration.

## What counts as a Breaking incompatibility

- A Solr feature used in production with no functional OpenSearch equivalent.
- A query that cannot be translated without changing result semantics.
- A field type that requires data transformation before indexing.
- Any plugin or custom handler that must be rebuilt before go-live.

**Reference:**
- `references/05-legacy-features.md` — DIH, BlockJoin, function queries with no direct equivalent.
- `references/05b-legacy-features-continued.md` — joins, Streaming Expressions, SpellCheck, MoreLikeThis, custom handlers, atomic updates, gap summary table.
- `references/06-feature-compatibility-matrix.md` — full ✅/⚠️/❌ matrix for quick lookup and effort scoping.
