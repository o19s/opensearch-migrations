# Merging the Two Skill Approaches

This directory now contains two complementary approaches to Solr → OpenSearch
migration guidance:

1. **SKILL.md** (Jon's code-driven approach) — a conversational workflow with
   Python scripts, MCP server, session state, stakeholder-tailored guidance,
   and inline reference tables.

2. **references/** (Sean's knowledge-driven approach) — 16 expert reference files
   covering strategic guidance, pre-migration assessment, target design, migration
   execution, validation, operations, platform integration, and edge cases.

Both are valuable. This document proposes how to unify them.

---

## What Each Brings

### SKILL.md strengths
- **Structured 7-step workflow** with explicit ordering and skip prevention
- **Stakeholder role adaptation** — tailors depth per audience (Search Engineer
  vs. Product Manager)
- **Session persistence** — resumes across conversations
- **Python scripts** — schema converter, query converter, report generator, MCP server
- **Inline reference tables** — field type mappings, query incompatibilities,
  customization mappings, client library mappings

### references/ strengths
- **Deep expert knowledge** — Key Judgements, Decision Heuristics, Common Mistakes,
  war stories (not documentation summaries)
- **Consulting methodology** — OSC engagement patterns, intake workflow, relevance
  measurement methodology
- **Edge cases** — 30+ gotchas with external source links that go far beyond the
  inline tables
- **Platform-specific guidance** — Spring Boot/Kotlin, Python, Drupal, Rails
  integration patterns
- **Strategic guidance** — when NOT to migrate, risk assessment, go/no-go frameworks

---

## Proposed Merge Path

### Phase 1: Side-by-side (current state)

Both approaches coexist. The SKILL.md workflow can reference the expert files
for deeper context at each step. Add `#[[file:references/...]]` directives to
SKILL.md where the reference content is relevant:

| SKILL.md step | Reference file |
|---------------|---------------|
| Step 0 — Stakeholder ID | `references/consulting-methodology.md`, `references/roles-and-escalation-patterns.md` |
| Step 1 — Schema Acquisition | `references/03-target-design.md`, `references/solr-concepts-reference.md` |
| Step 2 — Incompatibility Analysis | `references/08-edge-cases-and-gotchas.md` |
| Step 3 — Query Translation | `references/04-migration-execution.md` |
| Step 4 — Customizations | `references/solr-concepts-reference.md` |
| Step 5 — Infrastructure | `references/06-operations.md`, `references/aws-opensearch-service.md` |
| Step 6 — Client Integration | `references/07-platform-integration.md` |
| Step 7 — Report | `references/05-validation-cutover.md`, `references/01-strategic-guidance.md` |

### Phase 2: Deduplicate inline tables

The SKILL.md inline tables (field type mapping, query incompatibilities,
customization table, client library table) overlap with content in the
reference files. Move the canonical versions into reference files and
replace inline tables with pointers. This keeps SKILL.md under 500 lines
(Agent Skills spec tenet T2).

### Phase 3: Unified routing

Merge the SKILL.md frontmatter to include both the `metadata.author` fields
and a combined `description` that covers both the conversational workflow and
the deep reference knowledge. The result is one skill with two modes:
- **Interactive mode** — the 7-step workflow with scripts and session state
- **Reference mode** — the agent loads reference files on demand for ad-hoc
  questions (no workflow, just expert answers)

---

## Content Gaps to Fill

The references bring expert knowledge that the current SKILL.md workflow
doesn't cover:

- **When NOT to migrate** — `01-strategic-guidance.md` has go/no-go frameworks
  that should inform a "Step -1" assessment before starting the workflow
- **Relevance validation** — `05-validation-cutover.md` covers Quepid/RRE
  methodology for measuring migration quality; not in the current workflow
- **Operations handoff** — `06-operations.md` covers ISM, monitoring, DR
  patterns for post-migration; the current workflow ends at "report"
- **Dual-write patterns** — `04-migration-execution.md` has detailed cutover
  strategies; the current workflow focuses on schema/query but not execution

---

## Decision Points

- **Should the Python scripts reference the expert files?** The schema and query
  converters could log warnings from `08-edge-cases-and-gotchas.md` when they
  detect patterns known to be problematic.

- **Should the workflow expand beyond 7 steps?** The references suggest a
  pre-engagement assessment (strategic guidance) and post-migration validation
  (relevance testing) that bookend the current 0–7 workflow.

- **Which author owns which files?** Proposed: Jon owns SKILL.md + scripts/,
  Sean owns references/. Both review changes that cross the boundary.
