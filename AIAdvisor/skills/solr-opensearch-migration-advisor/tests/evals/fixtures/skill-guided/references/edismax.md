# eDisMax to OpenSearch Query DSL Reference

| Solr eDisMax | OpenSearch |
|-------------|-----------|
| `qf=title^10 overview^5 cast^3` | `multi_match` with `fields: ["title^10", "overview^5", "cast^3"]` |
| `pf=title^15 overview^8` | `multi_match` with `type: "phrase"` in `bool.should` |
| `mm=75%` | `minimum_should_match: "75%"` |
| `bq=genres:Action^5` | Additional `should` clause with `boost: 5` |
| `bf=vote_average` | `function_score` with `field_value_factor` |

Use `type: "best_fields"` for heterogeneous fields, `type: "cross_fields"` for same-analyzer fields.
Always translate both `qf` AND `pf` — dropping `pf` loses phrase proximity boosting.
