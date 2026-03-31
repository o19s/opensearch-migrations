#!/usr/bin/env bash
# ============================================================================
# End-to-End Migration Advisor Demo
# ============================================================================
# Runs the full demo flow:
#   1. Start Solr (Docker)
#   2. Load 200K e-commerce products
#   3. Generate 15 minutes of search traffic
#   4. Inspect live Solr and generate migration report
#   5. Run promptfoo eval against the live instance
#   6. Print summary with artifact locations
#
# Usage:
#   bash run_demo.sh                # full demo (~20 min)
#   bash run_demo.sh --quick        # quick demo (~3 min, 10K docs, 2 min traffic)
#   bash run_demo.sh --report-only  # skip data/traffic, just inspect + report
#
# Prerequisites:
#   - Docker (for Solr)
#   - Python 3.x with the skill's venv
#   - promptfoo (npm install -g promptfoo)
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEMO_DIR="$SCRIPT_DIR/solr-demo"
IMPACT_DIR="$SKILL_DIR/tests/skill-impact"
REPORT_FILE="$DEMO_DIR/migration-report.md"
SOLR_URL="${SOLR_URL:-http://localhost:38983}"

MODE="${1:---full}"

echo "============================================================"
echo "  Migration Advisor — End-to-End Demo"
echo "  Mode: ${MODE}"
echo "============================================================"
echo ""

# ---- Step 1: Start Solr ----
echo "Step 1: Starting Solr..."
cd "$SCRIPT_DIR"

if curl -sf "${SOLR_URL}/solr/admin/info/system?wt=json" > /dev/null 2>&1; then
    echo "  Solr already running at ${SOLR_URL}"
else
    docker compose up -d 2>&1 | grep -v "^$"
    echo "  Waiting for Solr..."
    for i in {1..30}; do
        curl -sf "${SOLR_URL}/solr/admin/info/system?wt=json" > /dev/null 2>&1 && break
        [ "$i" -eq 30 ] && echo "ERROR: Solr failed to start" && exit 1
        sleep 2
    done
    echo "  Solr is ready."
fi
echo ""

# ---- Step 2+3: Load data and generate traffic ----
if [ "$MODE" != "--report-only" ]; then
    echo "Step 2-3: Loading data and generating traffic..."
    case "$MODE" in
        --quick)
            bash "$DEMO_DIR/setup_demo.sh" --quick
            ;;
        *)
            bash "$DEMO_DIR/setup_demo.sh" --full
            ;;
    esac
    echo ""
fi

# ---- Step 4: Inspect Solr and generate report ----
echo "Step 4: Inspecting Solr and generating migration report..."
cd "$SKILL_DIR"

# Activate venv if available
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

python3 "$DEMO_DIR/inspect_and_report.py" "$SOLR_URL" "ecommerce" "$REPORT_FILE"
echo ""

# ---- Step 5: Run promptfoo eval ----
echo "Step 5: Running promptfoo eval..."
EVAL_REPORTS_DIR="$IMPACT_DIR/eval-reports"
if command -v promptfoo &> /dev/null; then
    cd "$IMPACT_DIR"
    export REPORT_ARTIFACT_DIR="$EVAL_REPORTS_DIR"
    mkdir -p "$EVAL_REPORTS_DIR"
    promptfoo eval \
        --config promptfooconfig.yaml \
        --providers "exec:python3 mcp_provider.py" \
        --no-cache 2>&1 | grep -E "Results:|passed|failed|Duration"
    EVAL_RAN=true
else
    echo "  promptfoo not installed — skipping eval (npm install -g promptfoo)"
    EVAL_RAN=false
fi
echo ""

# ---- Summary ----
echo "============================================================"
echo "  Demo Complete!"
echo ""
echo "  Artifacts:"
echo "    Live Solr Report:   ${REPORT_FILE}"
if [ -f "$EVAL_REPORTS_DIR/migration-report-py.md" ]; then
echo "    Eval Report (MCP):  ${EVAL_REPORTS_DIR}/migration-report-py.md"
fi
if [ -f "$EVAL_REPORTS_DIR/migration-report-skill.md" ]; then
echo "    Eval Report (LLM):  ${EVAL_REPORTS_DIR}/migration-report-skill.md"
fi
if [ "$EVAL_RAN" = true ]; then
echo "    Promptfoo Eval:     run 'promptfoo view' for interactive results"
fi
echo ""
echo "  Quick look at the reports:"
echo "    cat ${REPORT_FILE}"
if [ -f "$EVAL_REPORTS_DIR/migration-report-py.md" ]; then
echo "    cat ${EVAL_REPORTS_DIR}/migration-report-py.md"
fi
echo ""
echo "  Cleanup:"
echo "    cd ${SCRIPT_DIR} && docker compose down"
echo "============================================================"
