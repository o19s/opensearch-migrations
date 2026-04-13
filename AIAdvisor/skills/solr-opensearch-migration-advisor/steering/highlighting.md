# Solr to OpenSearch Highlighting Steering

## Overview
Map Solr highlighting parameters to OpenSearch highlighter configuration.
Highlighting is critical for media/text-heavy search where users expect
snippet previews in results.

## Highlighter Types
- Solr `hl.method=original` → OpenSearch `type: "plain"` (re-analyzes text at query time).
- Solr `hl.method=unified` → OpenSearch `type: "unified"` (default, recommended).
- Solr `hl.useFastVectorHighlighter=true` → OpenSearch `type: "fvh"`.

## Parameter Mapping
- `hl.fl=title,overview` → `highlight.fields: { "title": {}, "overview": {} }`.
- `hl.fragsize=150` → `fragment_size: 150`.
- `hl.snippets=3` → `number_of_fragments: 3`.
- `hl.simple.pre=<em>` → `pre_tags: ["<em>"]`.
- `hl.simple.post=</em>` → `post_tags: ["</em>"]`.
- `hl.requireFieldMatch=true` → `require_field_match: true`.

## Term Vectors (FVH Requirement)
- Solr fields with `termVectors="true"` can use Fast Vector Highlighter.
- OpenSearch FVH requires `term_vector: "with_positions_offsets"` in the field mapping.
- **Storage warning**: term vectors significantly increase index size (often 2-3x for text-heavy fields). Flag this as a DevOps/storage consideration.
- If the source Solr schema does not use termVectors, recommend `unified` highlighter instead of FVH to avoid the storage overhead.

## Example
Solr request parameters:
```
hl=true&hl.fl=title,overview&hl.fragsize=150&hl.snippets=3&hl.simple.pre=<em>&hl.simple.post=</em>
```

OpenSearch query equivalent:
```json
{
  "highlight": {
    "fields": {
      "title": {},
      "overview": {}
    },
    "fragment_size": 150,
    "number_of_fragments": 3,
    "pre_tags": ["<em>"],
    "post_tags": ["</em>"]
  }
}
```
