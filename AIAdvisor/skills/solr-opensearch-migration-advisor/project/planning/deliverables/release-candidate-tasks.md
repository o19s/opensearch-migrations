# Release Candidate Task List: Migration Advisor v1.0-rc

Draft for OSC internal discussion, then presentation to Amazon team.
Generated 2026-03-22.

**Goal:** A release candidate that demonstrates the advisor is *useful today* for real
Solr→OpenSearch migration engagements, while showing a credible path to Migration
Assistant integration.

**Audience for this list:** OSC team (Eric, Jeff, Daniel, Sean) to align on scope,
then Amazon team to discuss priorities and timeline.

---

## RC Scope: What "Release Candidate" Means Here

An RC is not production-ready — it's *demo-ready and discussion-ready*. It should:
1. Handle one complete migration scenario end-to-end (TechProducts or equivalent)
2. Produce a useful migration report from that scenario
3. Work via MCP (so it can be demoed in Kiro or any MCP client)
4. Have enough test coverage to be credible
5. Show how it fits into the Migration Assistant architecture

What it does NOT need yet: HTTP adapter, Dockerfile, CDK construct, S3 storage,
multi-engine support, or production hardening.

---

## Phase 1: Foundation (get the structure right)

### 1.1 Adopt Eric's PR #5 layout
- [ ] Merge PR #5 (`mimic_launchpad_dir_structure`) on o19s fork
- [ ] Validate directory structure matches agentskills.io conventions
- [ ] Fix naming if needed (underscores → hyphens per spec)
- **Owner:** Eric (merge), Sean (validate)
- **Blocked by:** Eric's approval

### 1.2 Port agent99 knowledge base (PRs A + B from porting guide)
- [ ] PR A: 6 Solr-specific references → `skills/solr/references/` (~900 lines)
- [ ] PR B: 12 engine-agnostic references → `skills/migration_planner/references/` (~2,500 lines)
- [ ] PR C: IDE configs (Kiro + Cursor) → `kiro/`, `cursor/` (~200 lines)
- **Owner:** Sean
- **Blocked by:** 1.1

### 1.3 Split Jeff's code into two-skill layout
- [ ] Move `skill.py`, `report.py`, `storage.py` → `skills/migration-planner/scripts/`
- [ ] Move `schema_converter.py`, `query_converter.py` → `skills/solr/scripts/`
- [ ] Move `mcp_server.py` → `mcp/server.py`
- [ ] Update all import paths
- [ ] Verify existing tests pass after move
- **Owner:** Jeff or Sean (coordinate)
- **Blocked by:** 1.1

---

## Phase 2: Close the SKILL.md ↔ Code Gap (the #1 risk)

This is the difference between "demo that impresses" and "demo that raises questions."

### 2.1 Implement conversational workflow in handle_message()
Currently a keyword router. Needs to become a state-driven conversation:

- [ ] **Step 0 — Stakeholder identification**: Ask who the user is (dev, architect, ops, manager). Store in session. Tailor subsequent output.
- [ ] **Step 1 — Schema acquisition**: Already partially works (accepts schema XML/JSON). Needs prompting: "Do you have your schema.xml or Schema API output?"
- [ ] **Step 2 — Schema review**: After conversion, present findings and incompatibilities. Ask user to confirm/correct. Currently skipped.
- [ ] **Step 3 — Query translation**: Already partially works. Needs to handle common patterns beyond basic queries.
- [ ] **Step 4 — Customization assessment**: Pose questions from agent99's intake questionnaire to uncover custom request handlers, plugins, auth, operational constraints.
- [ ] **Step 5 — Cluster assessment**: Sizing heuristics. At minimum, ask about current cluster topology and produce rough OpenSearch sizing.
- [ ] **Step 6 — Client integration assessment**: Identify consuming applications (SolrJ, pysolr, Drupal, Spring Data Solr). Flag client library changes needed.
- [ ] **Step 7 — Report generation**: Already exists but reports are hollow. Wire up session state to report sections.
- **Owner:** Jeff (primary), Sean (knowledge base inputs)
- **Note:** Not all steps need to be fully autonomous for RC. Steps 0, 1-3, 7 are must-haves. Steps 4-6 can start as guided Q&A.

### 2.2 Wire steering docs into the workflow
- [ ] `steering/stakeholders.md` — populate with role-specific guidance patterns
- [ ] `steering/accuracy.md` — already exists, verify it influences responses
- [ ] `steering/migration_execution.md` — connect to Step 4-6 logic
- [ ] References loaded on demand (not all at init) based on conversation state
- **Owner:** Jeff + Sean

### 2.3 Improve schema_converter.py
- [ ] Analyzer chain conversion (tokenizer + filter pipeline → OpenSearch analysis block)
- [ ] `copyField` → `copy_to` mapping
- [ ] Dynamic field patterns (`*_t`, `*_i`) → dynamic templates
- [ ] `fieldType` inheritance resolution
- [ ] Incompatibility flagging for unconvertible types
- **Owner:** Jeff

### 2.4 Improve query_converter.py
- [ ] eDisMax parameter handling (`qf`, `pf`, `pf2`, `pf3`, `mm`, `bq`, `bf`)
- [ ] Filter query (`fq`) → `bool.filter`
- [ ] Facets → aggregations (terms, range, date range)
- [ ] Highlighting → highlight API
- [ ] Grouping → `collapse` + `top_hits`
- [ ] Clear incompatibility warnings for: streaming expressions, graph traversal, XCJF, payload scoring
- **Owner:** Jeff
- **Note:** Spatial, MLT, spellcheck can be post-RC stretch goals

---

## Phase 3: Report Quality (the deliverable Amazon sees)

### 3.1 Wire report.py to session state
- [ ] Milestones section populated from workflow progress
- [ ] Blockers section populated from incompatibilities detected
- [ ] Implementation points from schema + query conversion results
- [ ] Front-end integration assessment from Step 6 findings
- [ ] Cost estimation (even rough heuristics: "3-node Solr → 6+ node OpenSearch because of replica placement rules")
- **Owner:** Jeff

### 3.2 Create a golden demo scenario
- [ ] Use TechProducts (Solr's bundled example) as the reference scenario
- [ ] Walk through Steps 0-7 with realistic inputs
- [ ] Produce a complete migration report
- [ ] Store as integration test + demo script
- **Owner:** Sean + Jeff

### 3.3 Validate against agent99's worked example
- [ ] Compare RC report output against `examples/techproducts-demo/` artifacts
- [ ] Identify sections where agent99's prose is richer than the code output
- [ ] File issues or backlog items for each gap
- **Owner:** Sean

---

## Phase 4: Testing & Quality

### 4.1 Unit test coverage
- [ ] Existing tests pass after code reorganization (Phase 1.3)
- [ ] New tests for each implemented workflow step
- [ ] Schema converter edge cases (analyzer chains, dynamic fields, copyField)
- [ ] Query converter edge cases (eDisMax, fq, facets)
- **Owner:** Jeff

### 4.2 Integration tests
- [ ] End-to-end MCP test: connect client → send schema → get report
- [ ] Session persistence: start conversation, resume in new session
- [ ] Port agent99's eval suite (PR E from porting guide) if time allows
- **Owner:** Sean + Jeff

### 4.3 LLM-as-judge evaluation (stretch)
- [ ] Run golden scenarios through eval harness
- [ ] Score output quality on accuracy, completeness, actionability
- [ ] Establish baseline metrics for tracking improvement
- **Owner:** Sean

---

## Phase 5: Packaging & Presentation

### 5.1 MCP server verification
- [ ] All tools work end-to-end (10 registered tools)
- [ ] Error handling for malformed inputs
- [ ] Session persistence across tool calls
- [ ] Document setup instructions for reviewers
- **Owner:** Jeff

### 5.2 Kiro power packaging
- [ ] POWER.md points to correct skill paths
- [ ] mcp.json starts MCP server correctly
- [ ] Steering symlinks resolve in the new layout
- [ ] Test in Kiro IDE
- **Owner:** Sean

### 5.3 Demo script for Amazon
- [ ] Written walkthrough: what to show, what to say, what to skip
- [ ] Canned inputs that showcase strengths (TechProducts schema, common queries)
- [ ] Known limitations documented (what to deflect if asked)
- [ ] Backup plan if live demo fails (pre-recorded or static report)
- **Owner:** Daniel + Sean

---

## Phase 6: Upstream Alignment (post-RC, pre-contribution)

These are not blocking the RC but should be discussed with Amazon:

### 6.1 Adopt upstream patterns
- [ ] Audit logging (log every prompt, tool use, result)
- [ ] Safety tiers (Observe/Propose/Execute) — at minimum, document the model
- [ ] Match steering doc convention (`*.md` loaded at runtime)
- **Owner:** Sean + Jeff

### 6.2 Migration Assistant integration plan
- [ ] HTTP adapter design (FastAPI wrapping handle_message)
- [ ] Dockerfile for containerized deployment
- [ ] CDK construct sketch (ECS task def, security group, IAM role)
- [ ] Document how advisor fits into `migration_services.yaml`
- **Owner:** Jeff + Eric

### 6.3 Upstream PR preparation
- [ ] Align with Apache-2.0 (already done)
- [ ] Match Python conventions (pipenv, pytest)
- [ ] Pre-commit hooks per upstream `install_githooks.sh`
- [ ] Draft PR description for `AIAdvisor/` in `opensearch-project/opensearch-migrations`
- **Owner:** Eric (primary)

---

## Priority / Sequencing Summary

```
Phase 1 (Foundation)          ← Do now. Unblocks everything.
    ↓
Phase 2 (Close the gap)       ← Highest value. This IS the product.
    ↓
Phase 3 (Report quality)      ← What Amazon evaluates.
Phase 4 (Testing)             ← Runs in parallel with Phase 3.
    ↓
Phase 5 (Packaging + demo)    ← Final assembly.
    ↓
Phase 6 (Upstream alignment)  ← Discussion topic, not RC blocker.
```

## Discussion Questions for Amazon

1. **Which deployment target matters most for first release?** MCP server (IDE integration) vs Migration Assistant (containerized service). This drives Phase 5 vs Phase 6 priority.
2. **How important is the report vs the conversation?** If Amazon cares more about the generated report artifact, we invest in Phase 3. If they care more about interactive guidance, we invest in Phase 2.
3. **What's the bar for upstream contribution?** Do they want a polished PR for `opensearch-project/opensearch-migrations`, or is the O19s fork sufficient for now?
4. **Coordination with upstream Solr PRs** — 6 active PRs adding Solr detection/translation in Java. Should our Python advisor defer to those for certain capabilities, or provide independent coverage?
5. **Timeline expectations** — What does Amazon consider a reasonable cadence for RC → release → upstream contribution?
