# LLM vs Deterministic Query Translation Demo

Date: 2026-03-23

This note is a simple way to demo two different translation modes side by side:

- an LLM using only the skill/reference material
- a deterministic request converter using local code

The point is not to declare one "better" in the abstract.
The point is to show that they do different jobs well.

## The Basic Framing

Use this language:

- the LLM path is an **advisor / interpreter**
- the script path is a **deterministic baseline translator**

Or, more bluntly:

- LLM mode is flexible, explanatory, and fuzzy
- script mode is narrower, repeatable, and testable

That is a useful contrast for migration work.

## What The Markdown-Only Skill Can Do

The markdown-only skill can still do useful translation work:

- read a Solr request shape
- explain likely OpenSearch equivalents
- propose an OpenSearch request body
- call out caveats and unsupported areas
- reason across combined request intent

What it cannot guarantee:

- the same output every time
- precise or bounded behavior
- regression-tested stability
- a clean contract for what is supported

So the right claim is:

- the skill-only path can do **advisory translation**
- the deterministic path can do **scoped baseline conversion**

## What The Local Deterministic Path Currently Covers

The local request converter now provides basic demo-level support for:

- `defType=edismax` + `qf` -> `multi_match`
- one or more `fq` params -> `bool.filter`
- `facet.field` -> `terms` aggregation
- `hl=true` + `hl.fl` + basic tags + `hl.q` -> `highlight`
- `rows` -> `size`
- `sort` -> `sort`

This is still explicitly placeholder/demo scope, not full Solr parity.

## Best Demo Format

Use one request and show it three ways:

1. the original Solr request
2. the LLM's translated OpenSearch body and caveats
3. the deterministic script output

Then explain:

- where both paths agree
- where the LLM adds useful caveats
- where the script is more disciplined and stable
- what neither path fully solves yet

## Demo Request 1: eDisMax + Filters

### Solr request

```text
q=laptop&defType=edismax&qf=title^3 description^1&fq=status:active&fq=price:[0 TO 5000]
```

### What you want the LLM to do

- recognize `edismax`
- map `qf` to weighted multi-field search
- keep `fq` in non-scoring filter context
- mention that `mm`, `pf`, `bq`, and `bf` are separate concerns if absent

### What you want the script to do

- emit `multi_match`
- emit `bool.filter`
- preserve the two filter clauses

### Talking point

"The LLM is useful here because it can explain why this is an eDisMax-style relevance request.
The script is useful because it gives us a stable baseline body we can test and demo repeatedly."

## Demo Request 2: Integrated Request

### Solr request

```text
q=laptop&defType=edismax&qf=title^3 description^1&fq=status:active&fq=price:[0 TO 5000]&facet.field=category&hl=true&hl.fl=title,description&sort=price asc&rows=10
```

### What you want the LLM to do

- translate the combined request coherently
- explain the role of each section
- mention likely caveats around highlighting and analyzer parity
- mention `.keyword` / exact-field considerations for faceting

### What you want the script to do

- emit one combined OpenSearch body with:
  - `multi_match`
  - `bool.filter`
  - `aggs`
  - `highlight`
  - `size`
  - `sort`

### Talking point

"The LLM gives us interpretive migration guidance. The script gives us a repeatable conversion
floor. In practice, a migration advisor should probably have both."

## How To Present The Difference Clearly

Do not frame this as:

- "LLM versus rules"

Frame it as:

- "advisory reasoning versus deterministic translation"

That keeps the comparison honest.

## What To Watch For In The LLM Output

Good signs:

- it preserves scoring vs filter separation
- it maps `edismax` toward `multi_match`
- it mentions caveats instead of overclaiming parity
- it notices highlighting/analyzer risk

Bad signs:

- it silently invents support for `mm`, `pf`, or boost semantics not present
- it collapses filters into scoring clauses
- it overstates faceting/highlighting parity
- it produces different structural choices from one run to the next without explanation

## What To Watch For In The Script Output

Good signs:

- output is stable run to run
- supported features are obvious
- unsupported features are simply absent rather than hallucinated

Bad signs:

- the converter looks broader than it really is
- exact filters use weak query types
- integrated requests stop composing cleanly

## Suggested Live Talking Points

- "The markdown-only skill can already do useful best-effort migration reasoning."
- "That is valuable, especially when the source request is incomplete or messy."
- "But for repeatable demos, tests, and downstream tooling, we still want deterministic translation."
- "So the interesting product shape is not LLM or scripts. It is LLM plus scripts."

## Practical Repo Hooks

For the deterministic side:

- [query_converter.py](/opt/work/OSC/agent99/scripts/query_converter.py)
- [demo_query_translation.py](/opt/work/OSC/agent99/scripts/demo_query_translation.py)

For the skill/reference side:

- [SKILL.md](/opt/work/OSC/agent99/skills/solr-to-opensearch-migration/SKILL.md)
- [query-syntax-mapping.md](/opt/work/OSC/agent99/sources/opensearch-migration/query-syntax-mapping.md)
- [solr-concepts-reference.md](/opt/work/OSC/agent99/skills/solr-to-opensearch-migration/references/solr-concepts-reference.md)

## Bottom Line

Yes, showing the markdown-only LLM translation next to the deterministic converter is a good demo.

It demonstrates:

- what the skill can already do without MCP or Python tools
- why deterministic converters still matter
- why the most credible migration-advisor story probably combines both
