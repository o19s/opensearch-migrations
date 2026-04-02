# Implementation Tasks: `hello` Migration

[ASSUMED: team of 2 engineers (1 search/backend, 1 DevOps/platform); adjust estimates accordingly]

## Phase Overview

```
Phase 1: Audit & Provision     (3–5 days)   ← DO THIS FIRST
Phase 2: Build & Validate      (5–8 days)   ← offline, no production impact
Phase 3: Dual-Write & Shadow   (10–15 days) ← production dual-write begins
Phase 4: Cutover               (2–3 days)   ← traffic shift
Phase 5: Cleanup               (3–5 days)   ← decommission Solr
```

Total estimated duration: **5–7 weeks** [ASSUMED: moderate complexity, part-time migration team]

---

## Phase 1: Audit & Provision

**Goal:** Validate assumptions in this spec, provision the AWS target, establish baseline.

### TASK-101: Resolve all high-risk assumptions

**Owner:** Search Engineer
**Effort:** 0.5 days
**Priority:** Blocker — do not proceed to Phase 2 until done

Run these checks against the actual Solr instance:

```bash
# A12: Confirm no nested/parent-child documents
grep -n "childFilter\|BlockJoin\|toParent\|toChild\|[Nn]ested" solrconfig.xml schema.xml

# A11: Check for custom analyzer plugins
grep -n 'class=' schema.xml | grep -v 'solr\.TextField\|solr\.StrField\|solr\.IntPointField\|solr\.LongPointField\|solr\.FloatPointField\|solr\.DoublePointField\|solr\.DatePointField\|solr\.BoolField\|solr\.LatLonPointSpatialField'

# A14: Check for streaming expressions
grep -n "StreamHandler\|/stream\|StreamingRequestHandler" solrconfig.xml

# A20: Check for Data Import Handler
grep -n "DataImportHandler\|/dataimport" solrconfig.xml

# A16: Check for atomic update patterns in application code
grep -rn '"set"\s*:\|"add"\s*:\|"inc"\s*:\|"remove"\s*:' src/

# Get actual document count and index size
curl "http://solr:8983/solr/hello/select?q=*:*&rows=0&wt=json" | jq '.response.numFound'
```

Update README.md assumptions table with actual findings. If A12, A11, or A14 are wrong,
**stop and consult** — this spec needs redesign for those sections.

---

### TASK-102: Capture actual schema

**Owner:** Search Engineer
**Effort:** 0.5 days

```bash
# Export live schema via Schema API
curl "http://solr:8983/solr/hello/schema?wt=json" > schema-export.json

# Or copy schema.xml directly
scp solr-host:/var/solr/data/hello/conf/schema.xml ./schema.xml
```

Compare exported schema against the assumed schema in `design.md`. Update:
- `design.md` → "Assumed Solr Schema" section with real field names
- `design.md` → "Index Mapping" JSON with real field names
- `HelloDocument.kt` data class fields

---

### TASK-103: Provision AWS OpenSearch Service cluster

**Owner:** DevOps
**Effort:** 1 day

```hcl
# Terraform outline [ASSUMED: Terraform is the IaC tool]
resource "aws_opensearch_domain" "hello" {
  domain_name    = "hello-search"
  engine_version = "OpenSearch_2.17"   # [ASSUMED: latest supported]

  cluster_config {
    instance_type          = "r6g.large.search"   # [ASSUMED]
    instance_count         = 2
    zone_awareness_enabled = true
    zone_awareness_config {
      availability_zone_count = 2                  # [ASSUMED: 2-AZ]
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 100    # GB per node [ASSUMED: ~3× 500MB source]
  }

  encrypt_at_rest      { enabled = true }
  node_to_node_encryption { enabled = true }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  access_policies = data.aws_iam_policy_document.opensearch_access.json
}
```

Checklist:
- [ ] Cluster created and status Green
- [ ] VPC endpoint configured (no public access)
- [ ] IAM role for application created with `es:ESHttp*` permissions
- [ ] Automated snapshots enabled (S3 bucket created)
- [ ] `_cat/nodes?v` shows 2 nodes, both healthy

---

### TASK-104: Create OpenSearch index with mapping

**Owner:** Search Engineer
**Effort:** 0.5 days

After TASK-102 (real schema) and TASK-103 (cluster up):

```bash
# Create index with mapping from design.md (updated with real fields)
curl -X PUT "https://<endpoint>/hello" \
  -H "Content-Type: application/json" \
  --aws-sigv4 "aws:amz:us-east-1:es" \
  -d @src/main/resources/opensearch/hello-mapping.json

# Verify
curl "https://<endpoint>/hello/_mapping" | jq '.hello.mappings.properties | keys'
```

**Pass criteria:** All field names from `schema.xml` appear in `_mapping` output.

---

### TASK-105: Establish Solr relevance baseline

**Owner:** Search Engineer
**Effort:** 1 day

Using Quepid or a manual comparison script:

1. Select 20 queries from Solr query logs [ASSUMED: logs available — if not, define manually]
2. For each query, capture top-10 Solr results (doc IDs + scores)
3. Have a subject-matter expert rate results (1/3/5 relevance scale)
4. Calculate nDCG@10 as baseline target
5. Store judgment set in `test/resources/judgment-set.json`

This baseline cannot be skipped. You cannot validate parity without it.

---

## Phase 2: Build & Validate

**Goal:** Build the application layer and validate mappings + queries offline (no production impact).

### TASK-201: Implement Spring Boot project skeleton

**Owner:** Backend Developer
**Effort:** 1 day

Create project from `steering/structure.md` layout:
- [ ] `build.gradle.kts` with dependencies
- [ ] `OpenSearchConfig.kt` with SigV4 client
- [ ] `HelloDocument.kt` data class (real fields from TASK-102)
- [ ] `application.yml` with dev/prod profiles
- [ ] TestContainers setup for integration tests

---

### TASK-202: Implement HelloIndexService

**Owner:** Backend Developer
**Effort:** 1 day

- [ ] `index(doc: HelloDocument)` — single document index
- [ ] `bulkIndex(docs: List<HelloDocument>)` — bulk API, batches of 500
- [ ] Integration test: index 5 docs, GET by ID, verify fields match

---

### TASK-203: Implement HelloSearchService (query layer)

**Owner:** Search Engineer
**Effort:** 2 days

Implement all 8 query patterns from `design.md`:
- [ ] Q1: Basic keyword search (multi_match)
- [ ] Q2: Category filter
- [ ] Q3: Keyword + filter combined
- [ ] Q4: Date range filter
- [ ] Q5: Category facets (terms aggregation)
- [ ] Q6: Combined production query
- [ ] Q7: Sort by date
- [ ] Q8: Deep pagination guard (400 if from+size > 10K)

Unit tests for each query: assert the generated JSON matches expected Query DSL.

---

### TASK-204: Validate schema fidelity

**Owner:** Search Engineer
**Effort:** 0.5 days

Index all 20 sample documents from `test/resources/sample-docs.json`.
For each document:
- [ ] Retrieve by ID
- [ ] Verify all fields are stored and returned correctly
- [ ] Verify `_text_` catch-all field is populated (search `_text_:<term>` and find docs)
- [ ] Verify `category` facet returns correct counts

**Pass criteria:** FR-6 acceptance criteria met.

---

### TASK-205: Offline relevance comparison

**Owner:** Search Engineer
**Effort:** 2 days

Run the 20 queries from the judgment set (TASK-105) against OpenSearch:
1. Index representative data subset into OpenSearch (minimum 10% of production volume)
2. Execute all 20 judgment-set queries
3. Calculate nDCG@10 for OpenSearch
4. Compare against Solr baseline
5. Document any queries with significant ranking differences

**Pass criteria:** FR-7 — ≥ 90% of queries have nDCG@10 within 10% of Solr baseline.
If below threshold: investigate top-3 failing queries, tune field weights or `minimum_should_match`.

---

### TASK-206: Implement MigrationReindexService

**Owner:** Backend Developer
**Effort:** 1 day

Implement cursor-based full reindex from `design.md` → "Bulk Reindex Strategy".
- [ ] Cursor-mark pagination from SolrJ
- [ ] Batch size 500, bulk API
- [ ] Disable/re-enable `refresh_interval` around bulk load
- [ ] Progress logging every 10K documents
- [ ] Dry-run mode (validate doc count without actual indexing)

---

## Phase 3: Dual-Write & Shadow Traffic

**Goal:** Run OpenSearch alongside Solr in production; validate at real traffic scale.

### TASK-301: Deploy DualWriteIndexService

**Owner:** Backend Developer + DevOps
**Effort:** 1 day

- [ ] Implement `DualWriteIndexService` from `steering/structure.md`
- [ ] Deploy with `migration.dual-write.enabled=false` (dormant)
- [ ] Smoke test: flip to `true` in staging, index one document, verify in both Solr + OpenSearch
- [ ] Confirm rollback: flip back to `false`, verify Solr continues working

---

### TASK-302: Full production reindex

**Owner:** Search Engineer + DevOps
**Effort:** 1 day (+ execution time)

Run `MigrationReindexService.reindexAll()` against production Solr.
Expected duration: ~100K docs ÷ 500 docs/sec = ~3 minutes [ASSUMED: adjust for actual volume]

- [ ] Run during low-traffic window [ASSUMED: off-peak hours]
- [ ] Monitor disk usage on OpenSearch cluster during reindex
- [ ] Verify final doc count matches Solr (`numFound` vs `_cat/count`)
- [ ] Verify index health is Green after reindex

---

### TASK-303: Enable dual-write in production

**Owner:** DevOps
**Effort:** 0.5 days

- [ ] Flip `migration.dual-write.enabled=true` in production config
- [ ] Monitor for 1 hour: error rate, latency, OpenSearch doc count growing with Solr
- [ ] Confirm OpenSearch doc count matches Solr after 24 hours

---

### TASK-304: Shadow traffic comparison (3 weeks)

**Owner:** Search Engineer
**Effort:** 3 weeks (monitoring, not active work)

[ASSUMED: 3-week shadow traffic window — adjust based on traffic volume and confidence]

Set up shadow read: route 5% of read traffic to OpenSearch, log both result sets.
Compare result sets daily:
- [ ] Week 1: 5% shadow — fix any mapping/query issues found
- [ ] Week 2: 25% shadow — spot-check 50 random queries per day
- [ ] Week 3: 50% shadow — final parity check against judgment set

**Go/no-go gate before Phase 4:**
- [ ] ≥ 90% of judgment-set queries pass parity check
- [ ] P99 search latency ≤ target from tech.md
- [ ] Zero data consistency errors (doc missing from OpenSearch but present in Solr)
- [ ] OpenSearch cluster health is Green (not Yellow or Red)

---

## Phase 4: Cutover

**Goal:** Shift all read traffic to OpenSearch; keep Solr warm for rollback.

### TASK-401: Gradual traffic cutover

**Owner:** DevOps + Search Engineer
**Effort:** 2–3 days

Execute in stages, with 30-minute monitoring windows between each:

```
migration.read-target=split:5    → monitor 30 min
migration.read-target=split:25   → monitor 30 min
migration.read-target=split:50   → monitor 60 min
migration.read-target=split:100  → full cutover → monitor 2 hours
```

**Abort criteria (roll back to Solr immediately if):**
- P99 latency exceeds 2× baseline
- Error rate > 0.5%
- Any cluster health Yellow for > 5 minutes

---

### TASK-402: Post-cutover validation

**Owner:** Search Engineer
**Effort:** 0.5 days

- [ ] Run full judgment set against live OpenSearch — confirm parity still holds
- [ ] Verify monitoring alerts are configured and firing correctly (test by injecting bad query)
- [ ] Confirm S3 snapshot completed successfully post-cutover
- [ ] Product owner sign-off: search quality acceptable

---

## Phase 5: Cleanup

**Goal:** Decommission Solr after 30-day rollback window. [ASSUMED: 30-day window]

### TASK-501: Remove dual-write code

**Owner:** Backend Developer
**Effort:** 1 day (after 30 days post-cutover)

- [ ] Delete `DualWriteIndexService.kt`
- [ ] Delete Solr client dependency from `build.gradle.kts`
- [ ] Delete `migration.dual-write.*` config keys
- [ ] Delete `migration.read-target` feature flag code

---

### TASK-502: Decommission Solr

**Owner:** DevOps
**Effort:** 1 day

- [ ] Final snapshot of Solr collection (archival)
- [ ] Stop Solr service
- [ ] Stop ZooKeeper ensemble
- [ ] Confirm no application traffic is hitting old Solr endpoint (check access logs)
- [ ] Terminate EC2 instances (or container) — **irreversible, confirm with team**

---

### TASK-503: Documentation and handoff

**Owner:** Search Engineer
**Effort:** 1 day

- [ ] Update runbook: remove Solr procedures, add OpenSearch operational notes
- [ ] Document ISM policy (index lifecycle if using rolling indices)
- [ ] Document how to add new fields (update mapping + `HelloDocument.kt`)
- [ ] Update monitoring dashboard: remove Solr panels, confirm OpenSearch panels complete

---

## Task Summary

| Task | Phase | Owner | Effort | Blocker? |
|------|-------|-------|--------|----------|
| TASK-101: Resolve assumptions | 1 | Search Eng | 0.5d | YES |
| TASK-102: Capture schema | 1 | Search Eng | 0.5d | YES |
| TASK-103: Provision AWS cluster | 1 | DevOps | 1d | YES |
| TASK-104: Create index | 1 | Search Eng | 0.5d | |
| TASK-105: Solr baseline | 1 | Search Eng | 1d | |
| TASK-201: Project skeleton | 2 | Backend Dev | 1d | |
| TASK-202: IndexService | 2 | Backend Dev | 1d | |
| TASK-203: SearchService | 2 | Search Eng | 2d | |
| TASK-204: Schema fidelity test | 2 | Search Eng | 0.5d | |
| TASK-205: Offline relevance | 2 | Search Eng | 2d | |
| TASK-206: ReindexService | 2 | Backend Dev | 1d | |
| TASK-301: Deploy DualWrite | 3 | Both | 1d | |
| TASK-302: Production reindex | 3 | Both | 1d | |
| TASK-303: Enable dual-write | 3 | DevOps | 0.5d | |
| TASK-304: Shadow traffic (3 wks) | 3 | Search Eng | 3w | |
| TASK-401: Traffic cutover | 4 | Both | 2–3d | |
| TASK-402: Post-cutover validation | 4 | Search Eng | 0.5d | |
| TASK-501: Remove dual-write | 5 | Backend Dev | 1d | |
| TASK-502: Decommission Solr | 5 | DevOps | 1d | |
| TASK-503: Documentation | 5 | Search Eng | 1d | |
