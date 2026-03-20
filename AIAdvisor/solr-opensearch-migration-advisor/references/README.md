# Expert Reference Files

These reference files provide deep expert knowledge for the Solr → OpenSearch
migration skill. They are organized in two tiers:

## Primary References (01–07) — Core Migration Path

Cover the 80% case that applies to most engagements:

| File | Domain |
|------|--------|
| `01-strategic-guidance.md` | Go/no-go decisions, when NOT to migrate |
| `02-pre-migration.md` | Inventorying a Solr deployment |
| `03-target-design.md` | Designing the OpenSearch solution |
| `04-migration-execution.md` | Dual-write, cutover, pipelines |
| `05-validation-cutover.md` | Relevance measurement, go/no-go gates |
| `06-operations.md` | AWS ops, monitoring, ISM, DR |
| `07-platform-integration.md` | Spring Boot, Python, Drupal, Rails |

## Secondary References (08+) — Edge Cases and Long Tail

Cover the remaining 20% — obscure Solr features, uncommon configurations,
and issues that only surface in specific situations:

| File | Domain |
|------|--------|
| `08-edge-cases-and-gotchas.md` | 30+ gotchas with external source links |

## Supporting References

| File | Domain |
|------|--------|
| `aws-opensearch-service.md` | AWS-specific operational guidance |
| `consulting-methodology.md` | OSC engagement methodology |
| `consulting-concerns-inventory.md` | Common client concerns and responses |
| `migration-strategy.md` | Migration patterns and strategy |
| `roles-and-escalation-patterns.md` | Team roles and escalation triggers |
| `sample-catalog.md` | Sample data catalog |
| `scenario-drupal.md` | Drupal-specific migration scenario |
| `solr-concepts-reference.md` | Solr feature inventory and complexity |

## Source

These files are maintained in the [agent99](https://github.com/seanoc5/agent99)
knowledge base and synced here. The authoritative source for expert content
development is the agent99 repo.

## Merging with SKILL.md

The existing `SKILL.md` in this directory has its own inline reference tables
(field type mappings, query incompatibilities, customization mappings). These
reference files complement that content with deeper expert guidance. See
`MERGING.md` in this directory for a proposed path to unify the two.
