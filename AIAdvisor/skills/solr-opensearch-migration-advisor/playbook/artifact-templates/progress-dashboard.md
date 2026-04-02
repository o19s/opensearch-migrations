# Migration Progress Dashboard

**Session:** {session_id}
**Generated:** {timestamp}
**Overall status:** {overall_status}

---

## Executive Summary

| Phase | Status | Blockers |
|-------|--------|----------|
| 0. Stakeholder identification | {done/in-progress/not-started} | {blocker or "None"} |
| 1. Schema acquisition | {status} | {blocker} |
| 2. Schema review & incompatibilities | {status} | {blocker} |
| 3. Query translation | {status} | {blocker} |
| 4. Customization assessment | {status} | {blocker} |
| 5. Infrastructure planning | {status} | {blocker} |
| 6. Client integration assessment | {status} | {blocker} |
| 7. Report & recommendations | {status} | {blocker} |

**Incompatibility snapshot:**  {breaking_count} breaking | {unsupported_count} unsupported | {behavioral_count} behavioral

**Blocking risks:** {blocking_risk_count} (see Risk Register)

> *Managers / execs: the table above is the status.  Scroll down only if you
> want technical detail.*

---

## Phase Detail

### Phase 0 — Stakeholder Identification

- **Stakeholder role:** {stakeholder_role}
- **Team roster captured:** {yes/no}
- **Decision authority assigned:** {yes/no}

### Phase 1 — Schema Acquisition

- **Source format:** {schema_source}
- **Collections analyzed:** {collection_list}
- **Fields converted:** {field_count}
- **Field types mapped:** {field_type_count}
- **Conversion result:**
  - Cleanly mapped: {clean_count}
  - Mapped with caveats: {caveat_count}
  - Unmapped / requires manual review: {unmapped_count}

### Phase 2 — Schema Review & Incompatibility Analysis

- **Incompatibilities discovered:** {incompatibility_count}
- **By severity:**

| Severity | Count | Examples |
|----------|-------|----------|
| Breaking | {n} | {first 2-3 descriptions} |
| Unsupported | {n} | {first 2-3 descriptions} |
| Behavioral | {n} | {first 2-3 descriptions} |

- **Analyzer chains reviewed:** {analyzer_count}
- **User review notes:** {schema_review_notes}

### Phase 3 — Query Translation

- **Queries translated:** {queries_translated}
- **Query types encountered:** {query_types}
- **Translation results:**

| Query type | Count | Fully translated | Needs manual review |
|-----------|-------|-----------------|-------------------|
| Standard Lucene | {n} | {n} | {n} |
| DisMax / eDisMax | {n} | {n} | {n} |
| Facet queries | {n} | {n} | {n} |
| Spatial | {n} | {n} | {n} |
| Function queries | {n} | {n} | {n} |
| Other | {n} | {n} | {n} |

### Phase 4 — Customization Assessment

- **Custom request handlers:** {custom_request_handlers}
- **Custom plugins:** {custom_plugins}
- **Operational patterns:** {operational_patterns}
- **Auth method:** {auth_method}
- **Redesign zones identified:** {redesign_zone_count}

### Phase 5 — Infrastructure Planning

| Current (Solr) | Target (OpenSearch) |
|----------------|-------------------|
| {node_count} nodes | {recommended_nodes} nodes |
| {shard_count} shards | {recommended_shards} shards |
| {total_index_size_gb} GB index | {estimated_os_size_gb} GB (est.) |
| {jvm_heap_gb} GB heap | {recommended_heap_gb} GB heap |
| {qps} QPS | {qps} QPS (target) |

- **Platform:** {target_platform}
- **Region:** {aws_region}
- **AZ count:** {az_count}

### Phase 6 — Client Integration Assessment

| Integration | Type | Migration action | Effort |
|------------|------|-----------------|--------|
| {name} | {library/ui/http/other} | {action} | {low/med/high} |

### Phase 7 — Report & Recommendations

- **Report generated:** {yes/no}
- **Report path:** {latest_report_path}
- **Recommendation:** {proceed/hold/investigate}

---

## Change Log

*Each timestamped snapshot captures the state at generation time.  Compare
successive snapshots to see what changed between advisor sessions.*

| Timestamp | Notable changes |
|-----------|----------------|
| {timestamp} | {Initial generation / Phase N completed / N new incompatibilities / etc.} |

---

*Auto-generated from session state.  Re-run the advisor or request "progress"
to refresh.*
