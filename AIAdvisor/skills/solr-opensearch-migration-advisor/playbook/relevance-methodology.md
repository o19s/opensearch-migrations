# Relevance Methodology
**Scope:** How O19s measures, baselines, and improves search relevance during a migration — from first judgement set through production tuning. Tooling (Quepid, RRE), metrics (nDCG, P@k), and the baseline→tune loop.
**Audience:** Search relevance engineers, engagement leads, anyone responsible for proving the new engine is better (or at least not worse)
**Source:** OSC Playbook slides 17, 20–23 + expert annotation
**Last reviewed:** 2026-03-17  |  **Reviewer:** AI draft — needs expert review (highest priority)

---

## Key Judgements
<!-- This section is the most important in the file — hardest to write, most valuable. Write from memory. -->

> ⚠️ **This is the highest-priority gap in the entire skill.** Quepid workflow, nDCG interpretation, and the judgement methodology are core O19s IP. The bullets below are a starting scaffold — they need real O19s opinion.

- **"Apples-to-apples" is harder than it sounds.** You must measure the old and new engine on identical query sets, identical judgement sets, and identical scoring configurations. Any asymmetry in the comparison — different query shapes, different field boosts — will produce a meaningless result. Document every assumption.
- **The baseline is a stake in the ground, not a ceiling.** Its only job is to define "current state." Don't optimize the legacy system before baselining it — you'll be comparing against a ghost.
- **nDCG is the right default metric for most migrations.** It accounts for rank position (finding something at position 1 is more valuable than position 10) and handles graded relevance judgements (perfect / good / fair / bad) more naturally than binary P/R. Use P@k for simpler products or as a sanity check alongside nDCG.
- **Human judgements are expensive and wrong.** They're expensive because recruiting, training, and managing annotators takes real time. They're wrong because inter-annotator agreement on search relevance is typically 60–70% at best. Build in a calibration round; measure and report Kappa.
- **Customer analytics beat human judgements for query prioritization.** Use analytics to decide *which queries* to judge, not *how to judge them*. Judging the wrong queries (low-frequency, edge cases) wastes annotation budget and produces a measurement that doesn't reflect real customer experience.
- **"Relevance isn't meeting expectations" usually means the judgement set is wrong, not the search engine.** Before tuning, audit the judgement methodology. Are the judgements from people who actually use the product? Are they calibrated? Is the query set representative?

*[Add 3–4 more Key Judgements from your own Quepid/RRE experience here]*

---

## The Baseline → Tune Loop

This is the core O19s methodology cycle. Everything else in this file supports it.

```
Measure (run scoring tool)
    ↓
Log (record the score + config state)
    ↓
Analyze (best/worst queries, best/worst information needs)
    ↓
Hypothesize (one change at a time — this is one story)
    ↓
Test (run the experiment; compare score delta)
    ↓
Decide (promote / discard / modify hypothesis)
    ↓
Report (communicate to stakeholders)
    ↓
Measure → (repeat)
```

**Key constraints on the loop:**
- One hypothesis = one experiment = one story. Don't bundle changes.
- Always compare against the logged baseline, not the prior run. Drift is invisible otherwise.
- Run the loop at sprint cadence. Relevance tuning that happens in bursts (two weeks before cutover) is a red flag.
- Maintain a decision log. "We tried synonym expansion for [query cluster] and it hurt P@5 by 0.03 nDCG — discarded" is valuable institutional memory.

---

## Judgements and Ratings

### Methodology Setup

Before you collect a single judgement:

1. **Define the relevance scale.** OSC typically uses a 4-point scale: Perfect (3) / Good (2) / Fair (1) / Bad (0). Document what each level means for this specific product.
2. **Select the query set.** Start with actual analytics data. Take the top 100–200 queries by frequency. Add a representative sample from each major information-need category.
3. **Calibrate with a pilot round.** Have 2–3 judges rate the same 20–30 queries independently. Measure Fleiss' Kappa. If Kappa < 0.4, your rubric is too ambiguous — clarify before scaling.
4. **Separate annotation from hypothesis formation.** Judges should not be the same people proposing tuning changes.

### Common Judgement Mistakes

- Judging too many edge-case or zero-result queries — these don't move nDCG meaningfully
- Allowing the person proposing the tuning change to also rate its effectiveness
- Updating the judgement set while running experiments (invalidates comparisons)
- Using click data directly as relevance signal without normalizing for position bias

### Quepid Workflow (needs expert annotation)

> The outline below reflects what we understand of Quepid's workflow. This section needs someone who has actually run a Quepid case on a production engagement to fill in the real sequence, common pitfalls, and interpretation tips.

1. Create a Case — name it for the engagement + query set version (e.g., `acme-baseline-v1`)
2. Configure the search endpoint — point to Solr or OpenSearch; set the query template
3. Import the query set (CSV: `query, notes`)
4. Set the scorer — nDCG@10 is a reasonable default for most engagements
5. Run queries; results load in the Quepid interface
6. Rate each result (0–3 scale); Quepid tracks per-query scores
7. Export the case score — this is your baseline
8. For tuning: clone the case, adjust the query template or field weights, re-rate, compare delta

**Important**: Export and version-control your Quepid case JSON. Losing it means losing the ability to reproduce measurements.

*[Expert review needed: what does a typical initial nDCG score look like? What's a "good" delta from a tuning experiment? When do you stop tuning?]*

### RRE (Rated Ranking Evaluator) Workflow (needs expert annotation)

RRE is better suited for CI/CD integration — it runs as part of your build pipeline and alerts when a code change degrades relevance. Quepid is better for interactive exploration.

> *[RRE workflow detail needed — how do you set up an RRE project, what does the ratings JSON look like, and how do you integrate it into a migration pipeline?]*

---

## Metrics Reference

| Metric | What It Measures | When to Use |
|---|---|---|
| **nDCG@k** | Graded relevance at rank k, position-weighted | Default for most migrations; handles non-binary relevance well |
| **P@k** | Fraction of top-k results that are relevant | Simpler to explain; good for stakeholder-facing reporting |
| **R@k** | Fraction of all relevant docs that appear in top k | Useful when recall matters (legal, medical, compliance) |
| **ERR** | Expected Reciprocal Rank — user model that stops at first "perfect" result | Good for navigational queries; less common in practice |
| **MRR** | Mean Reciprocal Rank — where does the first relevant result appear? | Good for "find the right answer" tasks |

**For most Solr→OpenSearch migrations:** nDCG@10 or nDCG@20 as primary, P@5 as secondary sanity check.

---

## Tooling Decision

| Tool | Best For | Limitations |
|---|---|---|
| **Quepid** | Interactive relevance exploration; stakeholder demos; building judgement sets collaboratively | Not CI/CD-native; requires UI interaction |
| **RRE** | Automated regression testing; integrating relevance checks into deploys | Steeper setup; less interactive |
| **Querqy** | Query rewriting (synonyms, boosts, filters, deletes) managed as rules rather than code. Platform-agnostic rule engine with Solr, ES, and OpenSearch plugins. | Engine-native rules need rewriting during migration. AWS Managed requires custom plugin upload. |
| **SMUI** | Web UI for merchandisers to manage Querqy rules without editing files. Supports OpenSearch backend. | Must reconfigure backend + audit rules for Solr-native syntax after migration. |
| **Search-Collector** | Online measurement (real traffic); A/B test logging | Requires production integration; lags offline tools |
| **A/B testing** | Post-cutover live comparison | Not usable during migration phase |
| **Interleaving** | Online comparison with smaller user exposure than A/B | Complex to implement correctly |

**Recommended default:** Quepid for offline measurement during migration; add RRE for CI/CD once the new engine is in staging. If the client uses Querqy, port and validate rules *before* baselining — otherwise measurements don't reflect production behavior. Ship online measurement (Search-Collector or A/B) as a post-cutover workstream.

---

## Reporting to Stakeholders

The playbook (slide 21) calls for three dashboards: Relevance, Performance, and Operational. During a migration, you rarely have all three live — prioritize:

1. **Relevance dashboard first.** This is what proves the migration is worth doing. Show nDCG trend over sprints.
2. **Performance dashboard second.** Latency and throughput comparison vs. Solr baseline.
3. **Operational dashboard third.** Cluster health, indexing rate, error rates — important but not what stakeholders care about in early phases.

**Reporting cadence:** At minimum, one relevance report per sprint. Don't go more than 2 weeks without a measurement cycle — gaps make it impossible to attribute improvements to specific changes.

---

## Decision Heuristics

- **If nDCG on new engine < nDCG on old engine after 3 tuning sprints → escalate.** It may be a schema problem, a scoring formula problem, or a judgement set problem. Get a second pair of eyes.
- **If the team is debating which metric to use → start with nDCG@10 and add others later.** Perfect is the enemy of started.
- **If a single experiment moves nDCG by > 0.05 → verify. That's large.** Either something was wrong with the baseline, or the change was compounded with another variable. Re-run clean.
- **If stakeholders ask for A/B testing before cutover → reframe.** A/B is a post-cutover tool. Pre-cutover, the answer is Quepid + offline judgements.
- **If the client has no query analytics → don't start judgements yet.** Judging without analytics data produces a judgement set that doesn't represent real customers. The first deliverable is analytics instrumentation.

---

## Open Questions / Evolving Guidance

- What's the right nDCG@k target for "parity with Solr"? Is there a rule of thumb (e.g., new engine nDCG must be ≥ 95% of baseline)?
- How do you handle multilingual judgements? Different rater pools per language?
- Quepid is being actively developed — are there newer features (LTR integration, case sharing) that we should be using in standard engagements?
- How do we handle the "BM25 vs. TF-IDF gap" at the measurement level? The new engine's scores will naturally differ — how do we prevent that from being misread as a relevance regression?
