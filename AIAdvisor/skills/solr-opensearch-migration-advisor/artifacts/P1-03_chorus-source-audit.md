# P1-03: Chorus Source Configuration Audit

**Project:** Enterprise Solr 8 (Chorus) to OpenSearch Migration
**Generated:** 2026-04-02
**Status:** ASSUMED — awaiting team confirmation
**Source:** Reconstructed from Chorus GitHub repo (querqy/chorus), adjusted for ~2023 Solr 8.x install

> **Every item marked `[ASSUMED]` needs confirmation or correction by the team.**
> Search this doc for `[ASSUMED]` to find all guesses. There are approximately 30.
>
> **Note:** The current Chorus repo (2026) runs Solr 9.1.1 with vector/embedding features.
> This audit assumes the ~2023 Solr 8 vintage, which predates those additions.

---

## 1. Cluster Topology

| Property | Value | Confidence |
|----------|-------|------------|
| Solr version | **8.x** (confirmed by Sean) | Known |
| Deployment mode | SolrCloud | `[ASSUMED]` from Chorus default |
| Solr nodes | 3 (solr1, solr2, solr3) | `[ASSUMED]` from Chorus docker-compose |
| ZooKeeper nodes | 3 (zoo1, zoo2, zoo3) | `[ASSUMED]` from Chorus docker-compose |
| Collection name | `ecommerce` | `[ASSUMED]` from Chorus default |
| Shard count | 2 | `[ASSUMED]` from Chorus default |
| Replication factor | 1 | `[ASSUMED]` from Chorus default |
| Document count | ~20K-50K (Icecat electronics) | `[ASSUMED]` — depends on which dataset load was used |
| Total index size | ~500MB-2GB | `[ASSUMED]` — typical for this dataset size |
| JVM heap per node | 512MB-1GB | `[ASSUMED]` from Chorus Docker defaults |

### Supporting Stack

| Service | Version | Port | Purpose |
|---------|---------|------|---------|
| Blacklight | Rails app | 4000 | E-commerce storefront UI |
| SMUI | ~3.x-4.x | 9000 | `[ASSUMED]` Querqy rule management UI |
| Quepid | ~6.x-7.x | 3000 | `[ASSUMED]` Relevance testing |
| MySQL | 8.x | 3306 | Backend for SMUI + Quepid |
| Keycloak | — | 9080 | `[ASSUMED]` Auth (JWT + Basic) |
| Prometheus | v2.32.x | 9090 | `[ASSUMED]` Metrics collection |
| Grafana | 7.5.x | 9091 | `[ASSUMED]` Dashboards |

---

## 2. Schema (managed-schema / schema.xml)

### Field Types

| Solr fieldType | Definition | OpenSearch equivalent | Migration notes |
|---|---|---|---|
| `text_stemmed_en` | StandardTokenizer → LowerCase → EnglishMinimalStem | Custom analyzer: `standard` tokenizer + `lowercase` + `stemmer` (light_english) | **Primary text type.** EnglishMinimalStem ≈ `light_english` stemmer in OS. Verify stemming parity. |
| `text_general` | StandardTokenizer → LowerCase | `text` with `standard` analyzer | Straightforward mapping |
| `textSpell` | StandardTokenizer → LowerCase → RemoveDuplicates | Custom analyzer for suggest | Used by spellcheck/suggest |
| `string` | StrField | `keyword` | Exact match, no analysis |
| `boolean` | BoolField | `boolean` | Direct mapping |
| `integer` / `float` / `long` / `double` | PointField variants with docValues | `integer` / `float` / `long` / `double` | Direct mapping |
| `date` | DatePointField | `date` (strict_date_optional_time) | Direct mapping |
| `random` | RandomSortField | Script-based sort in OS | `[ASSUMED]` — needs custom implementation if used |

`[ASSUMED]` The Solr 8 vintage would NOT have the `knn_vector_*` types present in the current (Solr 9) Chorus repo. Those are post-2023 additions.

### Explicit Fields

| Field | Type | Indexed | Stored | multiValued | Purpose |
|---|---|---|---|---|---|
| `id` | string | Y | Y | N | Unique key (required) |
| `name` | text_stemmed_en | Y | Y | N | Product name — primary search field |
| `title` | text_stemmed_en | Y | Y | N | Product title — primary search field |
| `ean` | string | Y | Y | Y | European Article Number (barcode) |
| `price` | integer | Y | Y | N | Product price `[ASSUMED: integer, not float]` |
| `short_description` | text_stemmed_en | Y | Y | N | Brief product description |
| `img_high` | string | N | Y | N | High-res image URL (stored only) |
| `img_low` | string | N | Y | N | Low-res image URL (stored only) |
| `img_500x500` | string | N | Y | N | Standard image URL (stored only) |
| `img_thumb` | string | N | Y | N | Thumbnail URL (stored only) |
| `date_released` | date | Y | Y | N | Product release date |
| `supplier` | text_general | Y | Y | N | Supplier/manufacturer name |
| `suggestions` | text_general | Y | Y | Y | Autocomplete target (copyField destination) |
| `search_attributes` | text_stemmed_en | Y | Y | Y | Catch-all for product attributes (copyField destination) |
| `name_stored` | string | Y (docValues) | Y | N | Sortable/facetable copy of name |
| `title_stored` | string | Y (docValues) | Y | N | Sortable/facetable copy of title |
| `brand_stored` | string | Y (docValues) | Y | N | Sortable/facetable copy of brand |
| `short_description_stored` | string | Y (docValues) | Y | N | Sortable copy of description |
| `product_type` | text_stemmed_en | Y | Y | N | Product category (searchable) |
| `brand` | text_general | Y | Y | N | Brand name (searchable) |
| `filter_brand` | string | Y | Y | N | Brand facet field |
| `filter_product_type` | string | Y | Y | N | Product type facet field |

### Dynamic Fields

| Pattern | Type | Purpose |
|---------|------|---------|
| `attr_t_*` | text_stemmed_en | Text product attributes (specs, features) |
| `attr_b_*` | boolean | Boolean product attributes |
| `attr_n_*` | float | Numeric product attributes |
| `filter_t*` | string | String facet fields (auto-generated from attr_t_*) |
| `random_*` | random | Random sort support |

`[ASSUMED]` These dynamic field patterns match the current Chorus repo. A 2023 install should be the same.

### copyField Directives

| Source | Destination | Purpose |
|--------|-------------|---------|
| `name` | `suggestions` | Autocomplete |
| `title` | `suggestions` | Autocomplete |
| `brand` | `suggestions` | Autocomplete |
| `short_description` | `suggestions` | Autocomplete |
| `name` | `name_stored` | Sortable/facetable copy |
| `title` | `title_stored` | Sortable/facetable copy |
| `brand` | `brand_stored` | Sortable/facetable copy |
| `short_description` | `short_description_stored` | Sortable/facetable copy |
| `supplier` | `brand` | `[ASSUMED]` Supplier treated as brand |
| `supplier` | `filter_brand` | `[ASSUMED]` Supplier used for brand facet |
| `attr_t_product_type` | `product_type` | Category searchable field |
| `attr_t_product_type` | `filter_product_type` | Category facet field |
| `attr_t*` | `filter_t*` | Dynamic: all text attrs → facet fields |
| `attr_t*` | `search_attributes` | Dynamic: all text attrs → catch-all searchable |

**Migration note:** `copy_to` in OpenSearch handles the simple cases. The dynamic copyField (`attr_t*` → `filter_t*`) will need `dynamic_templates` with `copy_to` — verify this works as expected.

---

## 3. Query Configuration (solrconfig.xml)

### Request Handlers

#### `/select` — Default search handler

```
[ASSUMED] Based on Chorus default configuration:

defType:    querqy    (NOT edismax — Querqy wraps eDisMax)
tie:        0.01
echoParams: all

qf:  id name title product_type short_description ean search_attributes
pf:  [ASSUMED] name^10 title^5
mm:  [ASSUMED] 2<75%

facet:       true
facet.field: filter_brand
facet.field: filter_product_type
facet.range: price
```

**Key point:** The `defType` is `querqy`, not `edismax`. Querqy's QParser wraps eDisMax and adds rewriter chain processing. All eDisMax params (`qf`, `pf`, `mm`, `bq`, `bf`) still work — Querqy adds to them, doesn't replace them.

#### `/blacklight` — Storefront search handler

```
[ASSUMED] Extends /select with:

defType:     edismax
spellcheck:  true
spellcheck.dictionary: title
appends:     visible_products filter set (price:* AND -img_500x500:"")
```

`[ASSUMED]` The Blacklight handler may use `edismax` directly (not `querqy`) for the storefront, with Querqy used in A/B testing via paramsets.

#### `/suggest` — Autocomplete

```
[ASSUMED] Based on Chorus config:

handler:    SearchHandler with SuggestComponent
suggester:  FuzzyLookupFactory
field:      suggestions
buildOnCommit: true
```

### ParamSets (Relevancy Algorithm Switching)

Chorus uses Solr's ParamSets to switch between relevancy algorithms at query time. This is a key architectural pattern:

| ParamSet | defType | Rewriters | Purpose |
|----------|---------|-----------|---------|
| `visible_products` | — | — | Base filter: `price:*` AND `-img_500x500:""` |
| `default_algo` | edismax | none | Vanilla eDisMax baseline |
| `mustmatchall_algo` | edismax | none | eDisMax with mm=100% |
| `querqy_algo` | querqy | `replace,common_rules,regex_screen_protectors` | **Production rules** |
| `querqy_algo_prelive` | querqy | `replace_prelive,common_rules_prelive,regex_screen_protectors` | **Staging rules** (SMUI prelive) |

`[ASSUMED]` The Solr 8 vintage would not have the vector embedding paramsets (`querqy_boost_by_img_emb`, etc.) present in the current repo.

**Migration note:** ParamSets is a Solr-specific feature. In OpenSearch, equivalent behavior can be achieved with search templates or application-layer config switching.

### Security

| Setting | Value |
|---------|-------|
| Auth model | JWT (Keycloak) + Basic Auth |
| Basic auth credentials | `solr`/`SolrRocks`, `admin`/password |
| Anonymous access | Read-only on `/select` (GET/POST) |
| Admin operations | Require `admin` or `solr-admin` role |

`[ASSUMED]` from Chorus defaults. **Change these credentials if this is anything other than a local demo.**

---

## 4. Querqy Configuration

### Plugin Version

| Component | Version | Notes |
|-----------|---------|-------|
| Querqy Solr plugin | `[ASSUMED]` querqy-solr-5.x (lucene8xx variant) | Must match Solr 8 Lucene version |
| Querqy QParser | `querqy.solr.QuerqyDismaxQParserPlugin` | Registered as defType=querqy |
| Querqy Query Component | `querqy.solr.QuerqyQueryComponent` | Replaces default query component |
| Querqy Rewriter Handler | `/querqy/rewriter` | REST endpoint for rule management |
| skipUnknownRewriters | true | Graceful degradation if a rewriter is missing |

### Active Rewriters

| Rewriter | Type | Purpose | Rule source |
|----------|------|---------|-------------|
| `common_rules` | CommonRulesRewriter | Synonyms, boosts, filters, deletes | SMUI → `rules.txt` deployed to ZooKeeper |
| `common_rules_prelive` | CommonRulesRewriter | Staging/preview rules | SMUI prelive → `rules.txt` |
| `replace` | ReplaceRewriter | Query normalization, spelling correction | SMUI → `replace-rules.txt` deployed to ZK |
| `replace_prelive` | ReplaceRewriter | Staging replacements | SMUI prelive → `replace-rules.txt` |
| `regex_screen_protectors` | `[ASSUMED]` RegexFilterRewriter | `[ASSUMED]` Filters screen protector results for non-screen-protector queries | Custom rules file |

`[ASSUMED]` The Solr 8 vintage would not have the embedding rewriters (`embtxt`, `embimg`, etc.).

### Rewriter Chain Order

**Production:** `replace` → `common_rules` → `regex_screen_protectors`
**Prelive:** `replace_prelive` → `common_rules_prelive` → `regex_screen_protectors`

**Chain order matters:** Replace runs first (normalizes the query text), then common_rules (applies synonyms/boosts to the normalized query), then regex filters.

### Querqy Rule Types in Use

`[ASSUMED]` Based on typical Chorus demo usage. Confirm with actual `rules.txt` export:

**CommonRules (synonyms, boosts, filters, deletes):**
```
# Example: synonym + boost
notebook =>
  SYNONYM: laptop
  UP(100): product_type:laptop

# Example: filter
cheap laptop =>
  FILTER: * price:[* TO 500]

# Example: downboost
accessories =>
  DOWN(50): product_type:accessory

# Example: delete (remove noise term from query)
cheap =>
  DELETE
```

**Replace rules (query normalization):**
```
# Example: spelling correction
samung => samsung
iphon => iphone

# Example: abbreviation expansion  
tv => television
```

### Migration Impact

| Querqy feature | OpenSearch path | Risk |
|---|---|---|
| CommonRulesRewriter | `querqy-opensearch` plugin supports this | **Verify version compatibility** |
| ReplaceRewriter | `querqy-opensearch` plugin supports this | **Verify version compatibility** |
| Regex rewriters | `[ASSUMED]` supported in querqy-opensearch | Verify |
| Rule deployment to ZK | Must change — OS has no ZooKeeper. Rules deploy via API or file. | Medium effort |
| ParamSet switching | No OS equivalent — implement in app layer or search templates | Medium effort |
| Info logging / response sink | `[ASSUMED]` supported in querqy-opensearch | Verify |

**Critical path:** The `querqy-opensearch` plugin must support your target OpenSearch version. Check https://github.com/querqy/querqy-opensearch for the version compatibility matrix.

---

## 5. SMUI Configuration

### Version and Setup

| Property | Value | Confidence |
|----------|-------|------------|
| SMUI version | `[ASSUMED]` 3.x-4.x (Solr 8 era) | Estimated |
| Backend database | MySQL 8.x | `[ASSUMED]` from Chorus default |
| Target collection | `ecommerce` | `[ASSUMED]` |
| Deploy mechanism | `smui2solrcloud.sh` script → ZooKeeper configset | `[ASSUMED]` from Chorus default |
| Deploy targets | `rules.txt` → `/configs/ecommerce/rules.txt` | `[ASSUMED]` |
| | `replace-rules.txt` → `/configs/ecommerce/replace-rules.txt` | `[ASSUMED]` |

### SMUI Features in Use

| Feature | Enabled | Notes |
|---------|---------|-------|
| Spelling / Replace rules | `[ASSUMED]` Yes | Managed as ReplaceRewriter rules |
| Rule ID logging | `[ASSUMED]` Yes | For tracking which rules fire |
| Event history | `[ASSUMED]` Yes | Audit trail of rule changes |
| Rule tagging | `[ASSUMED]` Yes | With predefined tags |
| Prelive / staging rules | `[ASSUMED]` Yes | Separate deploy for preview |
| Suggested fields | `[ASSUMED]` product_type, title, brand | Fields SMUI suggests for rule targets |

### Estimated Rule Count

`[ASSUMED]` Based on a ~3-year-old Chorus install that has been actively used:

| Rule type | Estimated count | Notes |
|-----------|----------------|-------|
| Synonym rules | 30-100 | `[ASSUMED]` Product category and brand synonyms |
| Boost/UP rules | 20-50 | `[ASSUMED]` Brand and category boosts |
| Downboost/DOWN rules | 10-20 | `[ASSUMED]` Accessory demotions, irrelevant results |
| Filter rules | 5-15 | `[ASSUMED]` Price-based and category filters |
| Delete rules | 5-10 | `[ASSUMED]` Noise word removal |
| Replace/spelling rules | 20-50 | `[ASSUMED]` Common misspellings and abbreviations |
| **Total** | **~90-245** | `[ASSUMED]` — could be much higher if heavily used |

**To get exact count:** Export from SMUI or count lines in `rules.txt` and `replace-rules.txt` in ZooKeeper:
```bash
docker exec chorus-solr1-1 bin/solr zk cat /configs/ecommerce/rules.txt -z zoo1:2181
docker exec chorus-solr1-1 bin/solr zk cat /configs/ecommerce/replace-rules.txt -z zoo1:2181
```

### SMUI Migration Path

| Option | Description | Effort | Risk |
|--------|-------------|--------|------|
| **A: SMUI on OpenSearch** | SMUI deploys rules to OS via querqy-opensearch plugin | Medium | SMUI's OS deployment support needs verification |
| **B: Export rules, manual management** | Export all rules from SMUI MySQL, manage as files | Low | Loses the UI workflow, governance degrades |
| **C: Replace with OpenSearch Dashboards plugin** | Build or adopt OS-native rule management | High | No mature equivalent exists today |

**Recommendation:** Try Option A first. SMUI's deploy script is the integration point — if it can target OpenSearch's Querqy rewriter API instead of ZooKeeper, the rest of the workflow survives.

---

## 6. Dataset: Icecat Product Catalog

| Property | Value |
|----------|-------|
| Source | Icecat Open Content License product data |
| Product count | `[ASSUMED]` ~20K-50K loaded (up to 150K available) |
| Product types | Electronics: TVs, laptops, cameras, phones, tablets, accessories |
| Key fields | name, title, brand, price, descriptions, EAN codes, images, product attributes |
| Prices | Available for ~19K products (extracted via UPC/EAN lookup) |
| Images | Products without 500x500 images filtered out in Chorus default load |
| Human judgments | 125 e-commerce queries rated by 3 judges (`Broad_Query_Set_rated.csv`) |

**Migration note:** The existing 125-query judgment set is a head start for relevance comparison. Load these into Quepid (which already supports OpenSearch) to measure Solr→OS relevance delta.

---

## 7. Complexity Scorecard

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Schema complexity | **2/5** | Standard fields, clean dynamic patterns, custom but straightforward analyzer chains |
| Query complexity | **3/5** | eDisMax via Querqy is well-understood, but ParamSet switching and rewriter chains add migration surface |
| Data movement complexity | **1/5** | Small dataset, full rebuild from source trivial, no freshness constraints |
| Application complexity | **3/5** | Blacklight UI, SMUI, Quepid, Querqy — four integration points, not just one |
| Operational complexity | **1/5** | Docker Compose, local dev, no production SLA |
| Organizational readiness | **2/5** | 5-person team with clear roles, demo exercise (not production pressure) |

**Overall: 2-3/5 — moderate complexity, driven by the Querqy/SMUI toolchain, not by the data or schema.**

---

## 8. Identified Incompatibilities

| ID | Category | Issue | Severity | Recommendation |
|---|---|---|---|---|
| CHR-01 | Query | `defType=querqy` has no native OS equivalent | **High** | Requires `querqy-opensearch` plugin. Version compat is critical path. |
| CHR-02 | Query | ParamSets for algorithm switching | **Medium** | Implement via search templates or app-layer config. |
| CHR-03 | Ops | ZooKeeper-based rule deployment (SMUI → ZK) | **Medium** | SMUI deploy script must target OS Querqy API instead. |
| CHR-04 | Schema | `textSpell` type + FuzzyLookup suggester | **Medium** | OpenSearch suggest API differs. Needs redesign. |
| CHR-05 | Schema | Dynamic copyField (`attr_t*` → `filter_t*`) | **Low** | Test `dynamic_templates` with `copy_to` in OS. |
| CHR-06 | Schema | `RandomSortField` | **Low** | Use `function_score` with `random_score` in OS. |
| CHR-07 | Scoring | TF-IDF (Solr 8 default) → BM25 (OS default) | **High** | Baseline with Quepid judgment set before migration. Expect 30-40% top-10 shift. |
| CHR-08 | Tooling | SMUI OpenSearch compatibility | **High** | Verify deploy mechanism works with OS. Fallback: export rules, manage as files. |
| CHR-09 | Query | Regex rewriter (`regex_screen_protectors`) | **Medium** | Verify querqy-opensearch supports regex rewriters. |
| CHR-10 | Auth | JWT (Keycloak) + Basic Auth → OS auth model | **Medium** | Map to OS FGAC or IAM. Sys admin to investigate. |

---

## 9. Recommended Verification Steps

Assign these to your team to confirm or correct this audit:

### Solr Expert
- [ ] Confirm Solr version: `curl http://localhost:8983/solr/admin/info/system?wt=json | jq '.lucene["solr-spec-version"]'`
- [ ] Export schema: `curl http://localhost:8983/solr/ecommerce/schema?wt=json > schema-export.json`
- [ ] Export solrconfig request handlers: `curl http://localhost:8983/solr/ecommerce/config/requestHandler?wt=json`
- [ ] Export rules from ZK: `docker exec <solr-container> bin/solr zk cat /configs/ecommerce/rules.txt -z zoo1:2181`
- [ ] Export replace rules: `docker exec <solr-container> bin/solr zk cat /configs/ecommerce/replace-rules.txt -z zoo1:2181`
- [ ] Count documents: `curl 'http://localhost:8983/solr/ecommerce/select?q=*:*&rows=0&wt=json' | jq '.response.numFound'`

### OS Expert
- [ ] Check querqy-opensearch version matrix: https://github.com/querqy/querqy-opensearch
- [ ] Identify target OpenSearch version and confirm Querqy plugin availability
- [ ] Test SMUI deploy script against OS Querqy rewriter API

### Sys/Network Admin
- [ ] Document current Docker Compose topology (confirm node counts, ports, versions)
- [ ] Capture current resource usage (memory, disk, CPU per container)
- [ ] Assess target platform (AWS managed vs. local Docker for initial testing)

### Tester
- [ ] Locate judgment set: `Broad_Query_Set_rated.csv` (125 queries, 3 judges)
- [ ] Load into Quepid against current Solr to establish baseline scores
- [ ] Document current Quepid configuration (which scorer, which metrics)
