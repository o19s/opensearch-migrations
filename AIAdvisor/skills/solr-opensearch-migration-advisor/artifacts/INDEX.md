# Migration Artifacts Index

**Project:** Enterprise Solr 8 (Chorus) to OpenSearch Migration
**Created:** 2026-04-02

---

## Naming Convention

```
P{phase}-{seq}_{short-description}.md

Phase prefixes:
  P1 = Audit & Design       (weeks 1-4)
  P2 = Build & Validate     (weeks 5-8)
  P3 = Dual-Write & Shadow  (weeks 9-14)
  P4 = Cutover              (weeks 15-16)
  P5 = Cleanup & Handoff    (weeks 17-20)

Examples:
  P1-01_discovery-question-matrix.md
  P2-03_schema-conversion-report.md
  P4-01_go-no-go-checklist.md
```

**Why this works at scale:**
- `ls` sorts files by phase, then sequence — you see the migration timeline in directory order
- The phase prefix tells you instantly *when* in the project this artifact matters
- The sequence number within each phase gives a natural reading order
- The description after `_` is human-readable without opening the file

**Special files (no phase prefix):**
- `INDEX.md` — this file (artifact registry and naming guide)
- `SESSION-NN_*.md` — intake/review session notes (use session number, not phase)

---

## Artifact Registry

### P1: Audit & Design

| File | Description | Audience | Status |
|------|-------------|----------|--------|
| [P1-01_discovery-question-matrix.md](P1-01_discovery-question-matrix.md) | 200-item risk discovery matrix across 20 groups. Use as comprehensive reference during intake. | All team | Ready |
| [P1-02_intake-interview-template.md](P1-02_intake-interview-template.md) | 66-question structured interview guide for stakeholder sessions. Fill in live during meetings. | Project lead | Ready |
| [P1-03_chorus-source-audit.md](P1-03_chorus-source-audit.md) | Best-guess source config audit: schema, solrconfig, Querqy, SMUI, dataset. ~30 assumptions to verify. | Solr expert + OS expert | Assumed — needs verification |
| [P1-04_querqy-smui-migration-track.md](P1-04_querqy-smui-migration-track.md) | Querqy + SMUI investigation: plugin compat, SMUI deploy script, AWS constraints, decision tree, 15-task execution plan. | OS expert + Sys admin | Ready |

### P2: Build & Validate

| File | Description | Audience | Status |
|------|-------------|----------|--------|
| *(artifacts generated as schema, queries, and configs are provided)* | | | |

### P3: Dual-Write & Shadow

| File | Description | Audience | Status |
|------|-------------|----------|--------|
| *(artifacts generated during dual-write phase)* | | | |

### P4: Cutover

| File | Description | Audience | Status |
|------|-------------|----------|--------|
| *(go/no-go checklists, cutover runbooks)* | | | |

### P5: Cleanup & Handoff

| File | Description | Audience | Status |
|------|-------------|----------|--------|
| *(decommission plans, handoff docs)* | | | |

---

## Expected Artifacts by Phase

This is the full list of artifacts the migration will produce. Items are created as inputs become available.

### P1: Audit & Design
- [x] P1-01 — Discovery question matrix (200-item risk reference)
- [x] P1-02 — Intake interview template (66-question session guide)
- [x] P1-03 — Chorus source audit (schema, solrconfig, Querqy, SMUI, dataset — assumed, awaiting verification)
- [x] P1-04 — Querqy + SMUI migration track (plugin compat, deploy script, AWS decision tree, execution plan)
- [ ] P1-04b — Query translation report (after top queries are confirmed)
- [ ] P1-05 — Incompatibility register (preliminary in P1-03 §8, full version after verification)
- [ ] P1-06 — Complexity scorecard (preliminary in P1-03 §7, full version after verification)
- [ ] P1-07 — Infrastructure sizing recommendation
- [ ] P1-08 — Client integration inventory
- [ ] P1-09 — Risk register

### P2: Build & Validate
- [ ] P2-01 — OpenSearch index mappings (final)
- [ ] P2-02 — Analyzer chain conversion details
- [ ] P2-03 — Query DSL translation guide (for dev team)
- [ ] P2-04 — Relevance baseline report (Solr measurements)
- [ ] P2-05 — Gold query set

### P3: Dual-Write & Shadow
- [ ] P3-01 — Dual-write architecture spec
- [ ] P3-02 — Shadow traffic comparison report
- [ ] P3-03 — Relevance comparison report (Solr vs. OpenSearch)

### P4: Cutover
- [ ] P4-01 — Go/no-go checklist
- [ ] P4-02 — Cutover runbook
- [ ] P4-03 — Rollback procedure

### P5: Cleanup & Handoff
- [ ] P5-01 — Decommission plan (Solr + ZooKeeper)
- [ ] P5-02 — Operations runbook (OpenSearch)
- [ ] P5-03 — Knowledge transfer summary

---

## Quick Start

**New to this project?** Read these in order:
1. `P1-03` — Start here: what we think we're migrating (Chorus source audit)
2. `P1-01` — Scan the 20 risk groups to understand what we're watching for
3. `P1-02` — Use this to run your first stakeholder session
4. `INDEX.md` — Come back here to find anything else
