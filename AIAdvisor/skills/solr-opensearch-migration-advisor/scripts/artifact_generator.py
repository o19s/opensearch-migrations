"""
Auto-generate stakeholder-facing artifacts from migration session state.

Each generator reads :class:`~storage.SessionState` and produces a Markdown
file in the ``artifacts/`` directory with a timestamped filename.  Successive
snapshots coexist so that a future UI can show migration progress over time.

Artifact types
--------------
* **progress-dashboard** — executive summary + per-phase technical detail.
* **intake-worksheet**   — quick-facts table populated from discovered session data.
* **incompatibility-tracker** — standalone view of all discovered incompatibilities.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from storage import SessionState


# Step names used in the progress dashboard.
_PHASE_NAMES = [
    "Stakeholder identification",
    "Schema acquisition",
    "Schema review & incompatibilities",
    "Query translation",
    "Customization assessment",
    "Infrastructure planning",
    "Client integration assessment",
    "Report & recommendations",
]


def _default_artifacts_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")


def _save(content: str, artifact_type: str, session_id: str,
          artifacts_dir: Optional[str], now: Optional[datetime]) -> str:
    d = artifacts_dir or _default_artifacts_dir()
    os.makedirs(d, exist_ok=True)
    ts = (now or datetime.now(timezone.utc)).strftime("%Y%m%d%H%M")
    filename = f"{artifact_type}-{session_id}-{ts}.md"
    path = os.path.join(d, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return os.path.abspath(path)


def _val(state: "SessionState", key: str, default: str = "\u2014") -> str:
    """Return a fact value as a display string, or *default* if missing."""
    v = state.facts.get(key)
    if v is None or v == "":
        return default
    return str(v)


def _phase_status(state: "SessionState", step: int) -> str:
    if state.progress > step:
        return "Done"
    if state.progress == step:
        return "In progress"
    return "Not started"


# ------------------------------------------------------------------
# Progress dashboard
# ------------------------------------------------------------------

def generate_progress_dashboard(
    state: "SessionState",
    artifacts_dir: Optional[str] = None,
    *,
    now: Optional[datetime] = None,
) -> str:
    """Render and save the progress dashboard artifact.

    Returns the absolute path of the saved file.
    """
    breaking = [i for i in state.incompatibilities if i.severity == "Breaking"]
    unsupported = [i for i in state.incompatibilities if i.severity == "Unsupported"]
    behavioral = [i for i in state.incompatibilities if i.severity == "Behavioral"]
    ts = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")

    if state.progress >= 7:
        overall = "Report generated"
    elif state.progress > 0:
        overall = f"Phase {state.progress} in progress"
    else:
        overall = "Not started"

    lines = [
        "# Migration Progress Dashboard",
        "",
        f"**Session:** {state.session_id}",
        f"**Generated:** {ts}",
        f"**Overall status:** {overall}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "| Phase | Status | Blockers |",
        "|-------|--------|----------|",
    ]

    for step, name in enumerate(_PHASE_NAMES):
        status = _phase_status(state, step)
        blocker = "None"
        if step == 1 and not state.facts.get("schema_migrated"):
            blocker = "Schema not yet provided"
        elif step == 7 and (breaking or unsupported):
            blocker = f"{len(breaking) + len(unsupported)} blocking incompatibilities"
        lines.append(f"| {step}. {name} | {status} | {blocker} |")

    lines += [
        "",
        f"**Incompatibility snapshot:** {len(breaking)} breaking"
        f" | {len(unsupported)} unsupported | {len(behavioral)} behavioral",
        "",
        f"**Blocking risks:** {len(breaking) + len(unsupported)}",
        "",
        "> *Managers / execs: the table above is the status.  Scroll down only if you",
        "> want technical detail.*",
        "",
        "---",
        "",
        "## Phase Detail",
        "",
        "### Phase 0 \u2014 Stakeholder Identification",
        "",
        f"- **Stakeholder role:** {_val(state, 'stakeholder_role', 'Not identified')}",
        "",
        "### Phase 1 \u2014 Schema Acquisition",
        "",
        f"- **Source format:** {_val(state, 'schema_source', 'Not provided')}",
        f"- **Collection:** {_val(state, 'solr_collection')}",
        f"- **Document count:** {_val(state, 'solr_num_docs')}",
        f"- **Schema converted:** {'Yes' if state.facts.get('schema_migrated') else 'No'}",
        "",
        "### Phase 2 \u2014 Schema Review",
        "",
        f"- **Incompatibilities found:** {len(state.incompatibilities)}",
        f"- **Review notes:** {_val(state, 'schema_review_notes', 'None recorded')}",
        "",
        "### Phase 3 \u2014 Query Translation",
        "",
        f"- **Queries translated:** {_val(state, 'queries_translated', '0')}",
        "",
        "### Phase 4 \u2014 Customization Assessment",
        "",
        f"- **Assessed:** {'Yes' if state.facts.get('customizations_assessed') else 'No'}",
        f"- **Auth method:** {_val(state, 'auth_method')}",
        "",
        "### Phase 5 \u2014 Infrastructure Planning",
        "",
        f"- **Solr version:** {_val(state, 'solr_version')}",
        f"- **Target platform:** {_val(state, 'target_platform')}",
        f"- **Nodes:** {_val(state, 'solr_node_count')}",
        "",
        "### Phase 6 \u2014 Client Integration Assessment",
        "",
    ]

    if state.client_integrations:
        lines.append("| Integration | Type | Migration action |")
        lines.append("|------------|------|-----------------|")
        for c in state.client_integrations:
            lines.append(f"| {c.name} | {c.kind} | {c.migration_action} |")
    else:
        lines.append("- No client integrations recorded yet.")

    lines += [
        "",
        "### Phase 7 \u2014 Report & Recommendations",
        "",
        f"- **Report generated:** {'Yes' if state.progress >= 7 else 'No'}",
        "",
        "---",
        "",
        "*Auto-generated from session state.  Re-run the advisor to refresh.*",
    ]

    content = "\n".join(lines)
    return _save(content, "progress", state.session_id, artifacts_dir, now)


# ------------------------------------------------------------------
# Intake worksheet
# ------------------------------------------------------------------

def generate_intake_worksheet(
    state: "SessionState",
    artifacts_dir: Optional[str] = None,
    *,
    now: Optional[datetime] = None,
) -> str:
    """Render and save the intake worksheet artifact.

    Returns the absolute path of the saved file.
    """
    ts = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    schema_migrated = state.facts.get("schema_migrated", False)

    if state.progress >= 2:
        intake_status = "Complete"
    elif state.progress >= 1:
        intake_status = "Schema acquired, review pending"
    else:
        intake_status = "In progress"

    lines = [
        "# Migration Intake Worksheet",
        "",
        f"**Session:** {state.session_id}",
        f"**Generated:** {ts}",
        f"**Status:** {intake_status}",
        "",
        "---",
        "",
        "## Quick Facts",
        "",
        "| Item | Value |",
        "|------|-------|",
        f"| Solr version | {_val(state, 'solr_version')} |",
        f"| Collection(s) | {_val(state, 'solr_collection')} |",
        f"| Document count | {_val(state, 'solr_num_docs')} |",
        f"| Target platform | {_val(state, 'target_platform')} |",
        "",
        "## Schema Summary",
        "",
        f"- **Schema source:** {_val(state, 'schema_source', 'Not provided')}",
        f"- **Conversion status:** {'Converted' if schema_migrated else 'Not converted'}",
        "",
        "## Query Profile",
        "",
        f"- **Queries translated:** {_val(state, 'queries_translated', '0')}",
        "",
        "## Customizations",
        "",
    ]

    customizations = state.facts.get("customizations", {})
    if customizations:
        lines.append("| Solr feature | OpenSearch solution |")
        lines.append("|-------------|-------------------|")
        for solr_item, os_solution in customizations.items():
            lines.append(f"| {solr_item} | {os_solution} |")
    else:
        lines.append("- No customizations recorded yet.")

    lines += [
        "",
        "## Security & Access Control",
        "",
        f"- **Auth method:** {_val(state, 'auth_method')}",
        "",
        "## Open Questions",
        "",
        "| # | Question | Owner | Priority | Status |",
        "|---|----------|-------|----------|--------|",
    ]

    question_num = 1
    if not state.facts.get("schema_migrated"):
        lines.append(f"| {question_num} | Schema not yet provided or converted"
                      " | Tech lead | High | Open |")
        question_num += 1
    if not state.facts.get("customizations_assessed"):
        lines.append(f"| {question_num} | Customizations not yet assessed"
                      " | Search engineer | Medium | Open |")
        question_num += 1
    if not state.facts.get("target_platform"):
        lines.append(f"| {question_num} | Target platform not decided"
                      " | Architect | High | Open |")
        question_num += 1
    if question_num == 1:
        lines.append("| | No open questions | | | |")

    lines += [
        "",
        "---",
        "",
        "*Auto-generated from session state.  Missing values indicate information"
        " not yet gathered.*",
    ]

    content = "\n".join(lines)
    return _save(content, "intake", state.session_id, artifacts_dir, now)


# ------------------------------------------------------------------
# Incompatibility tracker
# ------------------------------------------------------------------

def generate_incompatibility_tracker(
    state: "SessionState",
    artifacts_dir: Optional[str] = None,
    *,
    now: Optional[datetime] = None,
) -> str:
    """Render and save the incompatibility tracker artifact.

    Returns the absolute path of the saved file.
    """
    ts = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    breaking = [i for i in state.incompatibilities if i.severity == "Breaking"]
    unsupported = [i for i in state.incompatibilities if i.severity == "Unsupported"]
    behavioral = [i for i in state.incompatibilities if i.severity == "Behavioral"]
    total = len(state.incompatibilities)

    lines = [
        "# Incompatibility Tracker",
        "",
        f"**Session:** {state.session_id}",
        f"**Generated:** {ts}",
        f"**Total:** {total} | **Breaking:** {len(breaking)}"
        f" | **Unsupported:** {len(unsupported)}"
        f" | **Behavioral:** {len(behavioral)}",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Cutover-blocking items | {len(breaking) + len(unsupported)} |",
        f"| Total items | {total} |",
        "",
    ]

    for severity, items, prefix in [
        ("Breaking", breaking, "B"),
        ("Unsupported", unsupported, "U"),
        ("Behavioral", behavioral, "V"),
    ]:
        lines.append(f"## {severity}")
        lines.append("")
        if severity == "Breaking":
            lines.append("*Must be resolved before cutover.*")
        elif severity == "Unsupported":
            lines.append("*No direct OpenSearch equivalent. Require redesign or removal.*")
        else:
            lines.append("*Exist in both platforms but behave differently. Monitor during testing.*")
        lines.append("")

        if items:
            lines.append("| ID | Category | Description | Recommendation |")
            lines.append("|----|----------|-------------|----------------|")
            for idx, item in enumerate(items, 1):
                lines.append(
                    f"| {prefix}-{idx} | {item.category}"
                    f" | {item.description} | {item.recommendation} |"
                )
        else:
            lines.append(f"- No {severity.lower()} incompatibilities found.")
        lines.append("")

    lines += [
        "---",
        "",
        "*Auto-generated from session state.  Re-run the advisor to refresh.*",
    ]

    content = "\n".join(lines)
    return _save(content, "incompatibilities", state.session_id, artifacts_dir, now)
