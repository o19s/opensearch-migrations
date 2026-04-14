# Function Query Migration Reference

Solr function queries use math expressions; OpenSearch uses `function_score`.

| Solr | OpenSearch |
|------|-----------|
| `bf=vote_average^2` | `field_value_factor: { field: "vote_average", factor: 2 }` |
| `bf=recip(ms(NOW,release_date),3.16e-11,1,1)` | `exp` or `gauss` decay on date field |
| `bf=log(vote_count)` | `field_value_factor: { field: "vote_count", modifier: "log1p" }` |
| Arbitrary math (`sum`, `product`, `if`) | `script_score` with Painless scripting |

Key: Solr `bf` is additive (`boost_mode: "sum"`), `boost` is multiplicative.
Set `missing: 0` on `field_value_factor` — Solr silently returns 0, OpenSearch throws errors.
