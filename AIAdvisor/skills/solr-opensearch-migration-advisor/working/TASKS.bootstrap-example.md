# Tasks

This is the default shared task tracker for active repo work.

Convention:

- use this file when the user and agent want a shared, persistent task list
- prefer markdown checkboxes
- keep items short and concrete
- move completed work into `Done Recently` instead of deleting it immediately

## Now

- [ ] Rehearse the `Hello Migration` demo end to end using `project/demos/hello-migration-demo-script.md`.
- [ ] Finalize the exact live prompt sequence for the YOLO/Express step and the short advisor step.
- [ ] Decide whether the LLM-vs-deterministic comparison is part of the mainline demo or a backup branch.
- [ ] Verify which files/windows to keep open during the live demo:
  - `project/demos/hello-migration-demo-script.md`
  - `project/demos/llm-vs-deterministic-query-translation-demo.md`
  - `scripts/demo_query_translation.py`
- [ ] Capture a short post-rehearsal note on where the `Hello Migration` flow still feels awkward or too hand-wavy.

## Next

- [ ] Prepare the Drupal demo as the next story after `Hello Migration`.
- [ ] Decide whether to deepen demo support next or return to richer Solr functionality work.
- [ ] If functionality is next, prioritize the next deterministic gaps after the demo path:
  - richer `edismax`
  - `mm`
  - `pf`
  - `bq` / boost handling
- [ ] Consider whether `working/TASKS.md` should be loaded as a tracked checklist in a named session by default during demo prep.

## Blocked

- [ ] No current blockers.

## Done Recently

- [x] Created the default shared task tracker at `working/TASKS.md`.
- [x] Added the shared task-tracker convention to `AGENTS.md`.
- [x] Added lightweight checklist parsing, named checklists, and file-backed checklist tracking to the skill.
- [x] Reorganized `project/` into clearer sections with a top-level `README.md`.
- [x] Added the five-story Solr migration demo ladder and the dedicated `Hello Migration` demo script.
