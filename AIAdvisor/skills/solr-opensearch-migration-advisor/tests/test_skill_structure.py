import os
import re
import yaml
import pytest

SKILLS_PATH = "."

def test_skill_md_exists():
    skill_md_path = os.path.join(SKILLS_PATH, "SKILL.md")
    assert os.path.exists(skill_md_path)

def test_skill_md_frontmatter():
    skill_md_path = os.path.join(SKILLS_PATH, "SKILL.md")
    with open(skill_md_path, 'r') as f:
        content = f.read()
    
    # Check for frontmatter
    assert content.startswith("---")
    parts = content.split("---")
    assert len(parts) >= 3
    
    metadata_wrapper = yaml.safe_load(parts[1])
    assert "name" in metadata_wrapper
    assert metadata_wrapper["name"] == "solr-to-opensearch-migration"
    
    # version is inside metadata sub-object
    assert "metadata" in metadata_wrapper
    assert "version" in metadata_wrapper["metadata"]

def get_reference_files():
    ref_dir = os.path.join(SKILLS_PATH, "references")
    if not os.path.isdir(ref_dir):
        return []
    return [f for f in os.listdir(ref_dir) if f.endswith(".md")]

@pytest.mark.parametrize("ref_file", get_reference_files())
def test_reference_follow_template(ref_file):
    # Some files are known drafts that don't follow the template yet
    drafts = [
        "migration-strategy.md",
        "consulting-methodology.md",
        "aws-opensearch-service.md",
        "solr-concepts-reference.md",
        "scenario-drupal.md",
        "08-edge-cases-and-gotchas.md",
        "sample-catalog.md",
        "consulting-concerns-inventory.md",
        "roles-and-escalation-patterns.md"
    ]
    
    ref_path = os.path.join(SKILLS_PATH, "references", ref_file)
    with open(ref_path, 'r') as f:
        content = f.read()
    
    if ref_file in drafts:
        # For drafts, we just check they have a title
        assert content.startswith("# ")
        return

    # Check for mandatory sections in non-drafts
    assert "## Key Judgements" in content
    assert "## Decision Heuristics" in content
    assert ("## Common Mistakes" in content or "## Common Failure Modes" in content)
    
    # Check for Scope and Audience at the top
    assert "**Scope:**" in content
    assert "**Audience:**" in content
