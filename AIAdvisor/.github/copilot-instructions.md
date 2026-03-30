# Solr to OpenSearch Migration Advisor — GitHub Copilot Instructions

## Skill Location
The migration advisor skill is at `skills/solr-opensearch-migration-advisor/`.
Read `skills/solr-opensearch-migration-advisor/SKILL.md` for the full agent skill definition.

## Domain Context
Consult the steering documents in `skills/solr-opensearch-migration-advisor/steering/`
before answering migration questions.

## Key Rules
- Accuracy > speed: never guess field type mappings or query translations
- Flag uncertain conversions explicitly rather than producing best-guesses
- Use Python 3.11+ with `uv` for package management; never install globally
