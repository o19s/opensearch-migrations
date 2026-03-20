# Endeca Architecture Audit
**Scope:** Identifying and inventorying components of an Oracle Commerce Guided Search (Endeca) deployment for migration planning.
**Audience:** Consultants and architects auditing legacy Endeca systems.
**Last reviewed:** 2026-03-19 | **Reviewer:** Gemini CLI

---

## Key Judgements

- **The Pipeline is the Source of Truth:** Do not trust the Dgraph's `/admin/schema` alone. You must find the `.epx` (Forge) and `.xml` (CAS) configuration files. These contain the logic (e.g., Perl scripts, JavaScript) that transforms raw data into Endeca records.
- **Dimension Hierarchy is the Risk:** Endeca allows deeply nested, tree-like dimensions. OpenSearch facets are naturally flat. Auditing the "Max Depth" of every dimension is critical to avoid broken navigation in the target system.
- **Experience Manager (XMGR) is the "Shadow CMS":** Many Endeca deployments use XMGR for full page layouts, not just search results. You must audit the "Content Zones" to determine if you're migrating a search engine or a hidden web-layer.
- **Record Store vs. MDEX:** CAS Record Stores are often used as a staging area. Distinguish between the "Full Crawl" (CAS) and the "Dgraph State" (MDEX). Migration should target the Record Store for its cleaner data format.
- **The "FirstMatch" Legacy:** Endeca defaults to a "FirstMatch" relevance strategy (matching on the first field that hits). OpenSearch uses "BM25" (summed scores across fields). Auditing the `RelRank` strategies in Endeca is vital for managing relevance expectations.

---

## Audit Checklist (The "Endeca Inventory")

### 1. Ingest & Pipeline
- [ ] Locate the `pipeline.epx` (Forge) file.
- [ ] Identify all **Record Adapters** (JDBC, XML, Delimited).
- [ ] List all **Forge Manipulators** (Perl/Java code that cleans data).
- [ ] Check for **CAS (Content Acquisition System)** crawls and their frequency.

### 2. Schema (Dimensions & Properties)
- [ ] Export the `Dimensions.xml` and `Properties.xml`.
- [ ] Identify **Multi-Select OR** dimensions (these require special logic in OpenSearch).
- [ ] Identify **Hierarchical Dimensions** (and their max depth).
- [ ] Map **Property Types** (String, Integer, Floating Point, Alpha-Numeric).

### 3. Query & Relevance
- [ ] Export the **Thesaurus** (Synonyms) and **Stopwords** list.
- [ ] Document all **Relevance Ranking Strategies** (e.g., `Static`, `Frequency`, `Interp`, `First`).
- [ ] List all **Business Rules** (Spotlights, Boost/Bury) in Experience Manager.

### 4. Hardware & Scale
- [ ] Count the number of **Dgraph** instances (MDEX).
- [ ] Note the **Index Size** (RAM vs. Disk). Endeca is RAM-heavy; OpenSearch is Disk-heavy.

---

## Decision Heuristics

| If the audit shows... | Then... |
|-----------------------|---------|
| Deeply nested Dimension trees (>3 levels) | You must implement a "Path-Based" mapping or "Flattening" logic in OpenSearch. |
| Custom Perl Manipulators in Forge | Budget for a significant rewrite of the ETL logic in Python/Spark. |
| Massive XMGR Content Zones | The project is a "Site Re-architecture," not just a "Search Migration." |
| "FirstMatch" is the only RelRank strategy | OpenSearch BM25 results will feel "fuzzy" to stakeholders; tune `minimum_should_match` early. |

---

## Common Mistakes

- **Ignoring the "Auto-Correct" (Did You Mean):** Endeca's "Spelling Correction" and "Dy-M" (Did You Mean) are often heavily customized via XML. Don't assume OpenSearch's default suggesters will match this behavior without tuning.
- **Underestimating "Multi-Select OR":** In Endeca, this is a checkbox in the Workbench. In OpenSearch, it requires a complex "Filter context" vs. "Query context" redesign.
- **Missing the "Precedence Rules":** Endeca can hide/show dimensions based on other selections. These rules are often buried in the MDEX config and are hard to replicate in standard OpenSearch facets.
