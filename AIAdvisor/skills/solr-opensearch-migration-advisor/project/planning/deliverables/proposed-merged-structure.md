# Proposed Merged Structure: Eric's Skeleton + Jeff's Code + Agent99 Knowledge

Generated 2026-03-22.

## Design Principles

1. **Follow opensearch-launchpad layout** — `skills/`, `kiro/`, `cursor/`, `tests/` as siblings
2. **Two skills** — engine-agnostic `migration-planner` + engine-specific `solr` (Eric's idea)
3. **Preserve Jeff's working code** — refactor location, not logic
4. **Port agent99's knowledge base** — references and steering fill the content gaps
5. **agentskills.io compliance** — hyphenated directory names, SKILL.md in each skill

---

## Proposed Directory Tree

```
AIAdvisor/
├── README.md                              overview, how to install, how to contribute
├── pyproject.toml                         single Python package for all skills
│
├── cursor/                                Cursor IDE plugin config
│   ├── .cursor-plugin/
│   │   ├── marketplace.json
│   │   └── plugin.json
│   └── plugins/solr-to-opensearch-migration/
│       ├── README.md
│       └── skills -> ../../skills/        symlink to skills dir
│
├── kiro/                                  Kiro Power configs
│   ├── migration-planner/
│   │   ├── POWER.md
│   │   ├── mcp.json                       points to MCP server
│   │   └── steering -> ../../skills/migration-planner/steering/
│   └── solr/
│       ├── POWER.md
│       ├── mcp.json
│       └── steering -> ../../skills/solr/steering/
│
├── skills/
│   ├── migration-planner/                 ENGINE-AGNOSTIC migration methodology
│   │   ├── SKILL.md                       agentskills.io format
│   │   ├── scripts/
│   │   │   ├── __init__.py
│   │   │   ├── skill.py                   ← from Jeff: workflow orchestration,
│   │   │   │                                handle_message() routing, stakeholder ID,
│   │   │   │                                report generation coordination
│   │   │   ├── report.py                  ← from Jeff: report generation (engine-agnostic structure)
│   │   │   └── storage.py                 ← from Jeff: session persistence (ABC + backends)
│   │   ├── steering/
│   │   │   ├── accuracy.md                ← from Jeff: correctness-first principles
│   │   │   ├── stakeholders.md            ← from Jeff: stakeholder identification
│   │   │   └── migration_execution.md     ← from Jeff: execution methodology
│   │   └── references/
│   │       ├── 01-strategic-guidance.md   ← from agent99: when/why/when-not to migrate
│   │       ├── 04-migration-execution.md  ← from agent99: dual-write, cutover, pipelines
│   │       ├── 05-validation-cutover.md   ← from agent99: relevance validation, go/no-go
│   │       ├── 06-operations.md           ← from agent99: monitoring, ISM, DR
│   │       ├── 09-approval-and-safety-tiers.md  ← from agent99: observe/propose/execute
│   │       ├── 10-playbook-artifact-and-review.md  ← from agent99: governance artifacts
│   │       ├── aws-opensearch-service.md  ← from agent99: AWS sizing, auth, cost
│   │       ├── consulting-methodology.md  ← from agent99: OSC process, roles, reporting
│   │       ├── consulting-concerns-inventory.md  ← from agent99: 200-item risk matrix
│   │       ├── migration-strategy.md      ← from agent99: strategy, decision trees
│   │       ├── roles-and-escalation-patterns.md  ← from agent99: team shape, escalation
│   │       └── sample-catalog.md          ← from agent99: sample datasets
│   │
│   └── solr/                              SOLR-SPECIFIC migration knowledge
│       ├── SKILL.md                       agentskills.io format
│       ├── scripts/
│       │   ├── __init__.py
│       │   ├── schema_converter.py        ← from Jeff: schema.xml/JSON → OS mappings
│       │   └── query_converter.py         ← from Jeff: Solr query → Query DSL
│       ├── steering/
│       │   ├── incompatibilities.md       ← from Jeff: Solr/OS feature gaps
│       │   ├── index_design.md            ← from Jeff: schema mapping guidance
│       │   ├── query_translation.md       ← from Jeff: query conversion guidance
│       │   ├── sizing.md                  ← from Jeff: cluster sizing heuristics
│       │   └── operations.md              ← from Jeff: Solr-specific ops concerns
│       └── references/
│           ├── 02-pre-migration.md        ← from agent99: auditing Solr deployments
│           ├── 03-target-design.md        ← from agent99: designing OS solution
│           ├── 07-platform-integration.md ← from agent99: Spring Boot, Python, Drupal
│           ├── 08-edge-cases-and-gotchas.md  ← from agent99: long-tail Solr issues
│           ├── solr-concepts-reference.md ← from agent99: feature audit, equivalence map
│           └── scenario-drupal.md         ← from agent99: Drupal Search API scenario
│
├── mcp/                                   MCP SERVER (top-level adapter)
│   ├── __init__.py
│   └── server.py                          ← from Jeff: mcp_server.py, wraps BOTH skills
│                                            exposes all tools from both migration-planner
│                                            and solr skills as a single MCP endpoint
│
└── tests/
    ├── unit/
    │   ├── test_skill.py                  ← from Jeff: adapted for new imports
    │   ├── test_storage.py                ← from Jeff
    │   ├── test_report.py                 ← from Jeff
    │   ├── test_schema_converter.py       ← from Jeff
    │   ├── test_query_converter.py        ← from Jeff
    │   └── test_mcp_server.py             ← from Jeff
    └── integration/                       future: end-to-end tests
```

---

## How Jeff's Code Splits

### → `skills/migration-planner/scripts/`

| File | Rationale |
|------|-----------|
| `skill.py` | The facade/workflow orchestrator. handle_message() routing, session management, stakeholder ID, steering doc loading — all engine-agnostic concerns. Engine-specific logic (schema/query conversion) becomes calls to the solr skill. |
| `report.py` | Report structure (milestones, blockers, implementation points, cost) is engine-agnostic. Engine-specific data (incompatibilities, conversion results) is fed in from session state. |
| `storage.py` | Session persistence is entirely engine-agnostic. The ABC + FileStorage + InMemoryStorage all live here. |

### → `skills/solr/scripts/`

| File | Rationale |
|------|-----------|
| `schema_converter.py` | 100% Solr-specific. Parses schema.xml and Solr Schema API JSON. |
| `query_converter.py` | 100% Solr-specific. Translates Solr query syntax. |

### → `mcp/server.py`

| File | Rationale |
|------|-----------|
| `mcp_server.py` | Transport adapter — imports from both skills, registers all tools as one MCP endpoint. Not a skill itself. Lives outside `skills/` because it's a deployment adapter. |

### The integration question

`skill.py` currently imports `SchemaConverter`, `QueryConverter`, and `StorageBackend`
directly. After the split:

```python
# skills/migration-planner/scripts/skill.py
from skills.solr.scripts.schema_converter import SchemaConverter
from skills.solr.scripts.query_converter import QueryConverter
# or via a plugin/registry pattern for future engine support
```

A cleaner approach for future multi-engine support:

```python
# skill.py discovers engine skills via entry points or a registry
class MigrationSkill:
    def __init__(self, engine_skill, storage_backend=None):
        self.engine = engine_skill  # e.g. SolrSkill instance
        self.storage = storage_backend or FileStorage()
```

This way, adding `skills/elasticsearch/` later just means registering a new engine skill.

---

## How Agent99 References Map

### → `skills/migration-planner/references/` (engine-agnostic)

| Agent99 file | Why it's engine-agnostic |
|---|---|
| `01-strategic-guidance.md` | When/why to migrate — applies to any search engine |
| `04-migration-execution.md` | Dual-write, cutover, pipelines — generic patterns |
| `05-validation-cutover.md` | Relevance validation, judgment sets, go/no-go — methodology |
| `06-operations.md` | Monitoring, ISM, DR — target-side (OpenSearch) concerns |
| `09-approval-and-safety-tiers.md` | Governance model — not engine-specific |
| `10-playbook-artifact-and-review.md` | Artifact structure, approval gates |
| `aws-opensearch-service.md` | AWS target-side configuration |
| `consulting-methodology.md` | OSC process and principles |
| `consulting-concerns-inventory.md` | Risk matrix (mostly engine-agnostic) |
| `migration-strategy.md` | Decision trees, ETL patterns |
| `roles-and-escalation-patterns.md` | Team shape, escalation triggers |
| `sample-catalog.md` | Sample datasets |

### → `skills/solr/references/` (Solr-specific)

| Agent99 file | Why it's Solr-specific |
|---|---|
| `02-pre-migration.md` | Auditing a *Solr* deployment specifically |
| `03-target-design.md` | Mapping *Solr* schemas to OpenSearch |
| `07-platform-integration.md` | SolrJ, pysolr, Drupal Search API Solr |
| `08-edge-cases-and-gotchas.md` | Solr-specific pitfalls and no-equivalents |
| `solr-concepts-reference.md` | Solr feature audit, equivalence map |
| `scenario-drupal.md` | Drupal Search API Solr scenario |

---

## What Needs New SKILL.md Files

### `skills/migration-planner/SKILL.md`

New file. Should cover:
- Migration phases (the 5-phase timeline from agent99's SKILL.md)
- Workflow steps 0 (stakeholder ID), 4 (customizations), 5 (cluster assessment), 6 (client integration), 7 (report)
- Question sets and intake methodology
- Report structure specification
- Engine-agnostic trigger patterns ("migration planning", "migration report", "what are the phases")

### `skills/solr/SKILL.md`

Derived from Jeff's existing SKILL.md, scoped down to:
- Solr-specific trigger patterns ("solr schema", "solr query", "dismax", "edismax")
- Schema translation quick-reference tables
- Query translation quick-reference tables
- Incompatibility catalog
- Solr feature audit and equivalence map
- Steps 1 (schema), 2 (review), 3 (query) from Jeff's workflow

---

## Open Questions for Eric and Jeff

1. **Should `skill.py` live in migration-planner or at the top level?** It orchestrates
   both skills. If it's in migration-planner, the solr skill becomes a dependency. If
   it's at the top level (e.g., `mcp/`), both skills are peers.

2. **Plugin/registry pattern or direct imports?** Direct imports are simpler now. A
   registry is cleaner for future engines but adds complexity. Recommendation: direct
   imports now, refactor when a second engine is added.

3. **Single pyproject.toml or per-skill?** Launchpad uses one top-level pyproject.toml.
   That's simpler for packaging and dependency management. Recommend: one `AIAdvisor/pyproject.toml`.

4. **Where do Jeff's steering/ docs go vs agent99 references/?** Jeff's steering docs
   are shorter, more operational. Agent99's references are longer, more comprehensive.
   They could coexist (steering = quick guidance, references = deep knowledge) or
   agent99's could replace Jeff's. Recommend: keep both — steering for SKILL.md-level
   quick patterns, references for deep dives.

5. **Naming: `solr` or `solr-to-opensearch`?** The skill is specifically about migrating
   *from* Solr *to* OpenSearch, not about Solr in general. `solr-to-opensearch` is more
   precise but longer. Eric's stub uses just `solr`.
