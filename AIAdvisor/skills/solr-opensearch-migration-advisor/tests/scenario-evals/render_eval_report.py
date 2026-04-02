"""
Render a scored eval run bundle as a self-contained HTML report.

Reads a run bundle produced by ``run_eval_tasks.py`` (or
``run_end_to_end_skill_eval.py``) and writes a single, dependency-free HTML
file suitable for opening in any browser.

The report contains:
- Run metadata header (timestamp, model, label, dataset)
- Summary grid: pass/fail counts, pass rate, per-dimension average scores
- Baseline comparison table (if the bundle includes ``baseline_comparison``)
- Per-scenario cards with score breakdowns and expandable judge rationale
- Stability annotations (if ``--repeat-judge > 1`` was used)

Usage::

    python render_eval_report.py \\
        --bundle tests/evals/history/latest.json \\
        --output /tmp/eval-report.html

    # Open immediately (macOS/Linux)
    open /tmp/eval-report.html
    xdg-open /tmp/eval-report.html
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


SCORE_FIELDS = (
    "methodology_alignment",
    "expert_judgement",
    "heuristics",
    "risk_identification",
)
OPTIONAL_SCORE_FIELDS = (
    "artifact_completeness",
    "approval_discipline",
    "consumer_impact_awareness",
    "cutover_readiness",
)
SCORE_LABELS = {
    "methodology_alignment": "Methodology",
    "expert_judgement": "Expert Judgement",
    "heuristics": "Heuristics",
    "risk_identification": "Risk ID",
    "artifact_completeness": "Artifact Completeness",
    "approval_discipline": "Approval Discipline",
    "consumer_impact_awareness": "Consumer Impact",
    "cutover_readiness": "Cutover Readiness",
}


def load_bundle(path: Path) -> dict:
    """Load and return a run bundle from *path*."""
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def score_pct(score: float) -> int:
    """Convert a 1–5 score to a 0–100 fill percentage for the score bar."""
    return max(0, min(100, round((score - 1) / 4 * 100)))


def score_color(score: float) -> str:
    """Return a CSS color name based on the 1–5 score."""
    if score >= 4.0:
        return "#16a34a"   # green
    if score >= 3.5:
        return "#ca8a04"   # amber
    return "#dc2626"        # red


def e(text) -> str:
    """HTML-escape *text*, converting None to an empty string."""
    return html.escape(str(text)) if text is not None else ""


def render_score_bar(score: float) -> str:
    pct = score_pct(score)
    color = score_color(score)
    return (
        f'<span class="score-bar">'
        f'<span class="score-fill" style="width:{pct}%;background:{color}"></span>'
        f'</span>'
    )


def render_score_row(scores: dict, fields: tuple) -> str:
    items = []
    for field in fields:
        if field not in scores:
            continue
        label = SCORE_LABELS.get(field, field)
        val = scores[field]
        items.append(
            f'<span class="score-item">'
            f'<span class="dim">{e(label)}</span> '
            f'{render_score_bar(val)}'
            f'<strong>{val:.2f}</strong>'
            f'</span>'
        )
    return '<div class="score-row">' + "".join(items) + "</div>"


def render_metadata(meta: dict) -> str:
    rows = []
    for key, label in [
        ("created_at", "Run time"),
        ("run_label", "Label"),
        ("model", "Judge model"),
        ("score_mode", "Score mode"),
        ("dataset_path", "Dataset"),
    ]:
        val = meta.get(key)
        if val:
            rows.append(f"<dt>{e(label)}</dt><dd>{e(val)}</dd>")
    return f'<dl class="meta-grid">{"".join(rows)}</dl>'


def render_summary(summary: dict) -> str:
    avg = summary.get("average_scores", {})
    overall = avg.get("overall", 0.0)
    pass_rate = summary.get("pass_rate", 0.0)
    pass_count = summary.get("pass_count", 0)
    fail_count = summary.get("fail_count", 0)
    total = summary.get("scored_scenario_count", 0)

    pass_cls = "pass" if fail_count == 0 else ("warn" if pass_rate >= 0.8 else "fail")

    cards = []
    cards.append(
        f'<div class="metric-card">'
        f'<div class="value {pass_cls}">{pass_rate:.0%}</div>'
        f'<div class="label">Pass Rate</div>'
        f'</div>'
    )
    cards.append(
        f'<div class="metric-card">'
        f'<div class="value">{pass_count}<span style="color:#666;font-size:1rem"> / {total}</span></div>'
        f'<div class="label">Passed</div>'
        f'</div>'
    )
    cards.append(
        f'<div class="metric-card">'
        f'<div class="value" style="color:{score_color(overall)}">{overall:.2f}</div>'
        f'<div class="label">Overall Avg (1–5)</div>'
        f'</div>'
    )
    for field in SCORE_FIELDS:
        val = avg.get(field, 0.0)
        label = SCORE_LABELS.get(field, field)
        cards.append(
            f'<div class="metric-card">'
            f'<div class="value" style="color:{score_color(val)}">{val:.2f}</div>'
            f'<div class="label">{e(label)}</div>'
            f'</div>'
        )

    opt_avg = summary.get("average_optional_scores", {})
    for field in OPTIONAL_SCORE_FIELDS:
        if field in opt_avg:
            val = opt_avg[field]
            label = SCORE_LABELS.get(field, field)
            cards.append(
                f'<div class="metric-card" style="border-style:dashed">'
                f'<div class="value" style="color:{score_color(val)}">{val:.2f}</div>'
                f'<div class="label">{e(label)} <em>(opt)</em></div>'
                f'</div>'
            )

    return '<div class="summary-grid">' + "".join(cards) + "</div>"


def render_baseline_comparison(bc: dict) -> str:
    if not bc:
        return ""
    m = bc.get("metrics", {})
    regressions = bc.get("regressions", [])
    detected = bc.get("regression_detected", False)
    status_cls = "fail" if detected else "pass"
    status_text = "REGRESSION DETECTED" if detected else "No regression"

    rows = ""
    for key, label in [
        ("candidate_overall_average", "Overall avg (this run)"),
        ("baseline_overall_average", "Overall avg (baseline)"),
        ("overall_score_drop", "Score drop"),
        ("candidate_pass_rate", "Pass rate (this run)"),
        ("baseline_pass_rate", "Pass rate (baseline)"),
        ("pass_rate_drop", "Pass rate drop"),
    ]:
        val = m.get(key)
        if val is not None:
            rows += f"<tr><td>{e(label)}</td><td>{val:.4f}</td></tr>"

    reg_html = ""
    if regressions:
        items = "".join(f"<li>{e(r)}</li>" for r in regressions)
        reg_html = f'<ul class="regression-list">{items}</ul>'

    return f"""
<section>
  <h2>Baseline Comparison</h2>
  <p class="{status_cls}"><strong>{status_text}</strong></p>
  <table class="comparison-table">
    <thead><tr><th>Metric</th><th>Value</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  {reg_html}
</section>
"""


def render_scenario_card(result: dict) -> str:
    sid = e(result.get("scenario_id") or result.get("title") or "—")
    title = e(result.get("title") or result.get("scenario_id") or "Untitled")
    judge = result.get("judge_output", {})
    decision = judge.get("final_decision", "—")
    avg = judge.get("average_score", 0.0)
    badge_cls = "pass" if decision == "PASS" else "fail"
    scores = {f: judge[f] for f in SCORE_FIELDS if f in judge}
    opt_scores = {f: judge[f] for f in OPTIONAL_SCORE_FIELDS if f in judge}

    score_html = render_score_row(scores, SCORE_FIELDS)
    opt_html = (
        '<div style="margin-top:0.25rem">' + render_score_row(opt_scores, OPTIONAL_SCORE_FIELDS) + "</div>"
        if opt_scores else ""
    )

    rationale = judge.get("rationale") or judge.get("explanation") or ""
    rationale_html = ""
    if rationale:
        rationale_html = (
            f'<details><summary>Judge rationale</summary>'
            f'<div class="detail-content">{e(rationale)}</div>'
            f'</details>'
        )

    stability = result.get("stability_summary")
    stability_html = ""
    if stability:
        spread = stability.get("average_score_spread", 0.0)
        consensus = stability.get("decision_consensus", True)
        runs = stability.get("run_count", 1)
        stab_cls = "pass" if consensus and spread <= 0.5 else "warn"
        stability_html = (
            f'<details><summary>Stability ({runs} judge runs)</summary>'
            f'<div class="detail-content">'
            f'Avg score spread: {spread:.4f} &nbsp; '
            f'Decision consensus: <span class="{stab_cls}">{"yes" if consensus else "no"}</span>'
            f'</div></details>'
        )

    return f"""
<div class="scenario-card" id="{sid}">
  <div class="scenario-header">
    <span><strong>{title}</strong> <span class="scenario-id">#{sid}</span></span>
    <span>
      <span class="badge {badge_cls}">{e(decision)}</span>
      &nbsp; avg <strong>{avg:.2f}</strong>
    </span>
  </div>
  <div class="scenario-body">
    {score_html}
    {opt_html}
    {rationale_html}
    {stability_html}
  </div>
</div>
"""


CSS = """
body {
  font-family: system-ui, -apple-system, sans-serif;
  max-width: 1000px;
  margin: 2rem auto;
  padding: 0 1.25rem;
  color: #1f2937;
  line-height: 1.5;
}
h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
h2 { font-size: 1.1rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.25rem; margin-top: 2rem; }
.meta-grid { display: grid; grid-template-columns: max-content 1fr; gap: 0.1rem 0.75rem;
             font-size: 0.875rem; margin: 0.5rem 0 1rem; }
.meta-grid dt { color: #6b7280; font-weight: 600; }
.meta-grid dd { margin: 0; }
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0;
}
.metric-card {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0.6rem 0.75rem;
  text-align: center;
}
.metric-card .value { font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
.metric-card .label { font-size: 0.7rem; color: #6b7280; text-transform: uppercase;
                      letter-spacing: 0.04em; margin-top: 0.2rem; }
.pass { color: #16a34a; }
.fail { color: #dc2626; }
.warn { color: #ca8a04; }
.badge {
  display: inline-block;
  padding: 0.15em 0.55em;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.03em;
}
.badge.pass { background: #dcfce7; color: #15803d; }
.badge.fail { background: #fee2e2; color: #b91c1c; }
.scenario-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin: 0.75rem 0;
  overflow: hidden;
}
.scenario-card:has(.badge.fail) { border-color: #fca5a5; }
.scenario-header {
  padding: 0.6rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9fafb;
}
.scenario-id { font-size: 0.75rem; color: #9ca3af; font-weight: normal; }
.scenario-body { padding: 0.75rem 1rem; }
.score-row { display: flex; flex-wrap: wrap; gap: 0.75rem; margin: 0.25rem 0; }
.score-item { font-size: 0.85rem; white-space: nowrap; }
.score-item .dim { color: #6b7280; }
.score-bar {
  display: inline-block;
  width: 60px;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  vertical-align: middle;
  margin: 0 3px 1px;
  overflow: hidden;
}
.score-fill { height: 100%; border-radius: 3px; }
details { margin-top: 0.5rem; }
summary { cursor: pointer; color: #2563eb; font-size: 0.85rem; user-select: none; }
summary:hover { text-decoration: underline; }
.detail-content {
  margin-top: 0.4rem;
  padding: 0.6rem 0.75rem;
  background: #f8fafc;
  border-radius: 4px;
  font-size: 0.83rem;
  white-space: pre-wrap;
  border-left: 3px solid #cbd5e1;
}
.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  margin: 0.5rem 0;
}
.comparison-table th, .comparison-table td {
  text-align: left;
  padding: 0.4rem 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}
.comparison-table th { background: #f9fafb; font-weight: 600; }
.regression-list { color: #dc2626; font-size: 0.875rem; }
"""


def render_html(bundle: dict) -> str:
    meta = bundle.get("run_metadata", {})
    summary = bundle.get("summary", {})
    results = bundle.get("results", [])
    bc = bundle.get("baseline_comparison")

    label = meta.get("run_label") or "Eval Run"
    created = meta.get("created_at", "")
    title_text = f"{label} — {created[:10]}" if created else label

    scenario_cards = "".join(render_scenario_card(r) for r in results)
    baseline_html = render_baseline_comparison(bc) if bc else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Eval Report: {e(title_text)}</title>
  <style>{CSS}</style>
</head>
<body>
  <h1>Eval Report: {e(title_text)}</h1>
  {render_metadata(meta)}

  <h2>Summary</h2>
  {render_summary(summary)}

  {baseline_html}

  <h2>Scenario Results ({len(results)})</h2>
  {scenario_cards if scenario_cards else "<p>No scored results in this bundle.</p>"}
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a scored eval bundle as HTML.")
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="Path to a run bundle JSON (default: tests/evals/history/latest.json).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write the HTML report (default: stdout).",
    )
    args = parser.parse_args()

    bundle_path = args.bundle
    if bundle_path is None:
        bundle_path = Path(__file__).resolve().parent / "history" / "latest.json"

    if not bundle_path.exists():
        print(f"Bundle not found: {bundle_path}", file=sys.stderr)
        return 1

    bundle = load_bundle(bundle_path)
    report = render_html(bundle)

    if args.output is not None:
        args.output.write_text(report, encoding="utf-8")
        print(args.output)
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
