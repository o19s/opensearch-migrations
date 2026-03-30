#!/usr/bin/env bash
# ============================================================================
# Unified Migration Advisor — Report Quality Eval
# ============================================================================
# Runs the migration advisor eval through promptfoo with two providers:
#   (a) Deterministic: MCP stdio bridge (free, no API key)
#   (b) LLM + Skill: Claude Code CLI with MCP tools (requires API key)
#
# Usage:
#   bash run_eval.sh              # both providers
#   bash run_eval.sh --mcp-only   # deterministic only (free)
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Check promptfoo ---
if ! command -v promptfoo &> /dev/null; then
    echo "ERROR: promptfoo not found. Install with: npm install -g promptfoo"
    exit 1
fi

if [[ "${1:-}" == "--mcp-only" ]]; then
    echo "=== Running deterministic MCP eval only ==="
    promptfoo eval \
        --config promptfooconfig.yaml \
        --providers "exec:python3 mcp_provider.py" \
        --no-cache 2>&1
else
    echo "=== Running unified eval (MCP + Claude Code CLI) ==="
    promptfoo eval \
        --config promptfooconfig.yaml \
        --no-cache 2>&1
fi

echo ""
echo "Run 'promptfoo view' to see detailed results."
