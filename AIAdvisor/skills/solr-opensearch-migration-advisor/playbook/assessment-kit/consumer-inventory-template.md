# Consumer Inventory Template

Use this artifact to identify every meaningful consumer of the current search system before migration planning advances.

This is not just an application list. It is the dependency map that supports:

- application integration planning
- cutover readiness
- rollback realism
- hidden-consumer discovery

Fill this in during assessment and keep it current through cutover planning.

---

## How To Use This

Track every consumer that:

- reads from Solr
- writes to Solr
- depends on Solr response shape or APIs
- would create business risk if missed during cutover

Good sources:

- architecture diagrams
- service repositories
- cron job inventories
- support/admin tool lists
- platform owner interviews
- logs and query analytics

---

## Suggested Fields

| Field | Purpose |
|---|---|
| `consumer_id` | Stable short identifier |
| `consumer_name` | Human-readable consumer name |
| `owner` | Team or person responsible |
| `consumer_type` | Web app, API, batch job, admin tool, script, service |
| `reads_search` | Whether it performs read/search behavior |
| `writes_index` | Whether it writes, updates, or deletes indexed data |
| `criticality` | Business importance: High, Medium, Low |
| `cutover_day_required` | Whether it must work on initial cutover day |
| `fallback_available` | Whether a safe fallback exists |
| `solr_touchpoints` | Endpoints, handlers, collections, or client libraries used |
| `response_shape_dependency` | Whether it depends on Solr-specific response structure |
| `migration_status` | Not started, assessing, in progress, validated, cut over |
| `notes` | Risks, assumptions, or open questions |

---

## Markdown Table Starter

| consumer_id | consumer_name | owner | consumer_type | reads_search | writes_index | criticality | cutover_day_required | fallback_available | solr_touchpoints | response_shape_dependency | migration_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 |  |  |  | yes/no | yes/no |  | yes/no | yes/no |  | yes/no |  |  |
| C2 |  |  |  | yes/no | yes/no |  | yes/no | yes/no |  | yes/no |  |  |

---

## CSV Header Starter

```csv
consumer_id,consumer_name,owner,consumer_type,reads_search,writes_index,criticality,cutover_day_required,fallback_available,solr_touchpoints,response_shape_dependency,migration_status,notes
```

---

## Review Questions

Before calling the inventory complete, ask:

- Have we included background jobs and admin tools, not just the main app?
- Do we know which consumers are read-only vs write-sensitive?
- Do we know which consumers must work on day one of cutover?
- Do we know which consumers have no realistic fallback?
- Do we know where Solr-specific response assumptions still exist?

If the answer is no to any of those, the inventory is still incomplete.
