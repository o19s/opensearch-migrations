# opensearch-migrations — Claude Code Instructions

## Minimal PR Discipline

When building incremental proof-of-concept PRs:

- **Only add what the PR title promises.** If the title says "Kiro packaging smoke test",
  don't fix empty files, backfill missing content, or improve things that aren't broken.
- **If a test catches something out of scope, skip it — don't fix the underlying issue.**
  Use `pytest.skip()` or `xfail` with a note pointing to the future PR where it belongs.
- **Assume reviewers are overworked and easily distracted.** Every file touched is a
  potential question. Every line changed is a potential objection. Minimize surface area.
- **When in doubt, remove rather than add.** A PR that does less is easier to approve
  than one that does more.
- **No drive-by fixes.** Spotted a typo? Empty file? Missing docstring? Leave it.
  That's a different PR (or not worth a PR at all).
