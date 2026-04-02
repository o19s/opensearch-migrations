# Hello Migration Demo Script

Date: 2026-03-23

This is the recommended first live demo for the Solr-specific lane.

It is designed to be:

- short
- credible
- forgiving
- grounded in the repo's strongest current coverage

Use this when you want to show:

- what the migration advisor is
- how a technical but Solr-inexperienced user might interact with it
- what deterministic translation support exists today
- where the tool is intentionally honest about its boundaries

## Demo Goal

Show a quick, useful first-contact experience for a technical OpenSearch-native user who does not
know much about Solr migration yet.

The success condition is not:

- "we fully migrate Solr live in 10 minutes"

The success condition is:

- "this tool asks good migration questions, gives useful early guidance, and can already show some
  grounded translation behavior"

## Recommended Audience Framing

Use a persona like this:

- technical OpenSearch / AWS engineer
- limited Solr background
- wants a quick understanding of the migration problem space
- only has partial source details available

Good opening line:

> "This is the first-contact migration experience: a strong OpenSearch engineer who is not yet a
> Solr migration expert wants to understand what the tool can do."

## Demo Assets

Primary sources:

- [five-demo-stories-solr-migration.md](/opt/work/OSC/agent99/project/demos/five-demo-stories-solr-migration.md)
- [golden-scenario-techproducts.md](/opt/work/OSC/agent99/tests/evals/golden-scenario-techproducts.md)
- [demo_query_translation.py](/opt/work/OSC/agent99/scripts/demo_query_translation.py)
- [llm-vs-deterministic-query-translation-demo.md](/opt/work/OSC/agent99/project/demos/llm-vs-deterministic-query-translation-demo.md)

Optional supporting sources:

- [techproducts-demo/README.md](/opt/work/OSC/agent99/examples/techproducts-demo/README.md)
- [testing-status.md](/opt/work/OSC/agent99/project/testing/testing-status.md)

## Recommended Timing

Total target:

- `12-15 minutes`

Suggested breakdown:

1. intro framing: `1-2 min`
2. fast YOLO/Express interaction: `2-3 min`
3. short advisor interaction: `4-5 min`
4. deterministic translation examples: `2-3 min`
5. close with limits and next steps: `1-2 min`

## Part 1: Intro Framing

### What to say

> "I'll start with the simplest credible migration story: a technical user who knows OpenSearch well
> but doesn't know Solr migrations deeply. The point is not to finish a migration. The point is to
> show how the tool helps orient the user quickly and then deepens into a more structured advisor
> flow."

### What to emphasize

- this is an introductory story, not the hardest scenario
- the user intentionally does not know all the answers yet
- the tool should still be useful

## Part 2: Fast YOLO / Express Interaction

### Goal

Show a fast first-pass interaction before deeper intake.

### Suggested prompt

> I'm an OpenSearch engineer helping evaluate a migration from Solr to OpenSearch.
> I don't know Solr very well yet. Assume a fairly standard TechProducts-like setup with a few text
> fields, some numeric fields, copyField behavior, and a couple common query patterns.
> Give me the fastest useful orientation: what are the first things I should care about?

### What good output looks like

- asks or suggests the right first artifacts:
  - schema
  - query samples
  - analyzers
  - copyField
  - deployment/topology basics
- mentions major migration themes:
  - schema/type mapping
  - query translation
  - analyzers/relevance
  - operational differences
- does not require perfect source details to be useful

### What to say after

> "This is the lightweight orientation pass. It should help a technically strong user get bearings
> even before they know enough Solr to answer everything well."

## Part 3: Short Advisor Interaction

### Goal

Show the tool moving from vague orientation into a more structured migration conversation.

### Suggested prompt sequence

Prompt 1:

> I'm a search engineer. We're migrating a product catalog from Solr to OpenSearch on AWS.
> The schema is pretty standard: text fields like name and features, price and popularity, a boolean
> inStock field, and copyField into a catch-all text field.

Prompt 2:

> We also have analyzer behavior similar to text_general with lowercase, stopwords, and some query-time
> synonyms like "hd" to "hard drive."

Prompt 3:

> Main query patterns are:
> 1. q=hard drive&qf=name^2 features^1 cat^0.5&defType=edismax
> 2. q=*:*&fq=inStock:true
> 3. q=*:*&facet=true&facet.field=cat&rows=0

### What good output looks like

- identifies stakeholder role
- recognizes analyzer/synonym relevance risk
- explains copyField / aggregate text field implications
- recognizes:
  - `edismax`
  - `fq`
  - facets
- asks sensible next questions rather than bluffing

### What to highlight live

- the tool is asking migration-shaped questions, not just generic LLM questions
- it surfaces relevance/analyzer concerns early
- it can already reason over partial Solr detail

## Part 4: Deterministic Translation Examples

### Goal

Show that there is some grounded, repeatable translation support today.

### Command

```bash
python scripts/demo_query_translation.py
```

### What this currently shows

- `defType=edismax` + `qf` -> `multi_match`
- `fq` -> `bool.filter`
- `facet.field` -> `terms` aggregation
- basic `highlight`
- integrated request composition with:
  - query
  - filters
  - aggs
  - highlight
  - size
  - sort

### What to say

> "This is the deterministic side. It is narrower than the advisor, but stable and testable. So the
> interesting product shape is not LLM or scripts. It is LLM plus scripts."

## Part 5: Optional LLM vs Deterministic Comparison

### Goal

Show the difference between advisory translation and deterministic translation.

### How to frame it

- LLM path: advisor / interpreter
- script path: deterministic baseline translator

### Suggested line

> "The LLM can often reason more broadly and add caveats. The script gives us a bounded and repeatable
> translation floor."

### Supporting note

- [llm-vs-deterministic-query-translation-demo.md](/opt/work/OSC/agent99/project/demos/llm-vs-deterministic-query-translation-demo.md)

## Part 6: Closing Summary

### Recommended close

> "For a first-contact migration experience, this is already in good shape. We can orient the user,
> ask better migration questions than they would ask on their own, and show some grounded request
> translation. Where the migration gets more advanced, the tool shifts from 'automatic translator' to
> 'advisor and risk surfacer,' and that's the honest boundary today."

## What To Avoid Saying

Avoid:

- "We already translate Solr fully."
- "This is production-complete query parity."
- "Highlighting is solved."
- "Advanced Solr semantics are automated."

Prefer:

- "basic demo-level support"
- "repeatable translation floor"
- "strong advisory value"
- "honest partial support"

## Recovery Paths If The Live Demo Gets Awkward

### If the advisor output is too generic

Switch to the deterministic side and say:

> "Let me show the grounded request-level translator next, since that gives a more concrete baseline."

### If the audience wants more realism

Say:

> "The next step up from this intro story is the Drupal or mid-market enterprise story, where the
> tool's value is more in migration planning and risk surfacing than in pretending every feature is
> auto-translated."

Then point to:

- [five-demo-stories-solr-migration.md](/opt/work/OSC/agent99/project/demos/five-demo-stories-solr-migration.md)

### If someone challenges parity

Say:

> "That's a fair challenge. This intro demo is deliberately scoped to a realistic first-contact story.
> The repo is stronger today on advisory depth plus demo-level request translation than on full Solr
> semantic parity."

## One-Page Version

If you only remember five beats, use these:

1. Open with the first-contact persona.
2. Run a short orientation prompt.
3. Show a few migration-shaped follow-up prompts.
4. Run `python scripts/demo_query_translation.py`.
5. Close with "LLM plus scripts" and an honest boundary statement.

## Bottom Line

This is the best next demo because it:

- matches the repo's strongest current capabilities
- is easy to present honestly
- creates a clean runway into the harder Drupal and enterprise stories later
