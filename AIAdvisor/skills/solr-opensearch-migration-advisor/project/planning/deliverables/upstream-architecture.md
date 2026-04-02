# Upstream Architecture: What OSC Needs to Know

Generated 2026-03-22. Deep analysis of `opensearch-project/opensearch-migrations` internals.

**Sources:**
- Upstream repo: https://github.com/opensearch-project/opensearch-migrations
- O19s fork: https://github.com/o19s/opensearch-migrations
- Upstream PRs: https://github.com/opensearch-project/opensearch-migrations/pulls

---

## 1. The Upstream Is More Sophisticated Than It Looks

The migration assistant isn't just a CLI tool — it's a full orchestration platform with
three layers that our advisor needs to integrate with (or at least not conflict with).

### 1.1 Argo Workflow Orchestration (`orchestrationSpecs/`)

**Source:** https://github.com/opensearch-project/opensearch-migrations/tree/main/orchestrationSpecs

The upstream uses a TypeScript monorepo that generates [Argo Workflow](https://argoproj.github.io/workflows/)
templates from user config. This is the "flow control" layer.

**How it works:**
1. User writes a `workflow-config.yaml`
2. `config-processor` CLI validates against Zod schemas (`packages/schemas/src/userSchemas.ts`)
3. Transforms into Argo Workflow templates + K8s CRD resources
4. Deploys to K8s; Argo orchestrates execution with approval gates

**Package dependency chain:**
```
schemas (Zod validation)
    ↓
config-processor (CLI: user config → K8s resources)
    ↓
argo-workflow-builders (constructs Argo templates)
    ↓
migration-workflow-templates (full workflow definitions)
```

**Approval gates (PR #2462):** Moving from Argo suspend steps to CRD-based signaling.
New `ApprovalGate` CRD — workflow creates it, CLI patches `status.phase` to `Approved`.
This decouples workflow control from the Argo API.

**Why this matters for OSC:** If the advisor eventually generates migration playbooks,
those playbooks could be `.wf.yaml` files that feed directly into this pipeline. The
advisor wouldn't just *recommend* a migration plan — it could *produce an executable one*.

### 1.2 Kiro AI Agent Configuration (`kiro-cli/`)

**Source:** https://github.com/opensearch-project/opensearch-migrations/tree/main/kiro-cli

This is the upstream's AI/LLM integration point. It configures a Kiro agent (Claude) to
operate the migration tools. Key patterns we should adopt:

**Agent definition** (`kiro-cli-config/agents/opensearch-migration.json`):
- Model: `claude-opus-4.5`
- Tools: `["*"]` (all tools enabled)
- Resources: steering docs (`file://.kiro/steering/*.md`)
- Agent spawn hook: auto-clones the project wiki on startup

**Steering docs** (`kiro-cli-config/steering/`):
- `workflow.md` — 500+ line workflow CLI reference with safety guardrails
- `deployment.md` — EKS deployment procedures
- `migration-prompt.md` — Auto-discovery prompt (scans AWS for domains, guides migration)
- `product.md` — Product context and wiki references

**Trust & debuggability patterns:**

| Pattern | Implementation | Source |
|---------|---------------|--------|
| Audit logging | Hooks log every prompt, tool use, and result to `.kiro/audit.log` | `kiro-cli-config/settings/hooks.json` |
| Safety tiers | Observe (read-only) / Propose (explain impact) / Execute (with approval) | `steering/workflow.md` |
| Read-only auto-allow | AWS reads don't need approval; writes always do | Agent config `autoAllowReadonly: true` |
| Pre-approval verification | "ALWAYS check workflow output BEFORE approving" | `steering/workflow.md` |
| Wiki cloning | Agent gets latest docs automatically on startup | Agent spawn hook |

**Why this matters for OSC:** Our advisor should adopt these same patterns. The agent99
repo already has safety tiers in `09-approval-and-safety-tiers.md` — these align well.
When we package as a Kiro power, we should include audit hooks and the graduated
permission model.

### 1.3 Migration Console (`migrationConsole/`)

**Source:** https://github.com/opensearch-project/opensearch-migrations/tree/main/migrationConsole

The CLI hub. Runs in a K8s pod (`migration-console-0`). Has a core library
(`lib/console_link/console_link/`) with:

- **`models/`** — Domain models for every service (cluster, backfill, replayer, kafka, etc.)
- **`workflow/`** — Workflow management: submit, approve, configure, status, stop
- **`api/`** — REST API exposing console commands as HTTP endpoints
- **`cli.py`** — Click-based CLI entry point

**Config contract:** All services configured via `migration_services.yaml`. Any new
component (including our advisor) would register here.

**REST API endpoints** (`api/`): backfill, clusters, metadata, sessions, snapshot, system.
The advisor could be exposed as an additional API module here.

### 1.4 The "Migration Companion" Vision (PR #2426)

**Source:** https://github.com/opensearch-project/opensearch-migrations/pull/2426

This RFC is the key future-direction doc. Major architectural decisions:

- **"The AI is the interface"** — no separate web UI. The AI reads telemetry and presents
  results conversationally.
- **Three deployment modalities:** Docker container (built-in Claude CLI), AWS CloudShell
  (Bedrock), IDE agent (bring your own AI)
- **Playbook = workflow config** — no separate playbook engine. Playbooks are `.wf.yaml`
  files processed by `orchestrationSpecs/`
- **Three phases:** Assessment (Advisor) → Deployment (EKS + Argo) → Execution (Playbooks)
- **Console becomes backend** — Companion drives Console via API; direct shell = escape hatch

**Why this matters for OSC:** Our Solr advisor maps to the "Assessment (Advisor)" phase.
We should produce output that feeds the Deployment and Execution phases — meaning our
migration report should be translatable into workflow configs.

---

## 2. Upstream Is Actively Adding Solr Support

**This is a coordination risk.** Multiple upstream PRs are adding Solr capabilities:

| PR | What | Author | Status |
|---|---|---|---|
| [#2457](https://github.com/opensearch-project/opensearch-migrations/pull/2457) | Solr cluster detection | AndreKurait | Active |
| [#2448](https://github.com/opensearch-project/opensearch-migrations/pull/2448) | Solr cursor-based backfill | AndreKurait | Active |
| [#2478](https://github.com/opensearch-project/opensearch-migrations/pull/2478) | Solr query translation (Java, AST-based) | nagarajg17 et al | Active |
| [#2477](https://github.com/opensearch-project/opensearch-migrations/pull/2477) | Solr query transformation tests | Various | Active |
| [#2458](https://github.com/opensearch-project/opensearch-migrations/pull/2458) | Solr schema-to-mapping conversion | Various | Active |
| [#2435](https://github.com/opensearch-project/opensearch-migrations/pull/2435) | Solr support infrastructure | AndreKurait | Active |

**Overlap analysis:**

| Capability | OSC (Python, advisory) | Upstream (Java, execution) | Complement or conflict? |
|---|---|---|---|
| Schema conversion | `schema_converter.py` — advisory output | `SolrTransformations/` — pipeline stage | **Complement**: ours advises, theirs executes |
| Query translation | `query_converter.py` — show user the mapping | TrafficCapture AST parser — live transformation | **Complement**: ours explains, theirs transforms at scale |
| Cluster detection | Not implemented | Solr cluster detection PR | **Complement**: theirs discovers, ours advises on findings |
| Data backfill | Not our scope | Cursor-based Solr backfill | **No overlap** |

**Key takeaway:** OSC's advisor and upstream's execution tooling are naturally complementary.
The advisor helps users *understand and plan*; the execution tools *do the migration*. But we
should be aware of their schema/query implementations to avoid contradictory recommendations.

---

## 3. Jeff's Code: Gap Between SKILL.md and Implementation

### What SKILL.md describes vs. what `handle_message()` does

| SKILL.md Step | Described Behavior | Code Reality |
|---|---|---|
| Step 0: Stakeholder ID | Determine user role, tailor all guidance | **Not implemented** |
| Step 1: Schema Acquisition | Obtain and convert Solr schema | Works (detects `<schema>` XML) |
| Step 2: Schema Review | Analyze incompatibilities, categorize | **Not implemented** (`add_incompatibility()` never called) |
| Step 3: Query Translation | Convert with gap documentation | Works (keyword "query"/"translate") |
| Step 4: Solr Customizations | Map handlers, plugins, auth | **Not implemented** |
| Step 5: Cluster Assessment | Sizing recommendations | **Not implemented** |
| Step 6: Client Integration | Library migration, front-end impact | **Not implemented** (`add_client_integration()` never called) |
| Step 7: Migration Report | Comprehensive deliverable | Structure exists, but reports are hollow |

### Module-by-module gaps

**`schema_converter.py`** (working but incomplete):
- No analyzer/tokenizer/filter conversion — just maps field types
- No `copyField` → `copy_to` conversion
- Dynamic field patterns only handle `*_suffix`, not `prefix_*`
- Unknown types silently default to `keyword` (no warning)

**`query_converter.py`** (working but limited):
- No eDismax parameter support (`qf`, `pf`, `mm`, `bq`, `bf`, `tie`)
- No filter query (`fq`) handling
- No facet → aggregation conversion
- No spatial, MLT, spellcheck, highlighting, grouping
- Boolean splitting handles only one operator at a time
- Boost values (`^n`) stripped, not converted

**`report.py`** (structure exists, data doesn't flow in):
- Has all 5 sections from deliverables doc (milestones, blockers, implementation, front-end, cost)
- But `handle_message()` never populates incompatibilities or client integrations
- Reports from real conversations will always be sparse

**`storage.py`** (the strongest module):
- Clean ABC with `StorageBackend`
- `InMemoryStorage` and `FileStorage` both work
- Session state model is well-designed
- Only gap: no S3 or DB backend yet

**`steering/`** docs:
- 5 of 6 files have content (accuracy, incompatibilities, index_design, query_translation, sizing)
- `stakeholders.md` is empty (0 bytes) despite PR #3 being merged for it
- Loaded at init but **never used** anywhere in the code

**`references/`**:
- Contains only `01-sample-reference.md` with placeholder text
- This is where agent99's rich knowledge base should go

---

## 4. Upstream Interfaces OSC Must Understand

### 4.1 `migration_services.yaml` — Service Discovery Contract

Every component registers via this YAML schema. Key sections: `source_cluster`,
`target_cluster`, `backfill`, `snapshot`, `metadata_migration`, `replay`, `kafka`,
`metrics_source`, `client_options`.

**For our advisor:** We'd likely add an `advisor` section here with endpoint URL and
storage config.

### 4.2 Workflow Config DSL — The Execution Contract

Defined by Zod schemas in `orchestrationSpecs/packages/schemas/src/userSchemas.ts`.
This is what users express in `.wf.yaml` files. If our advisor produces executable
plans, they should output this format.

### 4.3 Console REST API — The Integration Surface

`migrationConsole/lib/console_link/console_link/api/` exposes endpoints for backfill,
clusters, metadata, sessions, snapshots, system status. Our advisor could be exposed
as an additional module here, or as a standalone service the console can call.

### 4.4 CRD-Based Signaling — The Approval Contract

`ApprovalGate` CRDs with `status.phase` fields (Pending → Approved → Teardown).
If our advisor participates in approval workflows, it would read/write these CRDs.

### 4.5 Transformer Plugin Interface

`transformation/transformationPlugins/jsonMessageTransformers/jsonMessageTransformerInterface/`
defines how data transformations plug in. Not directly relevant to the advisor, but
any Solr-specific transformations we recommend should reference the existing plugins.

---

## 5. Contribution Standards

**From `CONTRIBUTING.md` and `DEVELOPER_GUIDE.md`:**

- Apache-2.0 license (Jeff's code already matches)
- Python components use `pipenv` and `pytest`
- Java components use Gradle with Spotless formatting
- TypeScript uses Jest, `tsgo` for type checking
- CI: GitHub Actions + Jenkins (weekly releases)
- Pre-commit hooks via `install_githooks.sh`
- Test tiers: `test` (unit), `slowTest`, `isolatedTest`, `fullTest`

**Key contributors to coordinate with:**
- `AndreKurait` — core orchestration + Solr support
- `sumobrian` — config processor + Migration Companion RFC
- `nagarajg17`, `akshay2000`, `k-rooot` — Solr query translation
