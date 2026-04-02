from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_top_level_docs_reference_current_companion_artifacts():
    readme = read_text("README.md")
    structure = read_text("project/core/structure.md")
    content_structure = read_text("working/CONTENT-STRUCTURE.md")

    for marker in [
        "migration-companion-demo",
        "09-approval-and-safety-tiers.md",
        "10-playbook-artifact-and-review.md",
    ]:
        assert marker in readme
        assert marker in structure
        assert marker in content_structure


def test_top_level_docs_use_current_reference_filenames():
    structure = read_text("project/core/structure.md")
    content_structure = read_text("working/CONTENT-STRUCTURE.md")

    for current_name in [
        "02-pre-migration.md",
        "05-validation-cutover.md",
    ]:
        assert current_name in structure
        assert current_name in content_structure

    for old_name in [
        "02-source-audit.md",
        "05-relevance-validation.md",
    ]:
        assert old_name not in structure
        assert old_name not in content_structure


def test_structure_doc_reflects_current_assessment_kit_artifacts():
    structure = read_text("project/core/structure.md")

    for marker in [
        "Reusable assessment artifacts (11 files)",
        "consumer-inventory-template.md",
        "go-no-go-review-template.md",
        "success-definition-template.md",
    ]:
        assert marker in structure
