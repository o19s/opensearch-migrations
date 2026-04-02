# Risk Register

**Artifact ID:** `northwind-risk-register-v1`
**Related assessment:** `assessment-summary.md`
**Status:** Open

| ID | Risk | Severity | Evidence | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Relevance acceptance is subjective and undocumented | High | No judged query set; boost rules described informally | Build and review gold query set before validation gate | Search lead |
| R2 | Inventory freshness may degrade during backfill and replay | High | Current business requirement is minute-level freshness | Isolate delta pipeline and monitor replay lag separately from bulk backfill | Platform lead |
| R3 | Manual synonym management may diverge between source and target | Medium | Synonyms updated outside deploy workflow | Move synonym source into versioned config before cutover | Search lead |
| R4 | Approval authority for rollback is unclear | Medium | No named owner yet in intake notes | Assign migration commander and rollback approver before cutover gate | Product owner |
| R5 | Query rewrite layer may expand scope late in project | Medium | eDisMax features are heavily used across browse and search | Lock API contract and require change review on unsupported patterns | App lead |

## Blocking Risks For Cutover Approval

- `R1`
- `R2`
- `R4`

## Accepted Risks For Validation Stage

- `R3` may remain open during offline validation if source and target synonym snapshots are pinned.
- `R5` may remain open during shadow traffic if unsupported patterns are blocked from production exposure.
