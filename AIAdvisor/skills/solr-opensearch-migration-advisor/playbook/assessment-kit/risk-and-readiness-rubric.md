# Risk and Readiness Rubric

Use this rubric to score pre-migration readiness and communicate where discovery must continue before implementation planning.

## Scoring Scale

Score each category from `0` to `3`.

- `0`: unknown, missing, or unowned
- `1`: weak understanding, partial evidence, or inconsistent ownership
- `2`: mostly understood with some material gaps
- `3`: strong evidence, clear ownership, and aligned understanding

The score is directional. It supports discussion and prioritization. It should not be treated as false precision.

## Readiness Categories

### Business Clarity

Look for:
- clear migration driver
- measurable success definition
- agreed tradeoff posture

### Product and Search Experience Clarity

Look for:
- clear in-scope experiences
- critical journeys identified
- “must preserve” behaviors distinguished from “familiar” behaviors

### Content and Data Access

Look for:
- known content sources
- confirmed access
- identified owners
- document volume and freshness understood

### Feature Inventory Completeness

Look for:
- active Solr features known
- plugins/processors inventoried
- unsupported features identified early

### Query and Relevance Maturity

Look for:
- top query patterns known
- baseline analytics available
- ranking logic documented
- evaluation method understood

### Operational Readiness

Look for:
- SLA/SLO clarity
- monitoring and DR understood
- incident ownership defined

### Security and Compliance Clarity

Look for:
- auth model documented
- sensitive data exposure risk understood
- audit obligations identified

### Target Platform Clarity

Look for:
- target platform explicitly chosen
- major service constraints validated
- unrealistic parity assumptions challenged

### Ownership and Governance

Look for:
- named owners
- decision authority clear
- de-scope authority clear
- rollout stop authority clear

### Evidence Quality

Look for:
- logs
- artifacts
- baselines
- architecture docs
- incident history

## Interpreting Total Score

- `0-12`: discovery only; not ready for strategic planning
- `13-20`: partial readiness; major gaps remain
- `21-26`: viable for strategic planning; not yet implementation-ready
- `27-30`: strong planning readiness; can define a gated implementation roadmap

## Risk Severity

Track risk separately from readiness score.

Severity levels:
- `Low`
- `Medium`
- `High`
- `Critical`

## Automatic High-Risk Conditions

Mark as `High` or `Critical` if any of the following are true:
- success criteria are undefined
- content access is blocked or unclear
- active custom plugins or processors are not yet understood
- no query evidence or analytics exist
- security model is unclear
- unsupported parity assumptions remain unchallenged
- no owner can make rollout tradeoff decisions

## Gate Recommendation Language

Use one of these assessment outcomes:

- `Do not begin implementation planning yet. Continue discovery.`
- `Proceed with strategic planning only. Major readiness gaps remain.`
- `Proceed with gated implementation planning after resolving listed gaps.`
- `Ready for implementation planning with explicit risk controls.`

