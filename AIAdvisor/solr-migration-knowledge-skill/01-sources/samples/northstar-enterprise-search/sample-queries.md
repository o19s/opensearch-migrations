# Representative Solr Query Patterns

## 1. General Keyword Search

```text
/select?q=hydraulic+pump+seal&qf=title^8 part_number^12 model_number^10 summary^4 body^1
&pf=title^15 model_number^20
&mm=2<75%
&defType=edismax
&rows=10
```

## 2. Part Lookup With Entitlement and Region Filters

```text
/select?q=NS-4400+seal+kit
&defType=edismax
&qf=part_number^15 title^8 compatible_models^10 summary^3
&fq=doc_type:part
&fq=region:NA
&fq=dealer_tier:(gold OR platinum)
&fq=visibility_level:(dealer OR internal)
&rows=20
```

## 3. Service Bulletin Search With Freshness Boost

```text
/select?q=overheating+fault+E41
&defType=edismax
&qf=title^7 error_codes^12 symptoms^8 body^2
&bq=doc_type:bulletin^5
&bf=recip(ms(NOW,published_at),3.16e-11,1,1)^3
&fq=region:EMEA
&sort=score desc
```

## 4. Manual Search With Product Line Facets

```text
/select?q=maintenance+schedule
&defType=edismax
&qf=title^6 body^2 product_family^5
&fq=doc_type:manual
&facet=true
&facet.field=product_line
&facet.field=language
&facet.limit=15
```

## 5. Support Case Similarity Search

```text
/select?q=pressure+drop+during+startup
&defType=edismax
&qf=case_title^6 case_summary^3 symptom_terms^8
&fq=doc_type:case
&fq=business_unit:water_systems
&rows=10
```

## Translation Notes

- `qf` and `pf` will likely become a `multi_match` plus phrase `match_phrase` combination.
- entitlement and region filters should move into `bool.filter`.
- freshness boost should be reimplemented with `function_score`.
- facet behavior should move to aggregations.
- any Solr collapse behavior should be explicitly reviewed rather than blindly ported.
