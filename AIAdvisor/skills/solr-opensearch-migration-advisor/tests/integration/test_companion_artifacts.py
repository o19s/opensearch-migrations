from pathlib import Path
import csv


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPANION_DEMO_DIR = REPO_ROOT / "examples" / "migration-companion-demo"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_companion_demo_contains_expected_artifact_chain():
    expected_files = {
        "README.md",
        "assessment-summary.md",
        "success-definition.md",
        "consumer-inventory.csv",
        "risk-register.md",
        "migration-playbook.md",
        "go-no-go-review.md",
        "approval-record.md",
        "cutover-checklist.md",
    }

    actual_files = {path.name for path in COMPANION_DEMO_DIR.iterdir() if path.is_file()}
    assert expected_files.issubset(actual_files)


def test_companion_demo_readme_lists_core_artifacts():
    content = read_text(COMPANION_DEMO_DIR / "README.md")

    for artifact in [
        "assessment-summary.md",
        "success-definition.md",
        "consumer-inventory.csv",
        "risk-register.md",
        "migration-playbook.md",
        "go-no-go-review.md",
        "approval-record.md",
        "cutover-checklist.md",
    ]:
        assert f"`{artifact}`" in content


def test_success_definition_contains_approval_grade_sections():
    content = read_text(COMPANION_DEMO_DIR / "success-definition.md")

    required_sections = [
        "## 1. Migration Scope",
        "## 2. Business Outcomes",
        "## 3. Technical Guardrails",
        "## 4. Validation Evidence Required",
        "## 5. Approval Thresholds",
        "## 9. Approvers",
        "## 10. Approval Record",
    ]

    for section in required_sections:
        assert section in content


def test_go_no_go_review_contains_decision_scope_and_recommendation():
    content = read_text(COMPANION_DEMO_DIR / "go-no-go-review.md")

    assert "## 1. Decision Under Review" in content
    assert "## 2. Recommendation" in content
    assert "## 8. Approvers" in content
    assert "`Go with conditions`" in content or "`Go`" in content or "`No-Go`" in content


def test_consumer_inventory_has_required_columns():
    with (COMPANION_DEMO_DIR / "consumer-inventory.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []

    required_columns = {
        "consumer_id",
        "consumer_name",
        "owner",
        "consumer_type",
        "reads_search",
        "writes_index",
        "criticality",
        "cutover_day_required",
        "fallback_available",
        "solr_touchpoints",
        "response_shape_dependency",
        "migration_status",
        "notes",
    }

    assert required_columns.issubset(set(fieldnames))
