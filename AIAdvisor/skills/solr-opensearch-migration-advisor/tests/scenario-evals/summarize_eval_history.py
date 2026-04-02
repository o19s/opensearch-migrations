"""
Summarize eval run history as a Markdown trend table.

Reads all timestamped run bundles from a history directory (produced by
``run_eval_tasks.py --history-dir``), extracts key metrics from each, and
renders a Markdown table sorted chronologically.  Useful for spotting score
drift or pass-rate regressions across many runs.

Output columns
--------------
``Run``
    Timestamp and optional label from ``run_metadata``.
``Model``
    Judge model used.
``Pass``
    ``passed / total`` scenario count.
``Rate``
    Pass rate as a percentage.
``Overall``
    Average score across all scenarios and dimensions (1–5).
One column per ``SCORE_FIELDS`` dimension (abbreviated).
``Baseline``
    ``✓`` if the bundle includes a passing baseline comparison,
    ``✗`` if a regression was detected, ``—`` if not run.

Usage::

    # Print to stdout
    python summarize_eval_history.py --history-dir tests/evals/history

    # Write to TREND.md inside the history dir
    python summarize_eval_history.py \\
        --history-dir tests/evals/history \\
        --write-trend

    # Also compare the most recent run against the previous one
    python summarize_eval_history.py \\
        --history-dir tests/evals/history \\
        --delta
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCORE_FIELDS = (
    "methodology_alignment",
    "expert_judgement",
    "heuristics",
    "risk_identification",
)
SCORE_ABBREV = {
    "methodology_alignment": "Meth",
    "expert_judgement": "ExptJ",
    "heuristics": "Heur",
    "risk_identification": "RiskID",
}
OPTIONAL_SCORE_FIELDS = (
    "artifact_completeness",
    "approval_discipline",
    "consumer_impact_awareness",
    "cutover_readiness",
)
OPTIONAL_ABBREV = {
    "artifact_completeness": "ArtComp",
    "approval_discipline": "AppDisc",
    "consumer_impact_awareness": "ConsImp",
    "cutover_readiness": "CutRdy",
}


def load_bundle(path: Path) -> dict | None:
    """Load a run bundle from *path*, returning None on parse failure."""
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: skipping {path.name}: {exc}", file=sys.stderr)
        return None


def extract_row(bundle: dict, path: Path) -> dict:
    """Extract a flat summary row dict from a run bundle.

    Returns a dict with keys: ``created_at``, ``label``, ``model``,
    ``pass_count``, ``total``, ``pass_rate``, ``overall``,
    one key per ``SCORE_FIELDS`` dimension, one per ``OPTIONAL_SCORE_FIELDS``
    dimension (None if not present), and ``baseline_ok`` (True/False/None).
    """
    meta = bundle.get("run_metadata", {})
    summary = bundle.get("summary", {})
    avg = summary.get("average_scores", {})
    opt_avg = summary.get("average_optional_scores", {})
    bc = bundle.get("baseline_comparison")

    baseline_ok: bool | None = None
    if bc is not None:
        baseline_ok = not bc.get("regression_detected", True)

    row = {
        "path": path.name,
        "created_at": meta.get("created_at", ""),
        "label": meta.get("run_label") or "",
        "model": meta.get("model") or "",
        "pass_count": summary.get("pass_count", 0),
        "total": summary.get("scored_scenario_count", 0),
        "pass_rate": summary.get("pass_rate", 0.0),
        "overall": avg.get("overall", 0.0),
        "baseline_ok": baseline_ok,
    }
    for field in SCORE_FIELDS:
        row[field] = avg.get(field)
    for field in OPTIONAL_SCORE_FIELDS:
        row[field] = opt_avg.get(field)
    return row


def _fmt_score(val: float | None) -> str:
    if val is None:
        return "—"
    return f"{val:.2f}"


def _fmt_baseline(ok: bool | None) -> str:
    if ok is None:
        return "—"
    return "✓" if ok else "✗"


def _run_label(row: dict) -> str:
    ts = row["created_at"][:16].replace("T", " ") if row["created_at"] else "—"
    label = row["label"]
    return f"{ts} {label}".strip()


def render_markdown_table(rows: list[dict], show_optional: bool = False) -> str:
    """Render the history rows as a Markdown table string.

    Args:
        rows:           List of row dicts from :func:`extract_row`, chronological.
        show_optional:  If True, include optional score columns where any row
                        has data.
    """
    # Determine which optional fields have any data
    active_optional = [
        f for f in OPTIONAL_SCORE_FIELDS
        if any(r.get(f) is not None for r in rows)
    ] if show_optional else []

    headers = ["Run", "Model", "Pass", "Rate", "Overall"]
    headers += [SCORE_ABBREV[f] for f in SCORE_FIELDS]
    headers += [OPTIONAL_ABBREV[f] for f in active_optional]
    headers += ["Baseline"]

    sep = [":---"] + ["---:"] * (len(headers) - 2) + [":---:"]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(sep) + " |",
    ]

    for row in rows:
        cells = [
            _run_label(row),
            row["model"] or "—",
            f'{row["pass_count"]} / {row["total"]}',
            f'{row["pass_rate"]:.0%}',
            _fmt_score(row["overall"]),
        ]
        cells += [_fmt_score(row.get(f)) for f in SCORE_FIELDS]
        cells += [_fmt_score(row.get(f)) for f in active_optional]
        cells += [_fmt_baseline(row["baseline_ok"])]
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def render_delta_section(rows: list[dict]) -> str:
    """Render a short Markdown block comparing the two most recent rows.

    Returns an empty string if fewer than two rows are available.
    """
    if len(rows) < 2:
        return ""
    prev, curr = rows[-2], rows[-1]

    lines = ["", "## Delta: last two runs", ""]
    for field, label in [
        ("overall", "Overall avg"),
        ("pass_rate", "Pass rate"),
        *[(f, SCORE_ABBREV[f]) for f in SCORE_FIELDS],
    ]:
        p = prev.get(field)
        c = curr.get(field)
        if p is None or c is None:
            continue
        diff = c - p
        arrow = "▲" if diff > 0.001 else ("▼" if diff < -0.001 else "→")
        lines.append(f"- **{label}**: {p:.4f} → {c:.4f} {arrow} ({diff:+.4f})")

    prev_bc = _fmt_baseline(prev["baseline_ok"])
    curr_bc = _fmt_baseline(curr["baseline_ok"])
    if prev_bc != curr_bc:
        lines.append(f"- **Baseline**: {prev_bc} → {curr_bc}")

    return "\n".join(lines)


def load_history(history_dir: Path) -> list[dict]:
    """Load all run bundles from *history_dir/runs/*, sorted by filename.

    Filenames are ISO-timestamp prefixed so lexicographic order is
    chronological.  Bundles that fail to parse are skipped with a warning.

    Returns:
        List of row dicts, sorted oldest-first.
    """
    runs_dir = history_dir / "runs"
    if not runs_dir.is_dir():
        return []
    paths = sorted(runs_dir.glob("*.json"))
    rows = []
    for p in paths:
        bundle = load_bundle(p)
        if bundle is not None:
            rows.append(extract_row(bundle, p))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize eval run history as a Markdown trend table."
    )
    parser.add_argument(
        "--history-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "history",
        help="Directory containing runs/ and latest.json (default: tests/evals/history).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write the Markdown output (default: stdout).",
    )
    parser.add_argument(
        "--write-trend",
        action="store_true",
        help="Write output to TREND.md inside --history-dir (in addition to stdout).",
    )
    parser.add_argument(
        "--delta",
        action="store_true",
        help="Append a delta section comparing the two most recent runs.",
    )
    parser.add_argument(
        "--show-optional",
        action="store_true",
        help="Include optional score columns (artifact, approval, etc.) when present.",
    )
    args = parser.parse_args()

    rows = load_history(args.history_dir)
    if not rows:
        print(
            f"No run bundles found in {args.history_dir / 'runs'}.  "
            "Run eval_tasks.py with --history-dir first.",
            file=sys.stderr,
        )
        return 1

    table = render_markdown_table(rows, show_optional=args.show_optional)
    delta = render_delta_section(rows) if args.delta else ""
    output = f"# Eval History\n\n{table}\n{delta}\n"

    if args.output is not None:
        args.output.write_text(output, encoding="utf-8")
        print(args.output)
    elif args.write_trend:
        trend_path = args.history_dir / "TREND.md"
        trend_path.write_text(output, encoding="utf-8")
        print(trend_path)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
