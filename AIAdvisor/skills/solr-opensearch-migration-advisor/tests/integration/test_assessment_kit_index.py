from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
ASSESSMENT_KIT_DIR = REPO_ROOT / "playbook" / "assessment-kit"
ASSESSMENT_KIT_INDEX = ASSESSMENT_KIT_DIR / "assessment-kit-index.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_markdown_links(content: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", content)


def test_assessment_kit_index_links_resolve_to_real_files():
    content = read_text(ASSESSMENT_KIT_INDEX)
    links = extract_markdown_links(content)

    for link in links:
        target = (ASSESSMENT_KIT_INDEX.parent / link).resolve()
        assert target.exists(), f"Broken link in assessment kit index: {link}"


def test_assessment_kit_index_mentions_companion_artifact_templates():
    content = read_text(ASSESSMENT_KIT_INDEX)

    for artifact in [
        "success-definition-template.md",
        "consumer-inventory-template.md",
        "go-no-go-review-template.md",
    ]:
        assert artifact in content


def test_assessment_kit_templates_exist_with_expected_sections():
    templates = {
        "success-definition-template.md": [
            "## 1. Migration Scope",
            "## 4. Validation Evidence Required",
            "## 9. Approvers",
        ],
        "consumer-inventory-template.md": [
            "## Suggested Fields",
            "## Markdown Table Starter",
            "## CSV Header Starter",
        ],
        "go-no-go-review-template.md": [
            "## 1. Decision Under Review",
            "## 2. Recommendation",
            "## 8. Approvers",
        ],
    }

    for filename, required_sections in templates.items():
        content = read_text(ASSESSMENT_KIT_DIR / filename)
        for section in required_sections:
            assert section in content, f"{filename} is missing required section: {section}"
