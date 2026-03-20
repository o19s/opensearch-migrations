# Solr-to-OpenSearch: The Consultant’s Crosswalk

**Scope:** A bridge document for seasoned Solr/Fusion consultants transitioning to the OpenSearch/Elasticsearch ecosystem.
**Audience:** Solr/Fusion veterans who know the "why" of search but need the "what" of OpenSearch.

---

## 1. The Rosetta Stone: Core Concepts

| Solr / Fusion Concept | OpenSearch / Elastic Equivalent | Notes for the Solr Consultant |
|:---|:---|:---|
| **Collection** | **Index** | OS indices are more "shard-aware" than Solr collections. |
| **SolrCloud Core** | **Shard** | Don't obsess over shards; OS handles rebalancing better than ZK. |
| **`schema.xml`** | **Mappings API** | No XML. Everything is dynamic JSON. Use the Mappings API. |
| **`solrconfig.xml`** | **Index Settings / ISM** | Settings (refresh, etc.) are API-based. ISM handles life-cycle. |
| **ZooKeeper** | **Cluster State / Raft** | OS manages state internally (no separate ZK). Less operational baggage. |
| **`q=*:*`** | `match_all` | The standard "give me everything" query. |
| **`fl=field1,field2`** | `_source: ["f1", "f2"]` | You filter which fields are returned via `_source` masking. |
| **`fq=field:value`** | `filter` (in `bool` query) | Filters are cached and do *not* affect relevance scores. |
| **DisMax / eDisMax** | `multi_match` | The standard way to search across multiple fields with boosts. |
| **DataImportHandler (DIH)** | **Logstash / Data Prepper** | Solr handled data loading internally; OS expects an external pipeline. |

---

## 2. Common Gotchas: The "You Should Know" List

| Gotcha | Why it bites Solr vets | Source for Deep Dive |
|:---|:---|:---|
| **BM25 vs TF-IDF** | Scores are **not** 1:1. Clients will panic. | `01-sources/community-insights/relevance-scoring-differences.md` |
| **Atomic Updates** | OS uses "Optimistic Concurrency Control" (`_seq_no`). Partial updates require reading the doc first. | `01-sources/opensearch-migration/common-pitfalls.md` |
| **Segment Merging** | OS is "Near Real-Time" (NRT) by default (1s refresh). Solr was often "hard commit" focused. | `01-sources/opensearch-best-practices/indexing-speed-tuning.md` |
| **Deep Paging** | `start=1000000` kills OS nodes. Use `search_after` (cursor-based pagination). | `01-sources/opensearch-fundamentals/ingest-data.md` |
| **Dynamic Fields** | Solr allowed `*_s` wildcards. OS has "Dynamic Templates" which are more restrictive. | `01-sources/opensearch-fundamentals/mappings.md` |

---

## 3. The "Sean-to-OS" Quick-Tips for Relevance

1.  **Stop thinking about `fieldCache`**: You don't need to warm up memory like you did in Solr. OS uses `doc_values` (on-disk, off-heap) by default for sorting/faceting. It’s significantly more resilient.
2.  **Analyzers are "Immutable"**: You cannot change an analyzer on an existing index. If you mess up your `text_general` chain, you **must** reindex. Use `Index Templates` to enforce consistency.
3.  **Governance is now API-driven**: In Solr, you edited a file on the server. In OS, you `PUT` the settings to the cluster. **Build a script for every change.** Never edit "live" without a backup script.
4.  **Vectors are First-Class Citizens**: If you’ve dabbled in Solr Vector Search, you’ll find OS is vastly more mature here (k-NN search is a native index type). If your client is asking for AI/LLM, this is your killer feature.

---

## 4. Where to Find More Info

*   **Query Translation:** `01-sources/opensearch-migration/query-syntax-mapping.md`
*   **Field Mapping:** `01-sources/opensearch-migration/schema-field-type-mapping.md`
*   **The "Big One":** [AWS Prescriptive Guidance: Solr to OpenSearch](https://docs.aws.amazon.com/prescriptive-guidance/latest/migration-apache-solr-amazon-opensearch-service/)
*   **Deep Dives:** The `01-sources/community-insights/` folder has the best "war stories" for practitioners.
