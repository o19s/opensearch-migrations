# Artifact Templates

These templates define the **default artifact set** that the migration advisor
auto-generates into the `artifacts/` directory.  Each artifact is saved with a
timestamped filename (`{type}-{session}-{yyyyMMddHHmm}.md`) so that successive
snapshots coexist and show migration progress over time.

## Artifact inventory

| # | Template | Audience | Generated when |
|---|----------|----------|----------------|
| 1 | `intake-worksheet.md` | PM, tech lead | Session start (Step 0-1) |
| 2 | `stakeholder-register.md` | PM, product champion, exec sponsor | Step 0 (stakeholder ID) |
| 3 | `progress-dashboard.md` | Everyone (exec summary + tech detail) | Any step; refreshed on report |
| 4 | `incompatibility-tracker.md` | Engineers, PM | Steps 2-4 (schema/query/custom) |
| 5 | `migration-report.md` | Everyone | Step 7 (report generation) — already implemented |

## Design principles

- **One URL per artifact.** Stakeholders bookmark the `artifacts/` directory,
  not individual files.  Timestamps let them see what changed.
- **Executive summary up top.** Non-technical readers stop at the first table.
  Engineers scroll down.
- **Generated from session state.** Templates are populated from `SessionState`
  fields — no manual data entry required.
- **Additive history.** Files are never overwritten.  A future UI will show
  diffs between snapshots to visualize migration progress.
