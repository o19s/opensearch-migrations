---
inclusion: always
---

# Technology Stack

## Core

- **Python 3.11+** with `uv` for dependency management
- **AWS Bedrock** as the LLM provider (Claude models)
- **Agent Skills standard** for portable skill packaging

## Search Platforms

- **Apache Solr** (source) -- XML schema, SolrCloud, DisMax/eDisMax queries
- **Amazon OpenSearch Service** (target) -- JSON mappings, OpenSearch Query DSL

## Testing

- **pytest** for unit tests
- **promptfoo** for LLM evaluation and assertion testing
- **Docker** for live Solr integration tests

## Constraints

- All LLM calls go through AWS Bedrock (no direct API keys)
- Skill must work in Kiro IDE, Kiro CLI, and headless (CI) modes
- Accuracy over speed -- never guess a translation
