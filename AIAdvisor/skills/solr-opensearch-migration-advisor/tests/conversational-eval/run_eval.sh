#!/usr/bin/env bash
# Run the conversational step eval.
#
# This eval walks through the advisor's multi-turn workflow (Steps 0-7)
# using sequential Claude CLI sessions with --resume / --session-id.
#
# Prerequisites:
#   - claude CLI installed and authenticated
#   - promptfoo installed (npx promptfoo works)
#   - Skill venv with MCP server dependencies
#
# Usage:
#   bash run_eval.sh            # run all steps
#   bash run_eval.sh --dry-run  # show what would run without executing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean up stale session file from previous runs
rm -f /tmp/sma-conv-eval-session-id.txt

DRY_RUN=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="--dry-run" ;;
    *) echo "Unknown arg: $arg"; exit 1 ;;
  esac
done

echo "=== Migration Advisor — Conversational Step Eval ==="
echo ""
echo "This eval runs sequential multi-turn tests through the advisor's"
echo "8-step workflow. Tests must run in order (no parallelism)."
echo ""

# Force sequential execution — multi-turn tests depend on prior context
npx --yes promptfoo@latest eval \
  --config eval.yaml \
  --no-cache \
  --max-concurrency 1 \
  $DRY_RUN \
  "$@"

echo ""
echo "Done. Run 'npx promptfoo view' to inspect results."
