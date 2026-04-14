# Custom Request Handler Migration Reference

Solr custom request handlers (`SearchHandler`, `UpdateRequestHandler` subclasses)
have no direct equivalent in OpenSearch.

Options:
- Decompose into standard OpenSearch features (aggregations, highlighters, collapse)
- Use search templates for reusable query patterns
- Move orchestration logic to client-side code
- Custom OpenSearch plugins (last resort — increases operational complexity)

Key phrase: there is "no direct equivalent" — do not suggest a simple mapping exists.
