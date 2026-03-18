---
name: solr-to-opensearch
displayName: "Solr to OpenSearch Migration Advisor"
description: >
  Expert in migrating Apache Solr collections to OpenSearch indexes. 
  Translates Solr XML/JSON schemas to OpenSearch mappings and converts 
  Solr syntax (Standard, DisMax, eDisMax) into OpenSearch DSL. 
  Provides sizing for nodes, shards, and JVM heap.
  Uses the AWS Knowledge MCP Server for accurate, up-to-date OpenSearch
  and AWS service information.
keywords: 
  - "Solr to OpenSearch"
  - "migrate Solr"
  - "schema.xml to mapping"
  - "solrconfig.xml"
  - "edismax to bool query"
  - "synonyms.txt"
  - "SolrCloud vs OpenSearch Cluster"
  - "OpenSearch best practices"
  - "AWS OpenSearch Service"
  - "OpenSearch regional availability"
metadata:
  author: jzonthemtn
  version: "0.2.0"
  capability: "translation-engine"
---

# Apache Solr to OpenSearch Migration Advisor

An agent skill for migrating from Apache Solr to OpenSearch. This skill provides
a transport-agnostic migration advisor that can reason about Solr query behavior,
configuration, and cluster architecture.

## When to Use

Use this skill when:

- A user needs to migrate a Solr collection or SolrCloud deployment to OpenSearch.
- A user wants a comprehensive migration advisor that can handle conversational
  interaction and maintain session context.
- A user has a `schema.xml` or Solr Schema API JSON document and needs an
  equivalent OpenSearch index mapping.
- A user has Solr query strings and needs them translated to OpenSearch Query DSL.
- A user needs a migration report covering milestones, blockers, and cost estimates.
- A user has questions about Amazon OpenSearch Service features, regional availability, or AWS best practices.

**Trigger phrases:** "migrate from Solr", "convert Solr schema", "translate Solr
query", "Solr to OpenSearch", "migration advisor", "migration report",
"OpenSearch best practices", "AWS OpenSearch Service".

## AWS Knowledge Integration

This skill integrates with the [AWS Knowledge MCP Server](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server/)
(`https://knowledge-mcp.global.api.aws`) to provide accurate, up-to-date information about:

- Amazon OpenSearch Service features and configuration
- OpenSearch regional availability across AWS regions
- AWS best practices for search workloads
- Current AWS documentation and API references

The integration is used automatically when users ask OpenSearch or AWS-specific questions.
Two dedicated MCP tools are also exposed:

- `aws_knowledge_search(query, topic)` — search AWS docs for any AWS/OpenSearch topic
- `aws_opensearch_regional_availability(region)` — check OpenSearch Service regional availability

No AWS account or authentication is required to use the AWS Knowledge MCP Server.

## Migration Workflow

Walk the user through each step in order. Do not skip ahead — complete each step before moving to the next.

### Step 1 — Schema Acquisition

Get the Solr schema that will be the basis for the OpenSearch index mapping. There are two paths:

- **Path A — Existing schema:** Ask the user to paste their `schema.xml` or the JSON response from the Solr Schema API (`GET /solr/<collection>/schema`). Call `convert_schema_xml` or `convert_schema_json` accordingly and show the resulting OpenSearch mapping.
- **Path B — No schema yet:** If the user has no existing Solr schema, ask them to provide a sample JSON document that represents the data they plan to index. Infer field names and types from the JSON structure and generate a starter OpenSearch index mapping. Confirm the inferred types with the user before proceeding.

Once a mapping is agreed upon, save it to the session.

**Optional — Create the index in OpenSearch:** After presenting the mapping, ask the user:
*"Would you like me to create this index in OpenSearch now?"*
Only call `create_opensearch_index` if the user explicitly agrees. Pass the agreed-upon index name and the mapping JSON. If the user declines or does not respond affirmatively, skip this step and move on. Inform the user that `OPENSEARCH_URL`, `OPENSEARCH_USER`, and `OPENSEARCH_PASSWORD` environment variables can be set to point to their cluster (defaults to `http://localhost:9200`).

Move to Step 2.

### Step 2 — Schema Review & Incompatibility Analysis

This step is the primary incompatibility gate. Treat every finding as a potential blocker and be thorough — missed incompatibilities discovered late in a migration are expensive to fix.

Systematically check the converted mapping against every category in the **Incompatibility Reference** section below. For each issue found:

1. Classify it as one of: **Breaking** (will cause data loss or index failure), **Behavioral** (works but produces different results), or **Unsupported** (feature has no OpenSearch equivalent).
2. Record it in the session under `facts.incompatibilities` as a list of objects with keys `category`, `severity`, `description`, and `recommendation`.
3. Present it to the user immediately with a clear explanation and the recommended resolution.

Specific checks to perform on the schema:

- **copyField** — flag every `<copyField>` directive; explain replacement with `copy_to` on the source field definition.
- **Field type gaps** — flag `solr.ICUCollationField`, `solr.EnumField`, `solr.ExternalFileField`, `solr.PreAnalyzedField`, and `solr.SortableTextField` as unsupported or requiring manual workarounds.
- **Custom analyzers** — identify any `<analyzer>`, `<tokenizer>`, or `<filter>` referencing a non-standard class. Check whether an equivalent exists in OpenSearch's built-in analysis chain; flag those that do not.
- **Dynamic fields** — note that OpenSearch `dynamic_templates` match on field name patterns or data types, not Solr's glob syntax; verify the converted templates preserve the intended behavior.
- **Stored vs. source** — Solr stores fields individually; OpenSearch stores the original `_source` document. Fields marked `stored="true"` but `indexed="false"` in Solr may behave differently under `_source` filtering.
- **DocValues** — Solr requires explicit `docValues="true"` for sorting/faceting on most field types; in OpenSearch, `doc_values` is enabled by default for most types. Flag any field where the Solr schema explicitly disables docValues, as the OpenSearch default may change behavior.
- **Nested / child documents** — Solr block join (`{!parent}`, `{!child}`) has no direct equivalent; flag and recommend OpenSearch [nested objects](https://opensearch.org/docs/latest/field-types/supported-field-types/nested/) or [join field type](https://opensearch.org/docs/latest/field-types/supported-field-types/join/).
- **Trie field types** — `TrieIntField`, `TrieLongField`, etc. are deprecated in Solr 7+ and have no equivalent in OpenSearch; confirm the user is migrating to the Point field equivalents.

Present all findings as a prioritized list: Breaking first, then Behavioral, then Unsupported. If no incompatibilities are found, state that explicitly so the user has confidence to proceed.

### Step 3 — Query Translation

Ask the user for representative Solr queries — at minimum one of each type they use in production (standard, dismax/edismax, facet, range, spatial if applicable). For each query:

- Call `convert_query` and show the OpenSearch Query DSL equivalent.
- Actively check for query-level incompatibilities and behavioral differences. For each one found, record it in `facts.incompatibilities` with `category: "query"` before moving on.
- Flag queries that cannot be automatically translated and explain what manual work is needed.

Known query incompatibilities to check for:

| Solr feature | Severity | OpenSearch situation |
|---|---|---|
| eDismax `pf`, `pf2`, `pf3` phrase boost fields | Behavioral | No direct equivalent; approximate with `multi_match` type `phrase` in a `should` clause. |
| eDismax `bq` / `bf` additive boost | Behavioral | Use `function_score` or `script_score`; additive vs. multiplicative semantics differ. |
| `{!join}` cross-collection join | Breaking | Not supported; restructure as nested documents or application-side join. |
| `{!collapse}` field collapsing | Behavioral | Use `collapse` via the [Search API collapse parameter](https://opensearch.org/docs/latest/search-plugins/searching-data/collapse/) — available but syntax differs. |
| Solr Streaming Expressions | Unsupported | No equivalent; move aggregation logic to the application layer or use OpenSearch aggregations. |
| `{!graph}` graph traversal | Unsupported | No equivalent in OpenSearch. |
| Spatial `{!geofilt}` / `{!bbox}` | Behavioral | Use `geo_distance` / `geo_bounding_box` queries; parameter names differ. |
| `MoreLikeThis` handler | Behavioral | Use `more_like_this` query; `mindf`, `mintf` parameter names differ slightly. |
| Facet pivots | Behavioral | Use nested `terms` aggregations; result shape differs. |
| `cursorMark` deep pagination | Behavioral | Use `search_after` in OpenSearch; semantics are similar but not identical. |
| Solr relevance TF-IDF (classic) | Behavioral | OpenSearch defaults to BM25; scores will differ. Configurable via `similarity` setting. |

### Step 4 — Solr Customizations

Ask the user whether they rely on any Solr-specific customizations. Use this prompt:

*"Before we look at infrastructure, I'd like to understand any Solr customizations you're using. Do any of the following apply to your deployment? Please describe what you have for each that's relevant:"*

- **Request handlers** — custom `SearchHandler`, `UpdateRequestHandler`, or other handlers defined in `solrconfig.xml`.
- **Plugins** — custom `QParserPlugin`, `SearchComponent`, `TokenFilterFactory`, `UpdateRequestProcessorChain`, or other plugin types.
- **Authentication & authorization** — Basic Auth, Kerberos, PKI, Rule-Based Authorization Plugin, or a custom security plugin.
- **Operational constraints** — specific SLA requirements, air-gapped environments, compliance requirements (e.g. FIPS, FedRAMP), multi-tenancy needs, or read/write traffic isolation.

For each item the user provides, give a concrete OpenSearch equivalent or migration path:

| Solr customization | OpenSearch equivalent / approach |
|---|---|
| Custom `SearchHandler` | Use the [Search API](https://opensearch.org/docs/latest/api-reference/search/) with a custom request body; complex handler logic moves to the application layer or an ingest pipeline. |
| `UpdateRequestProcessorChain` | Replace with an [Ingest Pipeline](https://opensearch.org/docs/latest/ingest-pipelines/) using built-in or custom processors. |
| Custom `QParserPlugin` | Implement equivalent logic in Query DSL (e.g. `function_score`, `script_score`, `percolate`) or a search pipeline. |
| Custom `TokenFilterFactory` / `CharFilterFactory` | Re-express as a custom [analyzer definition](https://opensearch.org/docs/latest/analyzers/) in the index settings using the equivalent built-in filter, or implement a custom plugin via the OpenSearch plugin SDK. |
| Basic Auth | Use the [OpenSearch Security plugin](https://opensearch.org/docs/latest/security/) (bundled) with internal user database or LDAP/Active Directory backend. |
| Kerberos | OpenSearch Security supports Kerberos via the `kerberos` authentication domain. |
| PKI / mutual TLS | Configure node-to-node and client TLS in `opensearch.yml`; the Security plugin handles certificate-based auth. |
| Rule-Based Authorization Plugin | Map to OpenSearch Security [roles and role mappings](https://opensearch.org/docs/latest/security/access-control/). |
| Air-gapped / offline deployment | OpenSearch supports fully offline installation; use the tarball or RPM/DEB packages and mirror the plugin registry internally. |
| FIPS 140-2 compliance | OpenSearch provides a [FIPS-compliant distribution](https://opensearch.org/docs/latest/install-and-configure/install-opensearch/fips/). |
| Multi-tenancy | Use OpenSearch Security [tenants](https://opensearch.org/docs/latest/security/multi-tenancy/) for Dashboards isolation, and index-level permissions for data isolation. |
| Read/write traffic isolation | Route via separate [coordinating-only nodes](https://opensearch.org/docs/latest/tuning-your-cluster/cluster-formation/cluster-manager/) or use a load balancer with separate pools. |

If the user mentions a customization not in the table above, reason about the closest OpenSearch equivalent and flag it as a manual migration item.

Store all identified customizations and their OpenSearch mappings in the session under `facts.customizations` so they are included in the migration report.

### Step 5 — Cluster & Infrastructure Assessment

Ask the user about their current deployment topology:

- Standalone Solr or SolrCloud? Number of nodes, shards, and replicas?
- Approximate document count and index size?
- Peak query throughput and indexing rate?

Use the sizing steering document to provide OpenSearch cluster sizing recommendations (node count, instance types, shard strategy).

### Step 6 — Client & Front-end Integration

Ask the user what client-side code talks to Solr today. Use these prompts:

- *"What client libraries are you using — SolrJ, pysolr, a custom HTTP client, or something else?"*
- *"Do you have a front-end search UI (e.g. Solr-specific widgets, Velocity templates, or a custom React/Vue app)?"*
- *"Are there any other systems or services that make direct HTTP calls to Solr's `/select`, `/update`, or admin endpoints?"*

For each integration the user describes, record it in the session via `SessionState.add_client_integration` with:

| Field | What to capture |
|---|---|
| `name` | The library, framework, or component name (e.g. "SolrJ", "pysolr", "React Search UI") |
| `kind` | One of: `library`, `ui`, `http`, `other` |
| `notes` | How it is currently used (endpoints called, features relied on) |
| `migration_action` | The concrete change required for OpenSearch |

Use the table below to guide the migration action for common integrations:

| Solr client / UI | Kind | Migration action |
|---|---|---|
| SolrJ | library | Replace with [opensearch-java](https://github.com/opensearch-project/opensearch-java); update endpoint URLs and request/response models. |
| pysolr | library | Replace with [opensearch-py](https://github.com/opensearch-project/opensearch-py); update query construction and response parsing. |
| solr-ruby / rsolr | library | Replace with [opensearch-ruby](https://github.com/opensearch-project/opensearch-ruby). |
| Custom HTTP client | http | Update base URL from `/solr/<collection>/select` to `/<index>/_search`; migrate request body to Query DSL JSON. |
| Solr Admin UI | ui | Migrate to [OpenSearch Dashboards](https://opensearch.org/docs/latest/dashboards/); index management, query dev tools, and monitoring are all available. |
| Velocity / Solr response writer templates | ui | Remove; OpenSearch returns JSON natively — render in the application layer. |
| React/Vue/Angular with Solr-specific widgets | ui | Replace Solr-specific components with OpenSearch-compatible equivalents or generic REST-based components. |
| Solr SolrJ CloudSolrClient (SolrCloud) | library | Replace with OpenSearch client pointed at the cluster load balancer; no ZooKeeper dependency. |

If the user describes an integration not in the table, reason about the endpoint and request/response shape changes needed and provide a concrete before/after example.

Identify any authentication changes required (e.g. moving from Solr Basic Auth to OpenSearch Security headers) and note them in `migration_action`.

### Step 7 — Migration Report

Call `generate_report` to produce the final report. The report must cover:

- **Incompatibilities** (prominent, dedicated section at the top) — every item collected in `facts.incompatibilities` across all steps, grouped by severity: Breaking → Unsupported → Behavioral. Each entry must include the category, description, and recommended resolution. Breaking and Unsupported items are also surfaced as explicit blockers.
- **Client & Front-end Impact** — every `ClientIntegration` recorded in Step 6, grouped by kind (libraries, UI, HTTP clients). Each entry shows the current usage and the concrete migration action required. If no integrations were recorded, state that explicitly.
- Major milestones and suggested sequencing.
- Blockers surfaced in Steps 2–6.
- Implementation points with enough detail for an engineer to act on.
- Cost estimates for infrastructure, effort, and any required tooling changes.

Present the report to the user and offer to drill into any section.

## Resuming a Conversation

Migration plans can span weeks or months, and conversations may be restarted many times. All session state — schema mappings, incompatibilities, query translations, client integrations, and workflow progress — is persisted automatically after every turn using the `session_id` you provide.

### How to resume

When starting a new conversation, pass the same `session_id` you used previously:

```python
# Resume an existing session — all prior context is restored automatically
response = skill.handle_message("Let's continue the migration", session_id="my-project-migration")
```

Via MCP:
```json
{ "tool": "handle_message", "arguments": { "message": "Let's continue", "session_id": "my-project-migration" } }
```

The advisor will reload the full `SessionState` (history, facts, progress, incompatibilities, client integrations) and pick up exactly where you left off.

### Choosing a session ID

Use a stable, meaningful identifier tied to your project — not a random UUID — so it is easy to recall across restarts:

- `acme-solr-migration`
- `projectname-prod-cluster`
- `team-search-migration-2025`

### Listing and inspecting existing sessions

```python
from scripts.storage import FileStorage

storage = FileStorage("sessions")

# List all saved sessions
print(storage.list_sessions())

# Inspect a specific session
state = storage.load("my-project-migration")
print(f"Progress: Step {state.progress}")
print(f"Incompatibilities found: {len(state.incompatibilities)}")
print(f"Facts: {state.facts}")
```

### Session files

With the default `FileStorage` backend, each session is stored as a JSON file at `sessions/<session_id>.json`. You can back these up, copy them between machines, or inspect them directly. The file is human-readable and contains the full conversation history, all discovered facts, and migration progress.

### Starting fresh

To reset a session and start over:

```python
storage.delete("my-project-migration")
```

Or simply use a new `session_id`.

---

## Reference Knowledge Base

You have access to a verified knowledge base of technical information about Apache Solr and OpenSearch located under the `references` directory. Before answering any questions, search the provided context and cite your sources from the reference materials.

#[[file:references/01-sample-reference.md]]

## Instructions

- Always maintain the session context using the `session_id`. Every call loads the full `SessionState` (history, facts, progress, incompatibilities) and saves it back before returning — sessions are fully resumable across restarts.
- Follow the steps in order. If the user jumps ahead, acknowledge their input, store it in the session, and guide them back to complete any skipped steps.
- If a user asks for migration advice but hasn't provided technical details, proactively request the Solr schema or a sample JSON document (Step 1).
- Use the steering documents (Query Translation, Index Design, Sizing, Incompatibilities) to inform all reasoning.
- **Incompatibility tracking is mandatory.** Every incompatibility found in any step must be recorded in `facts.incompatibilities` (via `SessionState.add_incompatibility`) before moving on. Never silently skip a known issue.
- When in doubt about whether something is an incompatibility, flag it conservatively — a false positive is far less harmful than a missed breaking change.

### Session State Fields

The `SessionState` object persisted for each session contains:

| Field | Type | Purpose |
|---|---|---|
| `session_id` | `str` | Unique session identifier |
| `history` | `list[{user, assistant}]` | Full conversation turns |
| `facts` | `dict` | Discovered migration facts (e.g. `schema_migrated`, `customizations`) |
| `progress` | `int` | Current workflow step (0 = not started; advances forward only) |
| `incompatibilities` | `list[Incompatibility]` | All incompatibilities found, with `category`, `severity`, `description`, `recommendation` |
| `client_integrations` | `list[ClientIntegration]` | Client-side and front-end integrations collected in Step 6, with `name`, `kind`, `notes`, `migration_action` |

### Pluggable Storage Backends

The storage backend is injected at construction time. Built-in options:

- `InMemoryStorage` — ephemeral, process-scoped; useful for tests and single-turn use.
- `FileStorage(base_path)` — JSON file per session on disk; the default for persistent deployments.

Custom backends implement `StorageBackend` (four methods: `_save_raw`, `_load_raw`, `delete`, `list_sessions`) and are drop-in replacements with no changes to skill logic.

### Usage

#### Library Usage
```python
import sys
import os
# Add scripts directory to sys.path
sys.path.append(os.path.join(os.getcwd(), ".kiro/skills/solr-to-opensearch/scripts"))

from skill import SolrToOpenSearchMigrationSkill

# Initialize advisor
skill = SolrToOpenSearchMigrationSkill()

# Handle conversational message
session_id = "user-123"
response = skill.handle_message("Help me migrate my Solr schema: <schema>...</schema>", session_id)
print(response)

# Generate final report
report = skill.generate_report(session_id)
print(report)
```

#### MCP Server Usage
Install dependencies and run the MCP server over stdio:
```bash
pip install -e ".kiro/skills/solr-to-opensearch[mcp]"
python .kiro/skills/solr-to-opensearch/scripts/mcp_server.py
```

Or configure it in your MCP client (e.g. `.kiro/settings/mcp.json`):
```json
{
  "mcpServers": {
    "solr-to-opensearch": {
      "command": "python3",
      "args": [".kiro/skills/solr-to-opensearch/scripts/mcp_server.py"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Reference Data

### Field Type Mapping Reference
| Solr Field Type | OpenSearch Type |
|---|---|
| TextField | text |
| StrField | keyword |
| IntPointField / TrieIntField | integer |
| LongPointField / TrieLongField | long |
| FloatPointField / TrieFloatField | float |
| DoublePointField / TrieDoubleField | double |
| DatePointField / TrieDateField | date |
| BoolField | boolean |
| BinaryField | binary |
| LatLonPointSpatialField | geo_point |
| SpatialRecursivePrefixTreeFieldType | geo_shape |
