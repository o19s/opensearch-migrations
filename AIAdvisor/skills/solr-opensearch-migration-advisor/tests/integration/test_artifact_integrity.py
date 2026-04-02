import os
import json
import re
import pytest

SPECS_PATH = "examples"

def get_files_by_ext(ext):
    matches = []
    for root, dirnames, filenames in os.walk(SPECS_PATH):
        for filename in filenames:
            if filename.endswith(ext):
                matches.append(os.path.join(root, filename))
    return matches

@pytest.mark.parametrize("json_file", get_files_by_ext(".json"))
def test_json_artifact_syntax(json_file):
    """Verify that all JSON artifacts in examples are valid JSON."""
    with open(json_file, 'r') as f:
        try:
            json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {json_file}: {e}")

@pytest.mark.parametrize("ndjson_file", get_files_by_ext(".ndjson"))
def test_ndjson_artifact_syntax(ndjson_file):
    """Verify that all NDJSON artifacts in examples are valid line-delimited JSON."""
    with open(ndjson_file, 'r') as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid NDJSON on line {i+1} in {ndjson_file}: {e}")

@pytest.mark.parametrize("md_file", get_files_by_ext(".md"))
def test_markdown_link_integrity(md_file):
    """Verify that all internal file links in examples markdown files are valid."""
    with open(md_file, 'r') as f:
        content = f.read()

    # Find all markdown links: [label](path)
    # We only care about relative file links (not http, not anchors)
    links = re.findall(r'\[.*?\]\((?!http|#)(.*?)\)', content)
    
    base_dir = os.path.dirname(md_file)
    errors = []
    
    for link in links:
        # Clean up any anchor parts from the link (e.g., path.md#section)
        clean_link = link.split('#')[0]
        if not clean_link:
            continue
            
        target_path = os.path.join(base_dir, clean_link)
        if not os.path.exists(target_path):
            errors.append(f"Broken link in {md_file}: {link} (Target not found: {target_path})")
            
    assert not errors, "\n".join(errors)
