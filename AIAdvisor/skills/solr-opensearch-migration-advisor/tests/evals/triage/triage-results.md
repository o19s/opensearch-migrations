# Stumper triage — bare model results

Both models run from `/tmp` with no skill discovery, no references.
Targets: `claude-haiku-4-5-20251001` (cloud) and `qwen2.5:7b` (local Ollama).
Criteria are the contains-any patterns from `stumper-candidates.md`.
RED = criterion missed = candidate stumper for this model.

| QID | Title | Haiku A | Haiku B | Qwen A | Qwen B | Both fail? |
| --- | ----- | :-----: | :-----: | :----: | :----: | :--------: |
| q05-smui-opensearch-scope | SMUI v4.0.11 OpenSearch scope (labelling vs deployment) | RED | RED | RED | RED | YES |

Generated 2026-05-10 16:37:22.