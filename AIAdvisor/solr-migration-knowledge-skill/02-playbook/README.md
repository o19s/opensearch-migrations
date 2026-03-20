# 02-playbook — OSC Consulting Methodology

This folder contains the O19s/OSC process knowledge for search engine migration engagements.
It's the methodology layer, distinct from the technical migration content in `01-sources/`.

In this checkout, the methodology lives in markdown. Some repo docs still refer to a PPTX
playbook, but that deck is not committed here, so treat the markdown files in this folder as
the available source of truth.

---

## What's Here

| File | Contents | Source Slides |
|---|---|---|
| `pre-migration-assessment.md` | When *not* to migrate, risk register, prerequisites, preparation checklist | 8–11 |
| `relevance-methodology.md` | Baseline→tune loop, Quepid/RRE, metrics, judgements | 17, 20–23 |
| `migration-roles-matrix.md` | Delivery roles and responsibilities during migration engagements | derived |
| `team-and-process.md` | Team roles, communication, meeting cadence | 6–7, 26–27 |
| `intake-template.md` | Structured question guide for client intake sessions (9 blocks, ~59 questions) | field-derived |
| `interview-guide.md` | Expert interview guide for Sessions 2–3: gap-fill, assumption challenge, design review, readiness gates | assessment kit + field-derived |
| `assessment-kit/` | Reusable assessment artifacts: option cards, readiness rubric, readout template, red-team checklist (8 files) | assessment framework |

These markdown files are still draft material and need expert review, especially in the Key
Judgements sections where the value should be hard-won O19s opinion rather than summary.

---

## How This Feeds the Skill

Content in this folder is the primary source for two of the highest-priority skill gaps:

- **`04-skills/.../references/01-strategic-guidance.md`** — draws heavily from `pre-migration-assessment.md` (especially the risk table and "when not to migrate" section)
- **`04-skills/.../references/05-relevance-validation.md`** — draws heavily from `relevance-methodology.md` (the Quepid/RRE workflow, baseline→tune loop, and judgement methodology)

When you review or extend a file here, assume it will be distilled into those skill chunks. Write with that audience in mind: a junior O19s consultant or a client engineer who needs to know *what to do*, not just *what exists*.

---

## What's Missing

The playbook covers a lot of ground, but several areas are either thin in the deck or absent entirely:

- **Solr-specific gotchas** — the playbook is search-engine-agnostic. Solr→OpenSearch specifics (DIH, SolrCloud ZK, TF-IDF→BM25) aren't in here.
- **Real war stories** — the Common Issues slide (slide 9) is a great start, but the good stuff is what consultants remember, not what fits on a slide.
- **Quepid workflow detail** — the playbook names Quepid but doesn't show how to actually set up a case, run a scorer, or interpret nDCG deltas. This is core O19s IP that lives in heads, not slides.
- **Client handoff / knowledge transfer** — the playbook notes it as a goal; there's no checklist for what "done" looks like from a KT perspective.
- **Post-migration operations** — slide 24 lists topics (HA, DR, sharding, monitoring) without depth.

These gaps are tracked in `05-working/CONTENT-STRUCTURE.md`.

---

## How to Contribute

The most valuable thing you can do is add **Key Judgements** and **war stories** — opinions that a senior OSC consultant carries in their head but that aren't written down anywhere. The markdown template in `05-working/CONTRIBUTOR-GUIDE.md` explains the format.

Reviewing an existing file here is a ~30-minute task. Writing a net-new section (e.g., filling the Quepid workflow gap) is 1–2 hours.

Don't just restate the existing markdown. Add what's *between the lines* of the current
material: the things you'd tell a colleague before they walked into a difficult client meeting.
