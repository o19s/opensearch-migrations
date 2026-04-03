# Solr Customizations Assessment Steering

## Overview

Step 4 of the migration workflow assesses Solr customizations — plugins, handlers,
authentication, and operational patterns — that require migration planning beyond
schema and query translation.

## Structured Question Sets

### Request Handlers
- Are you using any custom `RequestHandler` classes beyond the standard `/select`, `/update`, `/admin`?
- Do any handlers contain embedded business logic (e.g., result post-processing, custom routing)?
- Are you using `/spell`, `/suggest`, `/terms`, `/export`, `/stream`, or `/sql` handlers?

### Search Components
- Do you have custom `SearchComponent` implementations in your handler chain?
- Are you using `SpellCheckComponent`, `SuggestComponent`, `MoreLikeThisComponent`, or `DebugComponent`?
- Is the component ordering in `solrconfig.xml` significant to your search behavior?

### Update Request Processors (URP)
- Do you have custom `UpdateRequestProcessorChain` configurations?
- Are you using any of: `StatelessScriptUpdateProcessorFactory`, `RegexReplaceProcessorFactory`, `CloneFieldUpdateProcessorFactory`, `FieldMutatingUpdateProcessor`?
- Is data enrichment or transformation happening at ingest time via URP?

### Authentication & Authorization
- Which authentication method is configured? (BasicAuth, Kerberos, PKI, custom plugin)
- Is authorization configured? (Rule-Based Authorization Plugin, custom)
- Are there per-collection or per-path access controls?
- Is TLS configured for inter-node and client communication?

### Plugins & Extensions
- Are you using any third-party or custom Solr plugins (JARs in `lib/` or `solr.xml`)?
- Are there custom `TokenFilter`, `Tokenizer`, or `CharFilter` implementations?
- Are you using Solr contrib modules? Which ones? (analysis-extras, clustering, langid, velocity, etc.)

### Operational Patterns
- Are you using Solr aliases? (standard, routed/time-routed)
- Is collection creation automated or manual?
- Are you using config sets shared across multiple collections?
- Is there a CI/CD pipeline for config changes, or are they applied manually?

## Solr → OpenSearch Mapping Table

| Solr Customization | OpenSearch Equivalent | Migration Effort |
|----|----|----|
| Custom `RequestHandler` | Standard Search API + client-side logic, or custom REST plugin | High — requires redesign |
| `SearchComponent` chain | No equivalent — rebuild as client-side orchestration or OpenSearch plugin | High |
| `UpdateRequestProcessorChain` | Ingest pipeline with processors | Medium — conceptual match, syntax differs |
| `StatelessScriptUpdateProcessor` | Script processor in ingest pipeline | Medium |
| `RegexReplaceProcessor` | Gsub processor in ingest pipeline | Low |
| `CloneFieldUpdateProcessor` | Set processor or copy_to in mappings | Low |
| BasicAuth | Security plugin — internal users database | Low |
| Kerberos | Proxy-based auth or LDAP backend via Security plugin | High |
| PKI / client certificates | Security plugin — client certificate auth | Medium |
| Rule-Based Authorization | Security plugin — roles and role mappings | Medium |
| TLS (inter-node) | Security plugin — transport layer TLS | Medium |
| Custom `TokenFilter` / `Tokenizer` | Custom analysis plugin, or map to built-in equivalent | High if custom; Low if built-in exists |
| Solr aliases | OpenSearch aliases | Low |
| Time-routed aliases | ISM rollover policies | Medium |
| Config sets | Index templates | Medium — different model (ZK config vs. REST API templates) |
| Collection API | Index API + index templates | Low — similar concepts, different REST endpoints |
| `/spell` handler | `suggest` API or `term` suggester | Medium |
| `/suggest` handler | Completion suggester with `completion` field type | Medium |
| `/stream` (Streaming Expressions) | No equivalent — PPL, SQL plugin, or application logic | High — requires redesign |
| `/sql` handler | SQL plugin | Medium — similar but not identical syntax |
| `/export` handler | Scroll API or Point-in-Time (PIT) + `search_after` | Medium |
| SolrJ client | `opensearch-java` client | High — completely different API surface |
| pysolr | `opensearch-py` | Medium — simpler API, less change surface |
| Velocity response writer | No equivalent — move rendering to application layer | Medium |
| XSLT response writer | No equivalent — move transformation to application layer | Medium |
