# Migration Artifacts Index

**Project:** Enterprise Solr 7 to OpenSearch Migration
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
- [ ] P1-03 — Schema conversion report (after schema.xml is provided)
- [ ] P1-04 — Query translation report (after top queries are provided)
- [ ] P1-05 — Incompatibility register (auto-generated from schema + query analysis)
- [ ] P1-06 — Complexity scorecard (6-dimension scoring)
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
1. `P1-01` — Scan the 20 risk groups to understand what we're watching for
2. `P1-02` — Use this to run your first stakeholder session
3. `INDEX.md` — Come back here to find anything else
