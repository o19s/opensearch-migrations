from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from storage import Incompatibility, ClientIntegration


class MigrationReport:
    """Generates a migration report from session context."""

    def __init__(
        self,
        milestones: List[str] = None,
        blockers: List[str] = None,
        implementation_points: List[str] = None,
        cost_estimates: Dict[str, str] = None,
        incompatibilities: List["Incompatibility"] = None,
        client_integrations: List["ClientIntegration"] = None,
    ):
        self.milestones = milestones or []
        self.blockers = blockers or []
        self.implementation_points = implementation_points or []
        self.cost_estimates = cost_estimates or {}
        self.incompatibilities = incompatibilities or []
        self.client_integrations = client_integrations or []

    def generate(self) -> str:
        report = []
        report.append("# Solr to OpenSearch Migration Report\n")

        # --- Incompatibilities (prominent, at the top) ---
        report.append("## Incompatibilities")
        if self.incompatibilities:
            for severity in ("Breaking", "Unsupported", "Behavioral"):
                items = [i for i in self.incompatibilities if i.severity == severity]
                if not items:
                    continue
                report.append(f"\n### {severity}")
                for item in items:
                    report.append(f"- **[{item.category}]** {item.description}")
                    report.append(f"  - *Recommendation:* {item.recommendation}")
            critical = [
                i for i in self.incompatibilities
                if i.severity in ("Breaking", "Unsupported")
            ]
            if critical:
                report.append(
                    "\n> **Action required:** The items above marked Breaking or "
                    "Unsupported must be resolved before cutover."
                )
        else:
            report.append("- No incompatibilities identified.")
        report.append("")

        # --- Client & Front-end Impact ---
        report.append("## Client & Front-end Impact")
        if self.client_integrations:
            # Group by kind for readability
            kind_order = ["library", "ui", "http", "other"]
            kind_labels = {
                "library": "Client Libraries",
                "ui": "Front-end / UI",
                "http": "HTTP / Custom Clients",
                "other": "Other Integrations",
            }
            rendered_kinds = set()
            for kind in kind_order:
                items = [c for c in self.client_integrations if c.kind == kind]
                if not items:
                    continue
                rendered_kinds.add(kind)
                report.append(f"\n### {kind_labels[kind]}")
                for c in items:
                    report.append(f"- **{c.name}**")
                    if c.notes:
                        report.append(f"  - *Current usage:* {c.notes}")
                    report.append(f"  - *Migration action:* {c.migration_action}")
            # Catch any kinds not in kind_order
            for c in self.client_integrations:
                if c.kind not in rendered_kinds and c.kind not in kind_order:
                    report.append(f"- **{c.name}** ({c.kind})")
                    if c.notes:
                        report.append(f"  - *Current usage:* {c.notes}")
                    report.append(f"  - *Migration action:* {c.migration_action}")
        else:
            report.append("- No client or front-end integrations recorded.")
        report.append("")

        # --- Milestones ---
        report.append("## Major Milestones")
        for i, m in enumerate(self.milestones, 1):
            report.append(f"{i}. {m}")
        report.append("")

        # --- Blockers ---
        report.append("## Potential Blockers")
        for b in self.blockers:
            report.append(f"- {b}")
        if not self.blockers:
            report.append("- No immediate blockers identified.")
        report.append("")

        # --- Implementation points ---
        report.append("## Implementation Points")
        for ip in self.implementation_points:
            report.append(f"- {ip}")
        report.append("")

        # --- Cost estimates ---
        report.append("## Cost Estimates")
        for item, est in self.cost_estimates.items():
            report.append(f"- **{item}**: {est}")
        if not self.cost_estimates:
            report.append("- TBD based on further infra analysis.")

        return "\n".join(report)
