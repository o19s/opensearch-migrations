<!-- REVIEW NOTES (delete before sharing):
  - Read the "Problem" section — does it oversell or land honestly?
  - Are the example prompts the right ones for each audience?
  - "What's Next" — conversation starter or TODO list?
  - Should this link from the main README or be a standalone share?
  - The guidance impact table is the centerpiece — does it make sense
    to a PM who doesn't know what script_score is?
-->

# Solr Migration Advisor: What It Is and How to Try It

## The One-Liner

An AI advisor that knows how to migrate Solr to OpenSearch — not generically,
but with O19s methodology, opinionated guidance, and the specific pitfalls
our consultants have learned the hard way.

## What Problem This Solves

A generic LLM asked about Solr-to-OpenSearch migration gives you
*"most things should port directly"* and *"syntax may differ slightly."*
That's not wrong, but it's not useful — it's the answer you get from
someone who read the docs but never did the work.

This advisor gives you the answer you'd get from a senior search
consultant who has done the migration before: *"function queries map to
`script_score` but the syntax is different, custom request handlers have
no direct equivalent and must be rebuilt, and if someone says 'we can
always point back to Solr' you need to ask who owns the rollback runbook."*

The difference is the **guidance content** — 18 expert reference files and
7 steering documents that encode our consulting methodology. We can
[prove this difference is real](#how-we-know-it-works) with automated tests.

## What You Can Do With It Today

### For a PM scoping an engagement

Open a Claude session and ask:

> *"We have 12 Solr collections totaling 800GB across 3 SolrCloud
> clusters. We need to migrate to AWS OpenSearch. Help me build a phased
> migration plan with resource estimates and risk areas."*

> *"Our CTO wants a go/no-go framework for this migration. What criteria
> should we use to decide whether we're ready to cut over?"*

The advisor will walk you through our methodology — phases, team roles,
risk areas, decision criteria — not boilerplate, but calibrated to the
specifics you provide.

### For an engineer doing the migration

Paste a `schema.xml` and ask:

> *"Convert this to an OpenSearch mapping and flag anything that needs
> manual attention."*

The advisor runs a deterministic converter (not LLM guesswork) and then
layers on expert judgment: which fields need rethinking, where the
analyzer chain will behave differently, what will break silently.

Or ask about query translation, sizing, dual-write patterns, relevance
validation with Quepid — it's a phone-a-friend for the working
consultant.

### For a technical lead evaluating the approach

The advisor isn't just a chatbot with a long prompt. It has:

- **Deterministic tools** that convert schemas, translate queries, and
  inspect live Solr clusters via API — these produce repeatable,
  testable output
- **378 automated tests** covering converters, skill logic, golden
  scenarios, and multi-turn conversation flows
- **A guidance impact test** that proves the expert content changes model
  output (see below)

## How We Know It Works

We run the same migration scenario through a small local LLM (3B
parameters) twice: once bare, once with our steering content loaded.
Then we check whether specific expert terms appear in the response.

| | Without Guidance | With Guidance |
|---|---|---|
| `script_score` (function query replacement) | miss | hit |
| `no direct equivalent` (custom handlers) | miss | hit |
| `nested` (child document mapping) | hit | hit |
| `terms lookup` (join replacement) | miss | hit |
| **Score** | **~1/4** | **3-4/4** |

The guidance content is the difference between generic advice and
consultant-grade specificity. The test runs in ~18 seconds on a laptop
with no API costs.

**Latest test report:**
[tests/reports/latest/guidance-impact-report.md](tests/reports/latest/guidance-impact-report.md)

## How to Try It

### 30-second version (just talk to it)

```bash
git checkout feature/kitchen-sink
cd AIAdvisor/skills/solr-opensearch-migration-advisor
claude
```

Then ask a question. Start with one of the examples above, or bring
your own Solr schema.

### Run the tests

```bash
# Unit tests (fast, no dependencies)
pytest tests/ -q

# Guidance impact test (needs Ollama running locally)
ollama pull llama3.2:latest
pytest tests/test_guidance_impact.py -v
```

After the guidance test, open the report:

```
tests/artifacts/latest/guidance-impact-report.md
```

### Share results with the team

```bash
pytest tests/test_guidance_impact.py -v --mode=demo
git push
```

This commits the human-readable report to `tests/reports/` so it's
browsable on GitHub.

## What's In the Box

| Layer | What | Count |
|-------|------|-------|
| **Expert knowledge** | Reference files, steering docs, incompatibility catalog | 18 references, 7 steering docs, 5 data files |
| **Deterministic tools** | Schema converter, query translator, Solr inspector, report generator | 7 Python modules, 18 MCP tools |
| **Consulting playbook** | Intake templates, interview guides, assessment kits | 11 reusable templates |
| **Worked examples** | TechProducts, Drupal, enterprise scenarios | 5 examples at varying complexity |
| **Tests** | Unit, integration, scenario evals, guidance impact | 378 tests across 6 suites |

## What's Next

This is a working prototype on a feature branch. The immediate questions:

1. **Does it handle your scenario?** Try it with a real schema or a real
   client question and see where it helps and where it falls short.
2. **What guidance is missing?** The expert content is the most valuable
   part — every gap found is a gap we can fill and test.
3. **How should this fit into engagements?** Pre-sales scoping tool?
   Consultant companion during active work? Client-facing deliverable
   generator? The answer shapes what we build next.
