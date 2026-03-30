#!/usr/bin/env bash
# ============================================================================
# Tier 3: Claude Code CLI as Implicit Test Harness
# ============================================================================
# Tests the skill through Claude Code's real IDE integration path.
# Claude Code auto-discovers CLAUDE.md and loads skill context.
#
# Runs the same question twice:
#   1. --bare mode (no CLAUDE.md, no skill context) -> baseline
#   2. default mode from AIAdvisor/ (loads CLAUDE.md + skill context) -> enhanced
#
# Usage:
#   bash run_tier3_claude.sh
#
# Prerequisites:
#   - claude CLI installed and authenticated
#   - Anthropic API key or configured auth
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ADVISOR_DIR="$(cd "$SKILL_DIR/../.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/tier3-results"

mkdir -p "$RESULTS_DIR"

# --- Check Claude CLI ---
if ! command -v claude &> /dev/null; then
    echo "ERROR: claude CLI not found. Install from https://claude.com/claude-code"
    exit 1
fi

QUESTION='I have a Solr schema with a field named "location" using LatLonPointSpatialField, a copyField directive from title to title_sort, and a field named "price" using TrieIntField. What OpenSearch mapping should I create? List the field types and flag any incompatibilities.'

echo "=== Tier 3: Claude Code CLI (real IDE integration) ==="
echo ""

# --- Run 1: Bare mode (no skill context) ---
echo "--- Run 1: Claude Code --bare (no skill context) ---"
echo ""

claude -p \
    --bare \
    --output-format text \
    --max-turns 1 \
    "$QUESTION" \
    > "$RESULTS_DIR/response-bare.txt" 2>&1

echo "Bare response saved to tier3-results/response-bare.txt"
echo "Preview:"
head -20 "$RESULTS_DIR/response-bare.txt"
echo "..."
echo ""

# --- Run 2: Default mode from AIAdvisor/ (loads CLAUDE.md + skill) ---
echo "--- Run 2: Claude Code default (loads CLAUDE.md + skill context) ---"
echo ""

# Run from AIAdvisor/ so Claude Code discovers CLAUDE.md and .kiro/
cd "$ADVISOR_DIR"
claude -p \
    --output-format text \
    --max-turns 1 \
    "$QUESTION" \
    > "$RESULTS_DIR/response-with-skill.txt" 2>&1

cd "$SCRIPT_DIR"

echo "With-skill response saved to tier3-results/response-with-skill.txt"
echo "Preview:"
head -20 "$RESULTS_DIR/response-with-skill.txt"
echo "..."
echo ""

# --- Check assertions ---
echo "============================================================"
echo "  TIER 3 RESULTS — Claude Code CLI"
echo "============================================================"
echo ""

BARE_PASS=0
BARE_FAIL=0
SKILL_PASS=0
SKILL_FAIL=0

check_assertion() {
    local file="$1"
    local term="$2"
    local label="$3"
    local mode="$4"

    if grep -qi "$term" "$file"; then
        echo "  PASS [$mode]: contains '$term' ($label)"
        if [ "$mode" = "bare" ]; then ((BARE_PASS++)); else ((SKILL_PASS++)); fi
    else
        echo "  FAIL [$mode]: missing '$term' ($label)"
        if [ "$mode" = "bare" ]; then ((BARE_FAIL++)); else ((SKILL_FAIL++)); fi
    fi
}

echo "Assertions on BARE response:"
check_assertion "$RESULTS_DIR/response-bare.txt" "geo_point" "spatial mapping" "bare"
check_assertion "$RESULTS_DIR/response-bare.txt" "copy_to" "copyField mapping" "bare"
check_assertion "$RESULTS_DIR/response-bare.txt" "integer" "TrieInt mapping" "bare"
check_assertion "$RESULTS_DIR/response-bare.txt" "incompatib" "flags issues" "bare"
echo ""

echo "Assertions on WITH-SKILL response:"
check_assertion "$RESULTS_DIR/response-with-skill.txt" "geo_point" "spatial mapping" "skill"
check_assertion "$RESULTS_DIR/response-with-skill.txt" "copy_to" "copyField mapping" "skill"
check_assertion "$RESULTS_DIR/response-with-skill.txt" "integer" "TrieInt mapping" "skill"
check_assertion "$RESULTS_DIR/response-with-skill.txt" "incompatib" "flags issues" "skill"
echo ""

echo "Summary:"
echo "  Bare:       $BARE_PASS passed, $BARE_FAIL failed"
echo "  With-skill: $SKILL_PASS passed, $SKILL_FAIL failed"
echo ""
echo "If the skill adds value, 'bare' should fail more assertions"
echo "than 'with-skill'."
echo ""
echo "Full responses saved in tier3-results/ for inspection."
echo "============================================================"
