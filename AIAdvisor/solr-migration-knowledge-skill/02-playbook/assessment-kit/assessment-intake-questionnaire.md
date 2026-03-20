# Assessment Intake Questionnaire

Use this questionnaire before expert interviews begin. The objective is to collect enough structured information to support a serious pre-migration assessment without forcing the client to pre-design the solution.

## How to Answer

Respondents should not treat this like a test. Best-effort answers are useful, especially when paired with confidence and supporting evidence.

For each answer, label confidence as:
- `Known`
- `Estimated`
- `Unknown`

For each section, also ask:
- primary owner
- supporting artifacts available
- major open questions

Guidance for respondents:
- If you are not sure, give your best guess and label it `Estimated`.
- If you truly do not know, say `Unknown` rather than filling space with a confident-sounding answer.
- If a question feels ambiguous, record the ambiguity and ask a clarifying sub-question.
- If a question depends on another team, name that dependency instead of guessing silently.
- If you need help understanding a tradeoff, refer to [pre-migration-assessment-framework.md](../../01-sources/opensearch-migration/pre-migration-assessment-framework.md) and [architecture-option-cards.md](architecture-option-cards.md).

Suggested clarification prompt for respondents:
- `Not sure how to answer. What kind of example, artifact, or level of detail are you looking for here?`

## 1. Business Drivers and Success Criteria

- Why is migration being considered now?
- What business outcome is expected from the migration?
- Is the goal parity, improvement, modernization, cost reduction, risk reduction, or a combination?
- What does success look like for users?
- What does success look like for operations and platform teams?
- What does success look like for leadership?
- Which regressions are acceptable?
- Which regressions are not acceptable under any circumstance?
- What timeline pressures exist, and which are externally fixed?

Embedded guidance:
- If success is not measurable, implementation planning should not start.
- If there is no customer-visible or operational benefit, challenge whether migration is the right move now.
- If unsure, start by naming the primary driver: `parity`, `quality`, `cost`, `platform standardization`, or `risk reduction`.

## 2. Product and Search Experience

- Which user journeys depend on search?
- Which search experiences are in scope: keyword search, browse, facets, autocomplete, spell correction, related content, alerts, recommendations?
- Which experiences are business-critical?
- Which experiences are high-volume versus high-value?
- What known complaints exist today?
- Which current behaviors are truly valuable versus merely familiar?
- Which flows are considered untouchable from a UX perspective?

## 3. Current Solr Footprint

- Which collections, cores, or search domains are in scope?
- Which Solr version and deployment model are currently in use?
- Which query parsers are in use?
- Which custom request handlers exist?
- Which custom update processors, plugins, or embedded logic exist?
- Which features are actively used: grouping, block join, nested docs, MLT, spellcheck, suggesters, streaming expressions, CDCR, atomic updates?
- Which analyzers, tokenizers, synonyms, stopword lists, or dictionaries are in use?

Embedded guidance:
- Treat every custom handler, processor, or plugin as redesign risk until reviewed.
- Treat unsupported feature assumptions as decision points, not implementation details.
- If unsure whether something counts as “custom,” include it anyway and flag it for review.

## 4. Content and Data

- What are the source systems for indexed content?
- What is the approximate document count?
- What is the expected data growth rate?
- What are the freshness requirements?
- What transformations happen before indexing?
- Who owns the content model?
- Who owns metadata quality?
- Are there known stale, duplicate, missing, or malformed document issues today?
- Are there major schema inconsistencies or dynamic-field patterns in current use?

## 5. Queries and Relevance

- What are the top query patterns?
- What query logs or analytics are available?
- What ranking logic exists today?
- What boost rules, synonyms, business rules, or query rewrites are active?
- Are judgments, benchmarks, replay tools, or relevance dashboards already available?
- Which query classes are most important to preserve?
- Which queries are known to perform poorly today?

Embedded guidance:
- “Looks right” is not a relevance strategy.
- If no measurement baseline exists, require a plan before implementation planning.
- If query analytics are weak, provide whatever top-query evidence exists and label the coverage gap.

## 6. Operations and Reliability

- What are the current SLAs for latency, availability, and freshness?
- What are the RTO and RPO expectations?
- What backup and DR patterns exist today?
- What is the current incident rate and common failure mode profile?
- What monitoring and alerting are in place?
- Who is on call today?
- What operational skills exist in-house?
- What operational pain points are driving interest in migration?

## 7. Security and Compliance

- How is authorization enforced today?
- Is filtering application-side, engine-side, or both?
- Are there tenant isolation requirements?
- What regulated or sensitive data may enter the index?
- What audit requirements apply?
- What explainability or access-proof requirements apply?
- Are snippets, autocomplete, and logs reviewed for leakage risk?

## 8. Target-State Assumptions

- Why is OpenSearch the target?
- Is the target AWS managed OpenSearch, self-managed OpenSearch, or another platform variant?
- Is provisioned or serverless under consideration?
- What procurement, region, VPC, IAM, or budget constraints already exist?
- What assumptions are being made about feature parity?
- What assumptions are being made about migration difficulty or duration?

## 9. Team and Governance

- Who is the executive sponsor?
- Who is the product owner?
- Who is the architecture owner?
- Who owns relevance decisions?
- Who owns implementation?
- Who owns security review?
- Who can approve tradeoffs and de-scoping?
- Who can stop rollout if search quality is not acceptable?

## Intake Summary

At the end of the questionnaire, capture:
- top 5 known risks
- top 5 unknowns
- missing artifacts
- contradictory answers
- areas requiring interview follow-up
