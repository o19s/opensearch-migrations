#!/usr/bin/env bash
# ============================================================================
# Multi-Run Stability Check
# ============================================================================
# Runs LLM tiers multiple times to check consistency. Reports pass rates
# per assertion across runs.
#
# Usage:
#   bash run_stability.sh              # 3 runs of T2 + T3 (default)
#   bash run_stability.sh 5            # 5 runs
#   bash run_stability.sh 3 T2         # 3 runs of T2 only
#   bash run_stability.sh 3 T3         # 3 runs of T3 only
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RUNS="${1:-3}"
TIER_FILTER="${2:-}"
RESULTS_DIR="$SCRIPT_DIR/eval-reports/stability"
mkdir -p "$RESULTS_DIR"

# --- Check prerequisites ---
if ! command -v promptfoo &> /dev/null; then
    echo "ERROR: promptfoo not found. Install with: npm install -g promptfoo"
    exit 1
fi
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq not found."
    exit 1
fi

# --- Assemble system prompt if missing ---
SYSTEM_PROMPT="$SCRIPT_DIR/system-prompt-assembled.txt"
if [[ ! -f "$SYSTEM_PROMPT" ]]; then
    SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
    echo "Assembling system-prompt-assembled.txt ..."
    {
        echo "# MIGRATION ADVISOR SKILL CONTEXT"
        echo ""
        echo "## SKILL.md (Agent Skill Definition)"
        echo ""
        cat "$SKILL_DIR/SKILL.md"
        for f in "$SKILL_DIR/steering/"*.md; do
            echo ""
            echo "## $(basename "$f" .md)"
            echo ""
            cat "$f"
        done
    } > "$SYSTEM_PROMPT"
fi

# Determine which tiers to run
if [[ -n "$TIER_FILTER" ]]; then
    TIERS=("$TIER_FILTER")
else
    TIERS=("T2" "T3")
fi

export REPORT_ARTIFACT_DIR="$RESULTS_DIR"

echo "=== Stability Check: ${RUNS} runs × ${TIERS[*]} ==="
echo ""

# --- Run evals ---
for tier in "${TIERS[@]}"; do
    for i in $(seq 1 "$RUNS"); do
        echo -n "  $tier run $i/$RUNS ... "
        OUT="$RESULTS_DIR/${tier}-run${i}.json"
        promptfoo eval \
            --config promptfooconfig.yaml \
            --filter-providers "$tier" \
            --no-cache \
            -o "$OUT" 2>/dev/null || true
        PASS_COUNT=$(jq '[.results.results[0].gradingResult.componentResults[] | select(.pass == true)] | length' "$OUT")
        TOTAL=$(jq '[.results.results[0].gradingResult.componentResults[]] | length' "$OUT")
        echo "${PASS_COUNT}/${TOTAL}"
    done
done

echo ""
echo "=== Per-Assertion Pass Rates ==="
echo ""

# --- Summarize ---
for tier in "${TIERS[@]}"; do
    echo "--- $tier ($RUNS runs) ---"

    # Get assertion names from first run
    FIRST="$RESULTS_DIR/${tier}-run1.json"
    METRICS=$(jq -r '.results.results[0].gradingResult.componentResults[].assertion.metric' "$FIRST")

    printf "%-35s %s\n" "Assertion" "Pass Rate"
    printf "%-35s %s\n" "---" "---"

    TOTAL_PASS=0
    TOTAL_ASSERTIONS=0

    while IFS= read -r metric; do
        PASSES=0
        for i in $(seq 1 "$RUNS"); do
            OUT="$RESULTS_DIR/${tier}-run${i}.json"
            PASSED=$(jq -r --arg m "$metric" '.results.results[0].gradingResult.componentResults[] | select(.assertion.metric == $m) | .pass' "$OUT")
            if [[ "$PASSED" == "true" ]]; then
                PASSES=$((PASSES + 1))
            fi
        done
        TOTAL_PASS=$((TOTAL_PASS + PASSES))
        TOTAL_ASSERTIONS=$((TOTAL_ASSERTIONS + RUNS))
        printf "%-35s %d/%d\n" "$metric" "$PASSES" "$RUNS"
    done <<< "$METRICS"

    echo ""
    echo "Overall: ${TOTAL_PASS}/${TOTAL_ASSERTIONS} ($((TOTAL_PASS * 100 / TOTAL_ASSERTIONS))%)"
    echo ""
done

echo "Raw results: $RESULTS_DIR/"
