# P1-04: Querqy & SMUI Migration Track

**Project:** Enterprise Solr 8 (Chorus) to OpenSearch Migration
**Generated:** 2026-04-02
**Status:** Investigation plan — research complete, execution pending
**Critical path:** Yes — Querqy plugin availability gates the entire migration

---

## Executive Summary

Querqy and SMUI **can** migrate to OpenSearch, but this is not a drop-in swap. Three things must be resolved:

1. **querqy-opensearch plugin version** — only 3 releases exist (OS 2.3, 2.19, 3.1). Your target OS version must match one of these.
2. **AWS managed service compatibility** — custom plugins on AWS OpenSearch Service have constraints. May require self-managed OS or a supported workaround.
3. **SMUI deploy script** — SMUI's built-in deploy targets Solr (file copy + core reload). A custom script (~50 lines of bash) is needed to push rules via the querqy-opensearch REST API.

**None of these are blockers.** But all three need answers before committing to a migration timeline.

---

## Part 1: querqy-opensearch Plugin

### Current State

| Property | Value |
|----------|-------|
| Repo | https://github.com/querqy/querqy-opensearch |
| Maintainer | Rene Kriegler (@renekrie) — Querqy co-author |
| Last commit | 2026-03-28 |
| Last release | 2026-03-31 (`opensearch-querqy-1.1.os3.1.0`) |
| Stars | 10 |
| License | Apache-2.0 |
| Status | **Actively maintained**, single primary maintainer |

### Version Compatibility Matrix

| Release | OpenSearch Version | Date | Notes |
|---------|-------------------|------|-------|
| `opensearch-querqy-1.0os.2.3.0` | **2.3.0** | 2022-09 | First release |
| `opensearch-querqy-1.1.os2.19.2` | **2.19.2** | 2025-07 | |
| `opensearch-querqy-1.1.os3.1.0` | **3.1.0** | 2026-03 | Latest |

**Gap: No releases for OpenSearch 2.4 through 2.18.** The plugin jumped from 2.3 → 2.19. Open issues confirm users hit "unable to install" errors on intermediate versions.

**Implication:** Your target must be **OS 2.19.x or 3.1.x** to use an official build. If AWS OpenSearch Service doesn't offer those exact versions, you may need to build from source or wait for a new release.

### Supported Rewriter Types

| Rewriter | Supported? | Chorus uses? | Notes |
|----------|-----------|--------------|-------|
| **CommonRulesRewriter** | Yes | Yes — synonyms, boosts, filters, deletes | Primary rewriter. Full parity with Solr. |
| **ReplaceRewriter** | Yes | Yes — spelling/normalization | Full parity with Solr. |
| **WordBreakRewriter** | Yes | No | Available if needed. |
| **NumberUnitRewriter** | Yes | No | Available if needed. |
| **Regex-based rewriters** | **Unclear** | Yes — `regex_screen_protectors` | Not mentioned in OS plugin README. Needs testing. |
| **Embedding rewriters** | **No** | No (Solr 8 vintage) | Only in newer Solr Querqy. Not relevant for this migration. |
| **Custom rewriters** | Yes (pluggable) | No | Framework supports custom Java rewriters. |

### How Rules Are Deployed (Different from Solr)

This is the key architectural difference:

| | Solr (current) | OpenSearch (target) |
|---|---|---|
| **Rule storage** | Files in ZooKeeper configset | Hidden index (`.opensearch-querqy`) |
| **Deploy mechanism** | File copy → ZK → core reload | REST API: `PUT /_plugins/_querqy/rewriter/<name>` |
| **Rule format** | `rules.txt` file | Same rules syntax, wrapped in JSON API body |
| **Cache** | Solr-managed | In-memory with configurable TTL |
| **Refresh** | Core reload | Automatic on PUT (cached, refreshed on next search) |

**Example — creating a rewriter in OpenSearch:**
```bash
curl -X PUT "https://opensearch:9200/_plugins/_querqy/rewriter/common_rules" \
  -H "Content-Type: application/json" \
  -d '{
    "class": "querqy.opensearch.rewriter.SimpleCommonRulesRewriterFactory",
    "config": {
      "rules": "notebook =>\n  SYNONYM: laptop\n\nsamsung tv =>\n  UP(100): brand:samsung"
    }
  }'
```

### Known Limitations vs. Solr Plugin

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Single maintainer (Rene Kriegler) | Bus factor risk for the plugin | Querqy-core is shared; OS plugin is thin wrapper |
| No multiplicative boosts (issue #25) | If Chorus rules use multiplicative boosts, they won't work | Check rules for multiplicative vs. additive boosts |
| AWS managed service may block custom plugins | Could prevent deployment on AWS OpenSearch Service | See AWS investigation section below |
| Smaller community (10 stars) | Less battle-tested than Solr plugin | Mitigated by shared querqy-core library |
| Version gap (2.3 → 2.19) | Limits target OS version choice | Pin to 2.19.x or 3.1.x |

---

## Part 2: SMUI (Search Management UI)

### Current State

| Property | Value |
|----------|-------|
| Repo | https://github.com/querqy/smui |
| Version | v4.0.11 (released 2024-03-12) |
| Language | Scala (Play Framework) |
| Last commit | 2025-06-23 |
| Stars | 56 |
| License | Apache-2.0 |
| Status | Moderately maintained (5-10 commits/year) |

### OpenSearch Support Status

**SMUI is engine-agnostic at the rule management layer.** It stores rules in its own MySQL database and exports standard querqy `rules.txt` format. The rules format is identical for Solr, Elasticsearch, and OpenSearch.

**The gap is purely in deployment.** SMUI's built-in deploy script (`smui2solr.sh`) does:
1. Generate `rules.txt` from database → write to temp file
2. `cp` or `scp` the file to a destination path
3. HTTP call to Solr to reload core

**For OpenSearch, you need a custom deploy script** that:
1. Reads the same temp file
2. Pushes it to the querqy-opensearch REST API

### SMUI Deploy Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        SMUI                              │
│                                                          │
│  Rule DB (MySQL) → QuerqyRulesTxtGenerator               │
│       │                                                  │
│       ▼                                                  │
│  /tmp/rules-txt.tmp         /tmp/replace-rules.tmp       │
│       │                          │                       │
│       ▼                          ▼                       │
│  Deploy Script (custom-script=true)                      │
└──────────────────────┬───────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
     Current (Solr)           Target (OpenSearch)
          │                         │
   cp rules.txt → ZK         PUT /_plugins/_querqy/
   + core reload              rewriter/common_rules
                              + rewriter/replace
```

### Custom Deploy Script (smui2opensearch.sh)

This is what needs to be written. It's straightforward — ~50 lines of bash:

```bash
#!/bin/bash
# smui2opensearch.sh — Deploy SMUI rules to OpenSearch via querqy-opensearch REST API
#
# Called by SMUI with positional args:
#   $1 = SRC_TMP_FILE (rules.txt temp path)
#   $2 = DST_CP_FILE_TO (unused for API deploy, but keep for backup)
#   $3 = SOLR_HOST (repurpose as OPENSEARCH_HOST)
#   $4 = SOLR_CORE_NAME (repurpose as REWRITER_NAME)
#   $5 = DECOMPOUND_DST_CP_FILE_TO (unused unless decompound rules exist)
#   $6 = TARGET_SYSTEM (e.g., "LIVE" or "PRELIVE")
#   $7 = REPLACE_RULES_SRC_TMP_FILE
#   $8 = REPLACE_RULES_DST_CP_FILE_TO (unused for API deploy)

set -euo pipefail

RULES_FILE="$1"
OS_HOST="$3"
TARGET="$6"
REPLACE_FILE="${7:-}"

# Determine rewriter names based on target (LIVE vs PRELIVE)
if [ "$TARGET" = "PRELIVE" ]; then
    COMMON_REWRITER="common_rules_prelive"
    REPLACE_REWRITER="replace_prelive"
else
    COMMON_REWRITER="common_rules"
    REPLACE_REWRITER="replace"
fi

# Escape rules content for JSON embedding
escape_for_json() {
    python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))" < "$1"
}

# Deploy common rules
if [ -f "$RULES_FILE" ] && [ -s "$RULES_FILE" ]; then
    RULES_ESCAPED=$(escape_for_json "$RULES_FILE")
    curl -sf -X PUT "${OS_HOST}/_plugins/_querqy/rewriter/${COMMON_REWRITER}" \
        -H "Content-Type: application/json" \
        -d "{
            \"class\": \"querqy.opensearch.rewriter.SimpleCommonRulesRewriterFactory\",
            \"config\": { \"rules\": ${RULES_ESCAPED} }
        }"
    echo "Deployed common rules to ${COMMON_REWRITER}"
fi

# Deploy replace rules
if [ -n "$REPLACE_FILE" ] && [ -f "$REPLACE_FILE" ] && [ -s "$REPLACE_FILE" ]; then
    REPLACE_ESCAPED=$(escape_for_json "$REPLACE_FILE")
    curl -sf -X PUT "${OS_HOST}/_plugins/_querqy/rewriter/${REPLACE_REWRITER}" \
        -H "Content-Type: application/json" \
        -d "{
            \"class\": \"querqy.opensearch.rewriter.SimpleCommonRulesRewriterFactory\",
            \"config\": { \"rules\": ${REPLACE_ESCAPED} }
        }"
    echo "Deployed replace rules to ${REPLACE_REWRITER}"
fi
```

**SMUI config to enable custom script:**
```
toggle.rule-deployment.custom-script=true
toggle.rule-deployment.custom-script-SMUI2SOLR-SH_PATH=/path/to/smui2opensearch.sh
```

### SMUI Migration Effort Estimate

| Task | Effort | Owner |
|------|--------|-------|
| Write `smui2opensearch.sh` deploy script | 2-4 hours | OS expert |
| Test LIVE deploy against querqy-opensearch | 2-4 hours | OS expert |
| Test PRELIVE deploy | 1-2 hours | OS expert |
| Update SMUI config (host, script path, labels) | 1 hour | Sys admin |
| Verify existing rules deploy correctly | 2-4 hours | Solr expert + Tester |
| **Total** | **~1-2 days** | |

---

## Part 3: AWS OpenSearch Service Constraints

This is the biggest unknown and could change the entire approach.

### The Problem

AWS OpenSearch Service is a **managed service**. Installing custom plugins (like querqy-opensearch) requires using the **custom plugin** feature, which has constraints:

- Plugin must be packaged as a ZIP and uploaded to S3
- AWS must approve the plugin (automated validation)
- Not all plugin types are allowed (security plugins, for example, are restricted)
- Plugin must be compatible with the exact AWS OpenSearch version
- Reported issues: GitHub issue #81 reports `VALIDATION_FAILED` on AWS OpenSearch 2.3

### Investigation Required

| Question | Who | How |
|----------|-----|-----|
| Does AWS OpenSearch Service support custom query parser plugins? | Sys admin | Check AWS docs + open support case |
| Which OS versions does AWS currently offer? | Sys admin | AWS Console → OpenSearch → Create Domain → version dropdown |
| Can querqy-opensearch be installed as a custom plugin on AWS? | OS expert | Test with a dev domain |
| If not: is self-managed OpenSearch on EC2/EKS acceptable? | You (project lead) | Discuss with stakeholders |

### Decision Tree

```
Can we install querqy-opensearch on AWS managed OpenSearch?
│
├── YES → Proceed with managed service. 
│         Pin to OS 2.19.x or 3.1.x.
│         Deploy SMUI rules via REST API.
│
├── NO, but self-managed is OK → Deploy OpenSearch on EC2/EKS.
│         Full control over plugins.
│         More ops burden (your sys admin carries this).
│
└── NO, and must stay managed → Querqy is off the table.
          Redesign query layer using native OS features:
          • multi_match + bool queries replace eDisMax
          • Search templates replace ParamSets
          • Synonym files in index settings replace CommonRules synonyms
          • function_score replaces boost rules
          • No equivalent for DELETE rules — app-layer stopword handling
          
          SMUI is also off the table in this path.
          This is a SIGNIFICANT scope increase — flag immediately.
```

---

## Part 4: Regex Rewriter Investigation

The `regex_screen_protectors` rewriter in Chorus uses a regex-based rewriter that may or may not be available in querqy-opensearch.

### What to check

```bash
# On the querqy-opensearch plugin, check if regex rewriter class exists:
# Look for RegexFilterRewriter or similar in the plugin JAR
jar tf querqy-opensearch-*.jar | grep -i regex
```

### Fallback if not supported

If regex rewriters aren't available in querqy-opensearch:
1. **Convert to CommonRules** — if the regex is simple (e.g., matching specific product types), rewrite as explicit CommonRules entries
2. **Move to app layer** — apply regex-based filtering in the application before/after the search call
3. **Use OpenSearch scripting** — painless script in a `script_score` or `bool` filter

**Risk: Low.** The `regex_screen_protectors` rewriter is a Chorus demo feature, not a complex business rule. Either of the fallbacks works.

---

## Part 5: Migration Sequence

### Phase 1: Verify (Week 1-2)

| # | Task | Owner | Depends on | Deliverable |
|---|------|-------|------------|-------------|
| 1 | Determine target OpenSearch version (2.19.x or 3.1.x) | OS expert + Sys admin | AWS version availability | Version decision |
| 2 | Test querqy-opensearch plugin install on target version | OS expert | Task 1 | Working plugin on dev cluster |
| 3 | Test AWS managed service custom plugin support | Sys admin | Task 1 | Managed vs. self-managed decision |
| 4 | Export current Querqy rules from Chorus ZooKeeper | Solr expert | None | `rules.txt` + `replace-rules.txt` files |
| 5 | Export current SMUI rule count and categories | Solr expert | None | Rule inventory with counts by type |
| 6 | Verify regex rewriter availability in querqy-opensearch | OS expert | Task 2 | Supported / fallback decision |

### Phase 2: Build Integration (Week 3-4)

| # | Task | Owner | Depends on | Deliverable |
|---|------|-------|------------|-------------|
| 7 | Deploy exported CommonRules to OS via REST API (manual) | OS expert | Tasks 2, 4 | Rules running on OS dev cluster |
| 8 | Deploy exported Replace rules to OS via REST API (manual) | OS expert | Tasks 2, 4 | Replace rewriter running |
| 9 | Write `smui2opensearch.sh` deploy script | OS expert | Task 7 | Tested deploy script |
| 10 | Configure SMUI to use custom deploy script | Sys admin | Task 9 | SMUI → OS deploy working |
| 11 | Test SMUI LIVE + PRELIVE deploy cycle end-to-end | Tester | Task 10 | Verified rule management workflow |

### Phase 3: Validate (Week 5-6)

| # | Task | Owner | Depends on | Deliverable |
|---|------|-------|------------|-------------|
| 12 | Run Chorus judgment set (125 queries) against OS with Querqy | Tester | Tasks 7, 8 | Relevance comparison report |
| 13 | Compare Solr vs. OS results for top query families | Tester + Solr expert | Task 12 | Delta analysis |
| 14 | Tune OS boosts to account for BM25 scoring shift | OS expert | Task 13 | Updated boost values |
| 15 | Re-run judgment set after tuning | Tester | Task 14 | Final relevance comparison |

---

## Part 6: Risk Register (Querqy/SMUI Specific)

| ID | Risk | Severity | Likelihood | Mitigation | Owner |
|----|------|----------|------------|------------|-------|
| QS-01 | querqy-opensearch plugin incompatible with target OS version | **Critical** | Medium | Pin to 2.19.x or 3.1.x; build from source as fallback | OS expert |
| QS-02 | AWS managed service blocks custom plugin install | **Critical** | Medium | Self-managed OS on EC2/EKS; or redesign without Querqy (major scope change) | Sys admin |
| QS-03 | SMUI deploy script fails on PRELIVE cycle | **Medium** | Low | Well-understood integration point; test early | OS expert |
| QS-04 | Regex rewriter not available in querqy-opensearch | **Low** | Medium | Convert to CommonRules or app-layer filter | OS expert |
| QS-05 | BM25 scoring shift breaks tuned Querqy boost values | **High** | High | Baseline with Quepid, retune boosts, re-validate | Tester + OS expert |
| QS-06 | Single maintainer risk on querqy-opensearch | **Medium** | Low | querqy-core is shared; OS plugin is thin wrapper; community can fork | You |
| QS-07 | Rule count exceeds OS plugin performance expectations | **Low** | Low | Typical Chorus rule count (~100-250) is small; test with actual rules | Tester |

---

## Decision Log

Track decisions here as they're made:

| Date | Decision | Rationale | Decided by |
|------|----------|-----------|------------|
| | Target OpenSearch version: ___ | | |
| | Managed vs. self-managed: ___ | | |
| | Querqy approach: plugin / redesign without: ___ | | |
| | SMUI approach: migrate / replace / drop: ___ | | |
| | Regex rewriter: supported / fallback to ___: ___ | | |
