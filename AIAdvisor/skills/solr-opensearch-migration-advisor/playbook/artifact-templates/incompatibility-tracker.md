# Incompatibility Tracker

**Session:** {session_id}
**Generated:** {timestamp}
**Total:** {total_count} | **Breaking:** {breaking_count} | **Unsupported:** {unsupported_count} | **Behavioral:** {behavioral_count}

---

## Summary

| Metric | Value |
|--------|-------|
| Cutover-blocking items | {breaking_count + unsupported_count} |
| Items with mitigation plan | {mitigated_count} |
| Items needing investigation | {unmitigated_count} |
| Resolved since last snapshot | {resolved_count} |

## Breaking

*These must be resolved before cutover.  Each item blocks go/no-go approval.*

| ID | Category | Description | Recommendation | Owner | Status |
|----|----------|-------------|----------------|-------|--------|
| B-{n} | {schema/query/plugin/ops} | {description} | {recommendation} | {owner} | {open/in-progress/resolved} |

## Unsupported

*Solr features with no direct OpenSearch equivalent.  Require redesign or removal.*

| ID | Category | Description | Recommendation | Owner | Status |
|----|----------|-------------|----------------|-------|--------|
| U-{n} | {category} | {description} | {recommendation} | {owner} | {status} |

## Behavioral

*Features that exist in both platforms but behave differently.  May affect
relevance, performance, or user experience.  Monitor during parallel testing.*

| ID | Category | Description | Recommendation | Owner | Status |
|----|----------|-------------|----------------|-------|--------|
| V-{n} | {category} | {description} | {recommendation} | {owner} | {status} |

---

## Burn-down

*Compare successive snapshots to track resolution progress.*

| Snapshot | Breaking | Unsupported | Behavioral | Total open |
|----------|----------|-------------|------------|------------|
| {timestamp} | {n} | {n} | {n} | {n} |

---

## Relationship to Other Artifacts

- **Blocking items** feed into the Risk Register and gate the Go/No-Go Review.
- **Behavioral items** should be validated during parallel testing (Phase 7).
- **All items** appear in the Migration Report's Incompatibilities section.
- **Progress Dashboard** shows the incompatibility snapshot count.

---

*Auto-generated from session state.  New incompatibilities are added as the
advisor processes schemas, queries, and customizations.  Re-run the advisor
to refresh.*
