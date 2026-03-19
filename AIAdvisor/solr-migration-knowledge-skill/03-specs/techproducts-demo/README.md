# Solr → OpenSearch Migration: Techproducts Demo Collection

## What This Is

This is a complete, worked **migration specification** for the Apache Solr **techproducts demo collection** to **AWS OpenSearch Service 2.x**. It demonstrates the artifacts and outputs that a migration advisor skill produces — concrete enough to execute, specific enough to teach.

The techproducts collection is ideal for learning migration methodology because it:
- Uses real Solr patterns (copyFields, dynamic fields, facets, geo search, text analysis)
- Is small enough to iterate quickly (7 sample products)
- Covers core search features (keyword search, filtering, faceting, geo, bulk indexing)
- Is **simple enough to learn from** but not so simple as to be unrealistic

This is **not production-ready** — it omits document parsing (Tika fields), payload scoring, and operational complexity that real migrations handle. That's intentional: it's a teaching example.

## How to Use This

1. **Start with `steering/` docs** — understand the scope, tech stack, and project structure before implementation
2. **Review `requirements.md`** — EARS-format user stories and acceptance criteria
3. **Study `design.md`** — the technical heart: mapping, query translation, indexing architecture
4. **Execute `tasks.md`** — an ordered checklist of implementation phases
5. **Build the Spring Boot app** — follow the structure in `steering/structure.md`

This mirrors the actual flow: **Scope → Requirements → Design → Build → Test**.

## File Structure

```
techproducts-demo/
├── README.md (this file)
├── steering/
│   ├── product.md       # What we're building (scope, success criteria)
│   ├── tech.md          # Stack decisions and open questions
│   └── structure.md     # Spring Boot/Kotlin project layout
├── requirements.md      # EARS user stories with acceptance criteria
├── design.md            # Mappings, queries, architecture
└── tasks.md             # Implementation checklist by phase
```

## Migration Complexity Score

**Techproducts: 2/5 (Low Complexity)**

This collection is a good starting point because:
- ✅ No nested documents
- ✅ No CDCR or replication rules
- ✅ No atomic updates
- ✅ Standard analyzers only (no custom plugins)
- ✅ Small data volume (~1 MB)
- ✅ No streaming expressions or complex post-query logic

Real migrations often score 4-5/5 and add:
- Complex nested/hierarchical structures
- Custom analyzers or linguistically-specialized filters
- Atomic updates in critical paths
- Multi-shard rebalancing concerns
- Cross-datacenter replication
- Document parsing and enrichment

**What to expect:**
- Setup (AWS OpenSearch, mappings): **2-3 days**
- Indexing pipeline: **2-3 days**
- Query layer + testing: **3-5 days**
- **Total**: ~1 week for a small team

## Opening in Kiro

If you're using **Kiro** (the migration advisor skill framework):

1. Export this spec to your skill's working directory:
   ```bash
   cp -r techproducts-demo ~/kiro-skills/solr-to-opensearch-migration/specs/
   ```

2. Reference from your skill:
   ```markdown
   See: [Techproducts Worked Example](../specs/techproducts-demo/design.md)
   ```

3. Use `design.md` mappings as templates for new migrations

## Key Outputs for Your Own Migration

When you use this skill on a *different* Solr collection:

- **Replace field names** with your schema
- **Adjust complexity score** based on your features (nested? atomic updates? CDCR?)
- **Adapt the mapping template** in design.md
- **Extend requirements.md** for your customer workflows
- **Expand tasks.md** for your data volume and team size

## Next Steps

- To understand the Solr source: see schema at top of this README file
- To see the target AWS OpenSearch mapping: read `design.md` → "Index Mapping"
- To understand queries: read `design.md` → "Query Architecture"
- To start building: follow `tasks.md` Phase 1

---

**Generated:** 2026-03-17
**Methodology:** OSC Search Engine Migration Consulting Playbook
**Author:** Solr→OpenSearch Migration Advisor Skill
