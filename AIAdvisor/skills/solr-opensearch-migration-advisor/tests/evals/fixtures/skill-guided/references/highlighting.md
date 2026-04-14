# Highlighting Migration Reference

| Solr | OpenSearch |
|------|-----------|
| `hl.fl=title,overview` | `highlight.fields: { "title": {}, "overview": {} }` |
| `hl.fragsize=150` | `fragment_size: 150` |
| `hl.snippets=3` | `number_of_fragments: 3` |
| `hl.simple.pre=<em>` | `pre_tags: ["<em>"]` |
| `hl.simple.post=</em>` | `post_tags: ["</em>"]` |
| `hl.requireFieldMatch=true` | `require_field_match: true` |

Highlighter types:
- `hl.method=unified` → `type: "unified"` (default, recommended)
- `hl.method=original` → `type: "plain"`
- Fields with `termVectors="true"` → `type: "fvh"` (requires `term_vector: "with_positions_offsets"` in mapping)
