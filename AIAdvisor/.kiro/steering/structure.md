---
inclusion: always
---

# Project Structure

```
AIAdvisor/
  .kiro/
    steering/             # Kiro steering files (product, tech, structure)
    skills/
      solr-to-opensearch/ # Symlink to the skill directory
    hooks/
      schema-assist.kiro.hook   # Auto-trigger on schema file edits
  skills/
    solr-opensearch-migration-advisor/
      SKILL.md            # Agent skill definition (frontmatter + instructions)
      README.md           # Developer guide and example prompts
      KIRO.md             # Kiro appendix -- why Kiro, comparison with alternatives
      steering/           # Domain steering files (accuracy, sizing, etc.)
      references/         # Reference documents loaded on demand
      scripts/            # Python skill implementation
        skill.py          # Main skill orchestrator
        schema_converter.py
        query_converter.py
        report.py
        storage.py
      tests/              # pytest unit tests
        skill-smoke/      # Step-by-step smoke tests (PR #11)
        connected/        # Integration tests requiring live services
        evals/            # promptfoo evaluation configs
```

## Naming Conventions

- Steering files: lowercase with underscores (`query_translation.md`)
- Scripts: lowercase with underscores (`schema_converter.py`)
- Kiro hooks: kebab-case with `.kiro.hook` suffix
- Skill name in SKILL.md frontmatter must be lowercase-hyphenated
