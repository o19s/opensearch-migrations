# Strategic Guidance: When NOT to Migrate

**Scope:** Decision-making, "Go/No-Go" heuristics, identifying "Parity Illusions."
**Audience:** Engagement Leads, CTOs, Engineering VPs, Stakeholders.
**Last reviewed:** 2026-03-19 | **Reviewer:** [Initials]

---

## Key Judgements

- **Don't migrate if the search is broken by data or politics, not engine choice.** If search quality is poor, replacing Solr with OpenSearch is like repainting a car that has no engine.
- **"Parity" is a trap.** If a stakeholder requires 1:1 behavioral parity with a legacy system they don't understand, you are not migrating; you are performing an expensive archaeological dig.
- **If the team doesn't understand the current system, they cannot safely migrate it.** Any "black box" legacy logic in Solr (e.g., custom JARs, undocumented DIH chains) is an unexploded bomb waiting to go off during cutover.
- **Migration is not a "Maintenance" task.** It is a platform upgrade. If the company is not ready to invest in observability, relevance tuning, and team training, they should stay on their current platform until they are.
- **If you can't measure it, you can't migrate it.** If there is no baseline (no query logs, no gold standard, no analytics), you have no way to prove the new system is "better"—or even "the same."

---

## Decision Heuristics: "Stop, don't migrate!"

| Red Flag | Heuristic |
|:---|:---|
| **Unknown Search Logic** | If the business logic is baked into a Java JAR that hasn't been touched in 5 years and no one knows how to compile, **STOP.** Perform a "Code Archeology" sprint first. |
| **"Make it faster" (only)** | If the ONLY business driver is performance, and relevance isn't broken, check if a simple Solr cache/node tuning would solve the problem cheaper. |
| **Stakeholder Void** | If the Stakeholder won't define success beyond "Don't break it," you will never finish. Push for a "Success Definition" (e.g., "The new system must beat Solr on CTR for the top 500 queries"). |
| **Data Silo/Governance** | If you don't know who owns the `manu` field across 10 different upstream apps, you will break upstream ingestion. Stop and formalize ownership. |
| **Parity-Above-All** | If the client demands 1:1 results parity, you are likely failing the project. Educate them on BM25 vs TF-IDF differences early. If they won't accept deviation, stay on Solr. |

---

## Common Pitfalls: The "War Stories"

- **The "Haunted Engine" Effect:** A client migrated to OS, but search quality dropped. It turned out they had a Solr `schema.xml` custom analyzer that was actually just broken, but users had "trained" themselves to work around it for years. The new engine worked "correctly," but because it differed from the "wrong" behavior, the client claimed the migration failed.
- **The "Shadow Consumer":** A client migrated their search cluster, only to realize an internal "Reporting Tool" was directly querying the Solr XML API for sales stats. Their dashboard broke, and they lost 3 days of revenue reporting because no one knew the "Search Engine" was actually acting as a database.

---

## Next Steps

1.  **If any of these "Red Flags" apply:** Halt the migration workstream and move to a "Pre-Migration Assessment" phase to de-risk the identified bottleneck.
2.  **Formalize Success:** If you are proceeding, create a `success-criteria.md` in the client's `03-specs/` folder, signed off by the primary Stakeholder.
