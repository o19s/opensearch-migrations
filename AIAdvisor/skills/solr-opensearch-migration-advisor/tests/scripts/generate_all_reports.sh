#!/bin/bash
#
# Run all SMA eval files and generate reports for each.
#
# Usage:
#   cd AIAdvisor/skills/solr-opensearch-migration-advisor
#   ./tests/scripts/generate_all_reports.sh
#
# Runs each eval file sequentially, generating markdown + HTML + JSON
# reports in tests/artifacts/<timestamp>/. Each eval file gets its
# own set of report files.
#
# To run a single eval file instead:
#   ./tests/scripts/generate_report.sh tests/evals/eval-fully-loaded.yaml

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
EVALS_DIR="$SKILL_DIR/tests/evals"

EVAL_FILES=(
    "$EVALS_DIR/eval.yaml"
    "$EVALS_DIR/eval-fully-loaded.yaml"
    "$EVALS_DIR/eval-blue-sky.yaml"
    "$EVALS_DIR/eval-yolo.yaml"
)

OVERALL_EXIT=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " SMA Eval Suite — Running all eval files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for eval_file in "${EVAL_FILES[@]}"; do
    if [[ ! -f "$eval_file" ]]; then
        echo "⊘ Skipping $(basename "$eval_file") (file not found)"
        echo ""
        continue
    fi

    echo "▶ Running $(basename "$eval_file")..."
    echo ""

    "$SCRIPT_DIR/generate_report.sh" "$eval_file" || {
        echo ""
        echo "✗ $(basename "$eval_file") had failures"
        OVERALL_EXIT=1
    }

    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $OVERALL_EXIT -eq 0 ]]; then
    echo " All eval files completed successfully"
else
    echo " Some eval files had failures (see reports above)"
fi
echo ""
echo " Reports are in: tests/artifacts/"
echo " Interactive:    cd tests/evals && promptfoo view"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $OVERALL_EXIT
