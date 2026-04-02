# Gap Closure Plan: SKILL.md ↔ Code

Generated 2026-03-22. Updated 2026-03-22 with hybrid architecture decision.

Deep analysis of Jeff's code vs SKILL.md promises.

**The core issue:** SKILL.md describes a guided 8-step migration advisor. The code is a
reactive keyword router. Closing this gap IS the product work.

---

## Architecture Decision: Hybrid (Protocol-Agnostic + LLM-Enhanced)

Amazon's requirement is explicit: the advisor must be **protocol agnostic**. From the
upstream "Migration Companion" vision (PR #2426), three deployment modes must work:

1. **Docker container** (built-in Claude CLI)
2. **AWS CloudShell** (Bedrock)
3. **IDE agent** (bring your own AI — Kiro, Cursor, etc.)

This means the core Python library MUST work without an LLM present. But the *primary*
interface IS an LLM. The upstream `kiro-cli/` agent config confirms this: steering docs
as resources, tools as capabilities, the LLM drives the flow.

### The Hybrid Model

```
┌─────────────────────────────────────────────────────────┐
│  LLM Path (Kiro/MCP/Bedrock)                           │
│  ┌─────────────┐    ┌──────────────────────────────┐    │
│  │  SKILL.md   │───▶│  LLM orchestrates tools:     │    │
│  │  (steering) │    │  convert_schema()            │    │
│  └─────────────┘    │  convert_query()             │    │
│                     │  record_incompatibility()    │    │
│                     │  assess_sizing()             │    │
│                     │  generate_report()           │    │
│                     │  get_session_summary()       │    │
│                     └──────────┬───────────────────┘    │
│                                │                        │
├────────────────────────────────┼────────────────────────┤
│  Python Core (protocol-agnostic)                        │
│                                ▼                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  handle_message(message, session_id) → str       │   │
│  │  ─ state machine for guided workflow             │   │
│  │  ─ always handles direct tool requests           │   │
│  │  ─ the "floor" experience for non-LLM clients   │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ schema_     │ │ query_      │ │ report.py       │   │
│  │ converter   │ │ converter   │ │ (generation)    │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
│  ┌─────────────────────────────────────────────────┐    │
│  │  storage.py (pluggable: file, memory, S3, DB)   │   │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │  session state (shared contract — both paths    │    │
│  │  read/write the same facts, incompatibilities,  │    │
│  │  progress, client_integrations)                 │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### What each path provides

| Concern | Python core (`handle_message`) | LLM path (SKILL.md + tools) |
|---------|-------------------------------|----------------------------|
| Conversation flow | State machine — reasonable guided flow | LLM — natural, adaptive conversation |
| Intent understanding | Keyword matching + state context | Full NLU — understands ambiguity |
| Domain tools | Direct calls to converters, report | Tool calls orchestrated by LLM |
| Session state | Read/write via storage API | Same read/write via MCP session tools |
| Steering knowledge | Loaded but used as static reference | Loaded as LLM context — deeply integrated |
| Quality ceiling | Predictable but rigid | High but variable |

### Key principle: session state is the shared contract

Both paths read and write the same `SessionState` object:
- `facts` — discovered migration details (stakeholder role, cluster topology, etc.)
- `incompatibilities` — flagged issues from conversion + assessment
- `client_integrations` — consuming apps and libraries
- `progress` — current workflow step
- `history` — conversation turns

This means a user could start with `handle_message()` via CLI, then switch to
an LLM-powered IDE, and all prior findings carry over.

### MCP tool surface (for LLM path)

```
Core tools (deterministic, tested):
  convert_schema(schema_xml_or_json) → ConversionResult
  convert_query(params) → ConversionResult
  assess_sizing(topology) → SizingResult
  generate_report(session_id) → Markdown

Session tools (state management):
  record_fact(session_id, key, value)
  record_incompatibility(session_id, category, description, recommendation)
  record_client_integration(session_id, name, kind, notes)
  get_session_summary(session_id) → current facts, progress, findings

Reference tools (knowledge retrieval):
  get_migration_checklist()
  get_field_type_reference()
  get_incompatibility_catalog(category?)
```

---

## Current State: What Works

| Component | Status | Notes |
|-----------|--------|-------|
| `storage.py` | **Solid** | Clean ABC, FileStorage + InMemoryStorage, good tests |
| `mcp_server.py` | **Solid** | 10 tools registered, clean pass-through to skill |
| `schema_converter.py` | **Prototype** | 15 field types mapped; no analyzers, no copyField, no incompatibility reporting |
| `query_converter.py` | **Prototype** | 12 patterns handled; no eDisMax, no fq, silent fallback, boosts stripped |
| `skill.py` | **Scaffold** | Keyword router, session management works, steering loaded but unused |
| `report.py` | **Scaffold** | Structure exists, data population methods exist but are never called |

## Additional Planning Gaps Exposed By Launchpad

The OpenSearch Launchpad docs make a few process assumptions explicit that this plan has
mostly treated as background context. They should be tracked as first-class gaps here too.

### Gap A: Supported operating modes are under-specified

We currently talk about the repo as if it were one thing, but it is really four:

- skill/reference guidance
- deterministic Python core
- MCP tool surface
- consultant-facing artifact workflow

That split is real and healthy, but it needs to be documented in process and release docs so
we stop mixing "content completion" with "runtime readiness".

### Gap B: Phase contracts are implied more than defined

The repo has the ingredients for a phase-based migration workflow, but we do not yet define
phase entry criteria, exit criteria, and required artifacts sharply enough.

What needs to become explicit:

- what closes intake
- what closes assessment
- what makes a design "reviewable"
- what makes a plan "ready for implementation"
- what makes a cutover artifact set "approval-ready"

### Gap C: Manual fallback behavior needs to be designed, not improvised

The hybrid model already assumes the Python core must work without an LLM. We should extend
that thinking:

- if MCP/tooling is absent, what exact floor experience do we still promise?
- if live eval scoring is unavailable, what exact review artifact do we still produce?
- if AWS/deployment facts are missing, what exact gap output do we emit?

Those are product questions, not only documentation questions.

### Gap D: Evaluation should increasingly consume real evidence

The newer eval scaffolding is useful, but the long-term target should be closer to an
evidence-backed evaluation flow:

- generated report/artifact output
- scenario-specific expectations
- optional live judge scoring
- explicit manual review for promotion and disputed judgments

That should influence both the test roadmap and the artifact roadmap.

---

## Gap 1: Conversational Workflow (the big one)

### Problem
`handle_message()` matches keywords and reacts. It never:
- Greets the user or asks who they are (Step 0)
- Prompts for schema input (Step 1)
- Reviews conversion results with the user (Step 2)
- Asks about customizations (Step 4)
- Asks about infrastructure (Step 5)
- Asks about client integrations (Step 6)

### What needs to change
The keyword router needs to become a **state machine** that tracks where the user is
in the workflow and proactively guides them. This is the "floor" experience — it must
work without an LLM. When an LLM is present, it can bypass this and call tools directly.

### Proposed approach: Lightweight state machine

```python
# Workflow states
STATES = [
    "greeting",          # → Step 0: identify stakeholder
    "schema_intake",     # → Step 1: acquire schema
    "schema_review",     # → Step 2: review conversion + flag incompatibilities
    "query_intake",      # → Step 3: acquire queries
    "customization",     # → Step 4: discover custom handlers, plugins, auth
    "infrastructure",    # → Step 5: cluster topology, sizing
    "integration",       # → Step 6: client libraries, UI frameworks
    "report",            # → Step 7: generate final report
]
```

**Key design decision:** The state machine should be *suggestive, not enforcing*. If a
user sends a schema XML at any point, convert it — don't say "we're not at that step
yet." But if the user says "help me migrate from Solr," guide them through the steps.

### Implementation sketch

```python
def handle_message(self, message: str, session_id: str) -> str:
    state = self._load_session(session_id)

    # Always handle direct tool requests regardless of state
    if self._is_schema_input(message):
        return self._handle_schema(message, state)
    if self._is_query_input(message):
        return self._handle_query(message, state)
    if "report" in message.lower():
        return self.generate_report(session_id)

    # Otherwise, advance the guided workflow
    current_step = state.get_fact("workflow_step", "greeting")
    handler = getattr(self, f"_step_{current_step}", self._step_greeting)
    response = handler(message, state)

    state.append_turn(message, response)
    self._save_session(state)
    return response
```

Each step handler:
1. Processes the user's response to the previous step's question
2. Records findings in session state
3. Returns guidance + the next question

### Effort estimate
This is the largest single piece of work. Each step handler is ~30-50 lines.
Total: ~300-400 lines of new code in skill.py.

### Priority: **MUST HAVE for RC**
Without this, the product is "converter tools" not "migration advisor."

---

## Gap 2: Incompatibility Detection & Reporting

### Problem
Both converters silently drop what they can't handle:
- Unknown field types → default to `keyword` (no warning)
- Analyzers → completely ignored (no warning)
- Boosts in queries → stripped (no warning)
- Unsupported query patterns → fall back to `query_string` (no warning)

Session methods `add_incompatibility()` and `add_client_integration()` exist in
storage.py but are **never called** from skill.py or the converters.

### What needs to change

**A. Converters return structured results, not just output:**

```python
@dataclass
class ConversionResult:
    output: dict                    # The converted mapping or query DSL
    warnings: list[str]             # Human-readable warnings
    incompatibilities: list[dict]   # Structured: {category, feature, severity, recommendation}
    confidence: float               # 0.0-1.0 — how much of the input was handled
```

**B. skill.py records incompatibilities in session:**

```python
def _handle_schema(self, message, state):
    result = self._schema_converter.convert(schema_xml)
    for incompat in result.incompatibilities:
        state.add_incompatibility(
            category=incompat["severity"],  # Breaking/Behavioral/Unsupported
            description=incompat["feature"],
            recommendation=incompat["recommendation"]
        )
    # Return conversion output + warnings to user
```

**C. Report pulls from populated session state** (already wired, just needs data)

### Specific incompatibilities to detect

**Schema converter should flag:**
- Analyzer chains present but not converted (Breaking — affects relevance)
- copyField directives present but not converted (Behavioral)
- multiValued fields (Behavioral — OpenSearch handles differently)
- Custom field types not in mapping table (Unsupported)
- Dynamic field patterns beyond `*_` prefix (Behavioral — silently dropped)
- Trie* fields (Behavioral — deprecated in Solr, semantically different)
- Nested document fields (Breaking — different model in OpenSearch)
- Custom similarity models (Behavioral — BM25 vs TF-IDF)

**Query converter should flag:**
- Boost values stripped (Behavioral — relevance regression)
- Fuzzy queries falling back to query_string (Behavioral)
- Function queries not converted (Breaking)
- Proximity queries not converted (Behavioral)
- eDisMax parameters not handled (Breaking — most Solr queries use these)
- Streaming expressions (Breaking — no equivalent)
- Graph traversal (Breaking — no equivalent)
- XCJF/join queries (Breaking — different model)
- Payload scoring (Breaking — no equivalent)

### Effort estimate
~150 lines per converter (detection logic + result structure).
~50 lines in skill.py to wire results to session.

### Priority: **MUST HAVE for RC**
Without this, the "advisor" gives advice that silently drops critical information.

---

## Gap 3: Schema Converter — Analyzer Chains

### Problem
Analyzer conversion is **the most important missing feature**. Solr's analyzer chains
(tokenizer + filter pipeline) are what make search work. Dropping them means the
converted index will tokenize differently, producing different search results.

### What a Solr analyzer chain looks like
```xml
<fieldType name="text_general" class="solr.TextField">
  <analyzer type="index">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.StopFilterFactory" words="stopwords.txt"/>
    <filter class="solr.LowerCaseFilterFactory"/>
  </analyzer>
  <analyzer type="query">
    <tokenizer class="solr.StandardTokenizerFactory"/>
    <filter class="solr.StopFilterFactory" words="stopwords.txt"/>
    <filter class="solr.SynonymGraphFilterFactory" synonyms="synonyms.txt"/>
    <filter class="solr.LowerCaseFilterFactory"/>
  </analyzer>
</fieldType>
```

### What the OpenSearch equivalent looks like
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "text_general_index": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["stop", "lowercase"]
        },
        "text_general_query": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["stop", "synonym_graph", "lowercase"]
        }
      },
      "filter": {
        "synonym_graph": {
          "type": "synonym_graph",
          "synonyms_path": "synonyms.txt"
        }
      }
    }
  }
}
```

### Tokenizer mapping table (core set for RC)

| Solr Tokenizer | OpenSearch Tokenizer | Notes |
|----------------|---------------------|-------|
| `StandardTokenizerFactory` | `standard` | Direct equivalent |
| `WhitespaceTokenizerFactory` | `whitespace` | Direct equivalent |
| `KeywordTokenizerFactory` | `keyword` | Direct equivalent |
| `LetterTokenizerFactory` | `letter` | Direct equivalent |
| `ClassicTokenizerFactory` | `classic` | Direct equivalent |
| `PatternTokenizerFactory` | `pattern` | Check regex syntax |
| `UAX29URLEmailTokenizerFactory` | `uax_url_email` | Direct equivalent |
| `PathHierarchyTokenizerFactory` | `path_hierarchy` | Direct equivalent |
| `ICUTokenizerFactory` | `icu_tokenizer` | Requires ICU plugin |

### Filter mapping table (core set for RC)

| Solr Filter | OpenSearch Filter | Notes |
|-------------|-------------------|-------|
| `LowerCaseFilterFactory` | `lowercase` | Direct |
| `StopFilterFactory` | `stop` | Check stopwords file path |
| `SynonymGraphFilterFactory` | `synonym_graph` | Check synonyms file format |
| `SynonymFilterFactory` | `synonym` | Deprecated in both; flag it |
| `PorterStemFilterFactory` | `porter_stem` | Direct |
| `SnowballPorterFilterFactory` | `snowball` | Map language param |
| `KStemFilterFactory` | `kstem` | Direct |
| `WordDelimiterGraphFilterFactory` | `word_delimiter_graph` | Check all params |
| `WordDelimiterFilterFactory` | `word_delimiter` | Deprecated; suggest graph version |
| `ASCIIFoldingFilterFactory` | `asciifolding` | Direct |
| `TrimFilterFactory` | `trim` | Direct |
| `PatternReplaceFilterFactory` | `pattern_replace` | Check regex |
| `LengthFilterFactory` | `length` | Direct |
| `NGramFilterFactory` | `ngram` | Check min/max params |
| `EdgeNGramFilterFactory` | `edge_ngram` | Check min/max/side params |
| `ICUFoldingFilterFactory` | `icu_folding` | Requires ICU plugin |
| `ElisionFilterFactory` | `elision` | Direct |
| `HunspellStemFilterFactory` | `hunspell` | Check dict paths |

### Filters with NO direct equivalent (flag as incompatibility)

| Solr Filter | Situation |
|-------------|-----------|
| `PhoneticFilterFactory` | OpenSearch has `phonetic` but needs plugin; params differ |
| `ReversedWildcardFilterFactory` | No equivalent; used for leading wildcard optimization |
| `CollationKeyFilterFactory` | No equivalent; use ICU collation instead |
| `ManagedSynonymGraphFilterFactory` | No equivalent; managed resources don't exist in OpenSearch |
| `ManagedStopFilterFactory` | No equivalent; use file-based stop filter |

### Effort estimate
~200-300 lines for tokenizer/filter mapping + chain construction.
The mapping tables above are the knowledge base input; the code walks the XML
and builds the analysis block.

### Priority: **HIGH for RC**
This is what separates "toy converter" from "useful tool." A migration that gets
analyzers wrong will produce different search results — the #1 thing users care about.

---

## Gap 4: Query Converter — eDisMax & Filter Queries

### Problem
Most production Solr deployments use eDisMax as their default query parser. The
converter doesn't handle any eDisMax parameters.

### eDisMax parameters to support

| Solr Parameter | OpenSearch Equivalent | Complexity |
|----------------|----------------------|------------|
| `qf` (query fields + boosts) | `multi_match.fields` with `^boost` | Medium |
| `pf` (phrase fields) | Separate `match_phrase` in `bool.should` | Medium |
| `pf2`, `pf3` (bigram/trigram phrase) | No direct equivalent — flag it | Flag only |
| `mm` (minimum match) | `multi_match.minimum_should_match` | Low |
| `bq` (boost query) | `bool.should` with boost | Medium |
| `bf` (boost function) | `function_score` wrapper | High |
| `ps` (phrase slop) | `match_phrase.slop` | Low |
| `qs` (query slop) | Not directly applicable | Flag |
| `tie` (tiebreaker) | `multi_match.tie_breaker` | Low |

### Filter query support

`fq` parameters are the second most common Solr parameter after `q`. They need to
map to `bool.filter` clauses:

```python
# Input: q=search terms&fq=category:electronics&fq=price:[10 TO 100]
# Output:
{
  "query": {
    "bool": {
      "must": [{"multi_match": {"query": "search terms"}}],
      "filter": [
        {"term": {"category": "electronics"}},
        {"range": {"price": {"gte": 10, "lte": 100}}}
      ]
    }
  }
}
```

### Design decision: single query string vs request object

Current converter accepts a single `q` string. For eDisMax + fq support, it needs
to accept a **request parameter dict**:

```python
def convert_request(self, params: dict[str, str | list[str]]) -> dict:
    """Convert a Solr request (q + fq + defType + qf + ...) to Query DSL."""
```

This is a **breaking API change** for the converter, but the MCP tool can accept
either format and route appropriately.

### Effort estimate
~200 lines for eDisMax parameter handling.
~100 lines for filter query support.
API change + backward compat wrapper: ~50 lines.

### Priority: **HIGH for RC**
Without eDisMax, the converter can't handle most real-world Solr queries.

---

## Gap 5: Report Data Wiring

### Problem
`report.py` has good structure but gets fed empty/hardcoded data because skill.py
never populates the session with real findings.

### What needs to happen

The report has 6 sections. Here's what populates each:

| Report Section | Data Source | Currently Populated? | Fix |
|----------------|-------------|---------------------|-----|
| Incompatibilities | `state.incompatibilities` | Never (only in tests) | Gap 2 fixes this |
| Client Integrations | `state.client_integrations` | Never | Step 6 handler populates |
| Milestones | Hardcoded list | Always same 5 items | Generate from workflow state |
| Blockers | Derived from incompatibilities | Empty (no incompatibilities) | Gap 2 fixes this |
| Implementation Points | Hardcoded + customizations | Always same 3 items | Generate from conversion results |
| Cost Estimates | Hardcoded | Always same generic numbers | Derive from cluster size + complexity |

### Milestone generation from workflow state

Instead of hardcoded milestones, generate from what was actually discovered:

```python
milestones = []
if state.get_fact("schema_migrated"):
    milestones.append("Schema conversion complete — review analyzer mappings")
if state.incompatibilities:
    breaking = [i for i in state.incompatibilities if i.category == "Breaking"]
    milestones.append(f"Resolve {len(breaking)} breaking incompatibilities")
if state.get_fact("cluster_topology"):
    milestones.append("Provision OpenSearch cluster per sizing recommendations")
# ... etc
```

### Cost estimation heuristics

Replace hardcoded "10% increase" with rough calculations:

```python
def _estimate_costs(self, state):
    estimates = []
    # Infrastructure
    solr_nodes = state.get_fact("solr_node_count", 3)
    # OpenSearch needs ~2x nodes due to replica placement rules
    os_nodes = max(solr_nodes * 2, 3)
    estimates.append(f"Infrastructure: ~{os_nodes} OpenSearch nodes "
                     f"(up from {solr_nodes} Solr nodes)")

    # Effort
    incompat_count = len(state.incompatibilities)
    base_weeks = 4
    incompat_weeks = incompat_count * 0.5  # ~0.5 weeks per incompatibility
    estimates.append(f"Effort: ~{base_weeks + incompat_weeks:.0f} weeks "
                     f"({incompat_count} incompatibilities to resolve)")
    return estimates
```

### Effort estimate
~100 lines to wire real data into report sections.
~50 lines for milestone generation.
~50 lines for cost heuristics.

### Priority: **SHOULD HAVE for RC**
The report is what Amazon evaluates. Generic reports undermine credibility.

---

## Gap 6: Steering Doc Integration

### Problem
`_load_steering_docs()` reads all `.md` files from `data/steering/` into a dict.
The dict is stored as `self._steering_docs`. It is referenced **zero times** in
`handle_message()` or any other method.

### What steering docs should do

Steering docs contain domain expertise that should inform the advisor's responses.
They should be **consulted at specific workflow steps**, not loaded and ignored.

### Proposed integration pattern

```python
def _get_steering_for_step(self, step: str) -> str:
    """Return relevant steering content for the current workflow step."""
    step_to_docs = {
        "schema_review": ["incompatibilities", "index_design"],
        "query_intake": ["query_translation"],
        "customization": ["accuracy"],
        "infrastructure": ["sizing", "operations"],
        "integration": ["stakeholders"],
    }
    relevant = step_to_docs.get(step, [])
    return "\n\n".join(
        self._steering_docs[name]
        for name in relevant
        if name in self._steering_docs
    )
```

This keeps the pattern simple — steering docs are context that enhances responses,
not executable logic. The agent (Claude, via MCP) gets the steering content as part
of its context when processing each step.

### Effort estimate
~30 lines for the routing function.
~10 lines per step handler to include steering context.

### Priority: **SHOULD HAVE for RC**
This is what differentiates "generic chatbot" from "domain expert."

---

## Implementation Sequence

```
Gap 2 (incompatibility detection)    ← Do first. Unblocks report + credibility.
    ↓
Gap 1 (conversational workflow)      ← Core product change. Depends on Gap 2
    ↓                                   to have something to report at each step.
Gap 3 (analyzer conversion)          ← Can parallel with Gap 1. Highest
Gap 4 (eDisMax + fq)                   technical value.
    ↓
Gap 5 (report wiring)               ← Falls into place once Gaps 1-4 populate data.
Gap 6 (steering integration)        ← Quick wins once workflow exists.
```

### What Sean can do now (in agent99, before PR #5 lands)
1. Build the analyzer mapping data files (Gap 3 — tokenizer + filter tables as JSON)
2. Build the eDisMax parameter mapping data file (Gap 4 — parameter → DSL patterns)
3. Draft the step handler prompts (Gap 1 — what questions to ask at each step)
4. Build the incompatibility catalog for programmatic consumption (Gap 2 — structured JSON)
5. Draft cost estimation heuristics (Gap 5 — formulas and lookup tables)
6. Enhance SKILL.md with LLM-path workflow instructions (architecture decision)

### What Jeff needs to do (in o19s fork)
1. Add `ConversionResult` return type to both converters (Gap 2)
2. Implement state machine in `handle_message()` (Gap 1)
3. Add analyzer chain conversion using mapping data files (Gap 3)
4. Add eDisMax + fq support to query converter (Gap 4)
5. Wire report sections to real session data (Gap 5)
6. Route steering docs to step handlers (Gap 6)
7. Add MCP session tools: `record_fact`, `record_incompatibility`, `get_session_summary` (architecture)

---

## Resolved Questions

1. ~~**Should the state machine be in Python or in the LLM?**~~ **RESOLVED: Both.**
   Python state machine is the "floor" (works without LLM — required for protocol
   agnosticism). LLM path via SKILL.md + MCP tools is the "ceiling" (better experience
   when LLM is present). Session state is the shared contract between both paths.

2. ~~**Should converters be standalone tools or part of the workflow?**~~ **RESOLVED: Both.**
   Converters are standalone MCP tools (for LLM path) AND called from `handle_message()`
   (for non-LLM path). Both paths write results to session state.

## Open Questions

1. **How opinionated should step handlers be?** Should Step 0 refuse to proceed without
   stakeholder identification, or just note that it's unknown and continue?
   *Recommendation:* Default to permissive. Record "unknown" and continue. The LLM path
   can be more persistent about asking.

2. **What's the minimum viable set of analyzer mappings?** The tables above cover ~25
   tokenizers/filters. Real-world Solr deployments may use 50+. Where's the cutoff for RC?
   *Recommendation:* The 25 in the tables cover ~90% of real deployments. Flag anything
   not in the table as "Unsupported — manual mapping required."

3. **Should `convert_query` accept a request dict or stay as single string?** eDisMax
   needs `qf`, `pf`, `mm`, `fq` — all separate parameters. A request dict is more
   natural. *Recommendation:* Add `convert_request(params)` as new method, keep
   `convert_query(q)` for backward compat. MCP exposes both.
