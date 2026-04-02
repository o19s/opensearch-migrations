# Go / No-Go Review Template

Use this artifact at explicit migration gates where a human decision is required.

This is not a long narrative report. It is a decision package that answers:

- what stage is under review
- what evidence was examined
- what risks remain
- whether the recommendation is go, no-go, or go with conditions

Use it for:

- assessment gates
- validation gates
- shadow-read readiness gates
- cutover gates
- rollback recommendation reviews

---

## Document Metadata

- Engagement:
- Gate name:
- Prepared by:
- Date:
- Version:

## 1. Decision Under Review

- current stage:
- requested next step:
- environments affected:
- scope of this decision:

## 2. Recommendation

Choose one:

- `Go`
- `Go with conditions`
- `No-Go`

## 3. Evidence Reviewed

- [artifact 1]
- [artifact 2]
- [artifact 3]
- [dashboard / report / query set / checklist]

## 4. What Is True Now

Summarize the current state in a few bullets:

- [state fact 1]
- [state fact 2]
- [state fact 3]

## 5. Decision Drivers

### Reasons To Proceed

- [reason 1]
- [reason 2]

### Reasons To Pause Or Reject

- [risk or blocker 1]
- [risk or blocker 2]

## 6. Conditions And Constraints

If the recommendation is conditional, name the conditions explicitly.

- [condition 1]
- [condition 2]

## 7. Rollback / Escalation Posture

- rollback owner:
- escalation trigger:
- fallback or hold position:

## 8. Approvers

| Name | Role | Decision |
|---|---|---|
|  |  |  |
|  |  |  |

## 9. Final Notes

- [short note on scope limits, assumptions, or follow-up]

---

## Review Questions

Before issuing the decision, confirm:

- Is the decision scope bounded?
- Are the evidence sources recent and relevant?
- Are blockers clearly distinguished from acceptable tradeoffs?
- If the answer is `Go`, would an operator know exactly what is approved next?
- If the answer is `No-Go`, is the next corrective step explicit?
