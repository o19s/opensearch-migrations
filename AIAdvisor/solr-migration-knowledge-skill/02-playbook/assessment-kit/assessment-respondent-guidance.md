# Assessment Respondent Guidance

Use this guide when presenting the intake and interview process to a client team. The goal is to make it easy for respondents to answer well without feeling forced to be prematurely precise.

## Core Guidance

- Best-effort answers are useful.
- Estimated answers are acceptable when labeled clearly.
- Unknown answers are better than false certainty.
- The purpose of the assessment is to surface decisions and risks, not to reward confident guessing.

## Preferred Prompting Style

When asking a client question, use the following pattern:

1. ask the primary question
2. offer a best-guess fallback
3. tell them what to do if they are unsure
4. point them to a short reference when tradeoffs are involved
5. invite clarifying sub-questions

## Recommended Prompt Format

Use a structure like this:

`Question`

`Not sure?`
- choose the closest option
- mark it as `Estimated`
- name the team or artifact that would confirm it

`Helpful reference`
- link to the relevant internal explainer or option card

`You can also ask`
- one or two clarifying sub-questions

## Example Pattern

Question:
- What is the primary migration goal?

Not sure?
- Choose the closest fit: `parity`, `search quality improvement`, `cost reduction`, `platform standardization`, or `risk reduction`.
- If there are multiple goals, rank the top two.

Helpful reference:
- [architecture-option-cards.md](architecture-option-cards.md)

You can also ask:
- `What is the difference between parity-first and redesign-first?`
- `If we are mostly trying to reduce risk, how should we answer this?`

## Clarifying Sub-Question Policy

Encourage respondents to ask sub-questions such as:
- `What counts as evidence for this answer?`
- `How detailed should this answer be?`
- `Who is usually the right owner for this question?`
- `What is the difference between these two options?`
- `Can I answer with a best guess now and refine later?`

## Research Link Guidance

When providing links to help respondents answer:
- prefer short internal references over long background reading
- link only the most relevant explainer
- explain why the link is useful
- do not bury the user in research before they answer the question

Recommended internal references:
- [pre-migration-assessment-framework.md](../../01-sources/opensearch-migration/pre-migration-assessment-framework.md)
- [architecture-option-cards.md](architecture-option-cards.md)
- [risk-and-readiness-rubric.md](risk-and-readiness-rubric.md)

## Best-Guess Defaults

When a respondent is unsure, offer a reasonable default choice rather than leaving them stuck.

Examples:
- Migration goal: if unclear, start with the dominant business driver.
- Search criticality: if unclear, start with the highest-traffic or highest-revenue search flow.
- Feature inventory: if unsure, include the feature and flag it for confirmation.
- Relevance maturity: if no benchmark exists, mark current state as weak and plan baseline work.
- Ownership: if unclear, name the current operational owner and flag governance ambiguity.

## What to Avoid

- questions with no examples or framing
- forcing binary answers when the reality is uncertain
- assuming the client already understands search-platform tradeoffs
- asking for implementation details during strategic discovery
- treating “unknown” as a failure instead of a useful assessment outcome

