# Solr to OpenSearch Incompatibilities

## Function Queries: bf vs boost
- Solr `bf` is **additive** — it adds to the relevance score. Use `boost_mode: "sum"` in OpenSearch `function_score`.
- Solr `boost` is **multiplicative** — it multiplies the relevance score. Use `boost_mode: "multiply"` in OpenSearch `function_score`.
- These are NOT interchangeable. Using the wrong boost_mode will produce completely different rankings.
- See `references/bf-vs-boost.md` for examples.

## Querqy on AWS OpenSearch Service
- Querqy is **NOT available** on AWS OpenSearch Service (managed). AWS does not allow custom plugin installation.
- Querqy IS available for self-managed OpenSearch via the community plugin.
- For AWS migrations, every Querqy rule must be translated to native OpenSearch constructs.
- See `references/querqy-to-native-os.md` for rule-by-rule translation.

## eDisMax multi_match Type Selection
- Use `type: "best_fields"` when qf fields have **different analyzers** (e.g., text_general vs text_en vs keyword).
- Use `type: "combined_fields"` ONLY when ALL qf fields share the **same analyzer**.
- `combined_fields` will produce errors or wrong results if fields use different analyzers.
- See `references/multi-match-type-selection.md` for decision criteria.

## TMDB copyField Strategy
- Solr copyField rules that feed synonym/idiom/taxonomy variants should be migrated to OpenSearch **multi-fields** with custom analyzers, not `copy_to`.
- OpenSearch `copy_to` copies raw values; it does NOT re-analyze with a different analyzer chain.
- Each Solr copyField destination with a unique analyzer becomes a sub-field under `fields:` in the mapping.
- See `references/copyfield-to-multifield.md` for the TMDB example.

## SMUI Rule Export and Translation
- SMUI exports Querqy rules as a plain-text file (one rule block per input term), not JSON.
- Rule types: UP (boost), DOWN (penalize), FILTER (add filter), DELETE (remove term), SYNONYM (expand query).
- See `references/smui-rule-translation.md` for the export format and per-rule-type OpenSearch DSL.
