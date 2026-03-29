#!/usr/bin/env bash
# ============================================================================
# Kiro Discovery Smoke Test
# ============================================================================
# Verifies that the .kiro/ directory is correctly structured so Kiro
# auto-discovers the migration advisor skill on project open.
#
# Run from the AIAdvisor/ directory:
#   bash skills/solr-opensearch-migration-advisor/tests/skill-smoke/test_kiro_discovery.sh
#
# Exit codes:
#   0 — all checks passed
#   1 — one or more checks failed
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Navigate up to AIAdvisor/ root (tests/skill-smoke -> tests -> skill -> skills -> AIAdvisor)
ADVISOR_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SKILL_DIR="$ADVISOR_ROOT/skills/solr-opensearch-migration-advisor"
KIRO_DIR="$ADVISOR_ROOT/.kiro"

PASS=0
FAIL=0

pass() {
    echo "  PASS: $1"
    PASS=$((PASS + 1))
}

fail() {
    echo "  FAIL: $1"
    FAIL=$((FAIL + 1))
}

check_exists() {
    local path="$1"
    local label="$2"
    if [[ -e "$path" ]]; then
        pass "$label exists"
    else
        fail "$label missing: $path"
    fi
}

echo "=== Kiro Discovery Smoke Test ==="
echo "AIAdvisor root: $ADVISOR_ROOT"
echo ""

# -------------------------------------------------------------------
# 1. .kiro/ directory structure
# -------------------------------------------------------------------
echo "--- .kiro/ directory structure ---"
check_exists "$KIRO_DIR" ".kiro directory"
check_exists "$KIRO_DIR/steering" ".kiro/steering directory"
check_exists "$KIRO_DIR/skills" ".kiro/skills directory"
check_exists "$KIRO_DIR/hooks" ".kiro/hooks directory"
check_exists "$KIRO_DIR/settings" ".kiro/settings directory"

# -------------------------------------------------------------------
# 2. Skill symlink resolves to a valid SKILL.md
# -------------------------------------------------------------------
echo ""
echo "--- Skill symlink ---"
SYMLINK="$KIRO_DIR/skills/solr-to-opensearch"
if [[ -L "$SYMLINK" ]]; then
    pass ".kiro/skills/solr-to-opensearch is a symlink"
    TARGET=$(readlink -f "$SYMLINK")
    if [[ -f "$TARGET/SKILL.md" ]]; then
        pass "symlink resolves to directory containing SKILL.md"
    else
        fail "symlink target ($TARGET) does not contain SKILL.md"
    fi
else
    fail ".kiro/skills/solr-to-opensearch is not a symlink"
fi

# -------------------------------------------------------------------
# 3. SKILL.md has valid frontmatter with required fields
# -------------------------------------------------------------------
echo ""
echo "--- SKILL.md frontmatter ---"
SKILL_MD="$SKILL_DIR/SKILL.md"
if [[ -f "$SKILL_MD" ]]; then
    # Check for YAML frontmatter delimiters
    if head -1 "$SKILL_MD" | grep -q '^---$'; then
        pass "SKILL.md has YAML frontmatter"
    else
        fail "SKILL.md missing YAML frontmatter (no leading ---)"
    fi

    # Check required frontmatter fields
    for field in name displayName description keywords; do
        if grep -q "^${field}:" "$SKILL_MD"; then
            pass "SKILL.md has '$field' field"
        else
            fail "SKILL.md missing '$field' field"
        fi
    done
else
    fail "SKILL.md not found at $SKILL_MD"
fi

# -------------------------------------------------------------------
# 4. Steering files exist and have inclusion frontmatter
# -------------------------------------------------------------------
echo ""
echo "--- Kiro steering files ---"
for f in product.md tech.md structure.md; do
    STEERING_FILE="$KIRO_DIR/steering/$f"
    if [[ -f "$STEERING_FILE" ]]; then
        pass ".kiro/steering/$f exists"
        if grep -q "^inclusion:" "$STEERING_FILE"; then
            pass ".kiro/steering/$f has 'inclusion:' frontmatter"
        else
            fail ".kiro/steering/$f missing 'inclusion:' frontmatter"
        fi
    else
        fail ".kiro/steering/$f not found"
    fi
done

# -------------------------------------------------------------------
# 5. MCP config is valid JSON and references the skill
# -------------------------------------------------------------------
echo ""
echo "--- MCP configuration ---"
MCP_JSON="$KIRO_DIR/settings/mcp.json"
if [[ -f "$MCP_JSON" ]]; then
    pass "mcp.json exists"
    if python3 -c "import json; json.load(open('$MCP_JSON'))" 2>/dev/null; then
        pass "mcp.json is valid JSON"
    else
        fail "mcp.json is not valid JSON"
    fi
    if grep -q "solr-to-opensearch" "$MCP_JSON"; then
        pass "mcp.json references solr-to-opensearch server"
    else
        fail "mcp.json does not reference solr-to-opensearch server"
    fi
else
    fail "mcp.json not found"
fi

# -------------------------------------------------------------------
# 6. Hook file is valid JSON
# -------------------------------------------------------------------
echo ""
echo "--- Kiro hooks ---"
HOOK_FILE="$KIRO_DIR/hooks/schema-assist.kiro.hook"
if [[ -f "$HOOK_FILE" ]]; then
    pass "schema-assist.kiro.hook exists"
    if python3 -c "import json; json.load(open('$HOOK_FILE'))" 2>/dev/null; then
        pass "schema-assist.kiro.hook is valid JSON"
    else
        fail "schema-assist.kiro.hook is not valid JSON"
    fi
    # Check required hook fields
    if grep -q '"when"' "$HOOK_FILE" && grep -q '"then"' "$HOOK_FILE"; then
        pass "hook has 'when' and 'then' fields"
    else
        fail "hook missing 'when' or 'then' fields"
    fi
else
    fail "schema-assist.kiro.hook not found"
fi

# -------------------------------------------------------------------
# 7. Skill steering directory exists and is not empty
# -------------------------------------------------------------------
echo ""
echo "--- Skill steering directory ---"
check_exists "$SKILL_DIR/steering" "steering/ directory"
STEERING_COUNT=$(find "$SKILL_DIR/steering" -name "*.md" | wc -l)
if [[ "$STEERING_COUNT" -gt 0 ]]; then
    pass "steering/ has $STEERING_COUNT .md files"
else
    fail "steering/ has no .md files"
fi

# -------------------------------------------------------------------
# 8. Core scripts exist
# -------------------------------------------------------------------
echo ""
echo "--- Core skill scripts ---"
for f in skill.py schema_converter.py query_converter.py report.py storage.py; do
    check_exists "$SKILL_DIR/scripts/$f" "scripts/$f"
done

# -------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [[ $FAIL -gt 0 ]]; then
    echo "SMOKE TEST FAILED"
    exit 1
else
    echo "SMOKE TEST PASSED"
    exit 0
fi
