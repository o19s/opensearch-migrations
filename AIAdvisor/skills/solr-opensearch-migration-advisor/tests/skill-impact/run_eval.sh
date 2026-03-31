#!/usr/bin/env bash
# ============================================================================
# Migration Advisor — 4-Tier Report Quality Eval
# ============================================================================
# Runs the migration advisor eval through promptfoo with four tiers:
#
#   T1  Deterministic (MCP stdio)        — Python only, no LLM (free)
#   T2  LLM + Skill + OS Mapping         — skill context + pre-converted mapping
#   T3  LLM + Skill, No OS Mapping       — skill context + raw schema only
#   T4  LLM + MCP Tools                  — full integration (Claude CLI + MCP)
#
# Report artifacts are saved to eval-reports/.
#
# Usage:
#   bash run_eval.sh              # all 4 tiers
#   bash run_eval.sh --tier 1     # deterministic only (free, instant)
#   bash run_eval.sh --tier 2     # LLM + skill + mapping
#   bash run_eval.sh --tier 3     # LLM + skill, no mapping
#   bash run_eval.sh --tier 4     # LLM + MCP tools
#   bash run_eval.sh --mcp-only   # alias for --tier 1
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Check promptfoo ---
if ! command -v promptfoo &> /dev/null; then
    echo "ERROR: promptfoo not found. Install with: npm install -g promptfoo"
    exit 1
fi

# --- Assemble system prompt if missing (needed by T2 and T3) ---
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
    echo "  -> $(wc -l < "$SYSTEM_PROMPT") lines assembled"
fi

# Report artifacts directory
export REPORT_ARTIFACT_DIR="$SCRIPT_DIR/eval-reports"
mkdir -p "$REPORT_ARTIFACT_DIR"

# --- Parse tier argument ---
FILTER_PROVIDERS=""
TIER_LABEL="all 4 tiers"

case "${1:-}" in
    --mcp-only|--tier-1|"--tier 1")
        FILTER_PROVIDERS="T1"
        TIER_LABEL="T1 Deterministic only"
        ;;
    --tier-2|"--tier 2")
        FILTER_PROVIDERS="T2"
        TIER_LABEL="T2 LLM + Skill + OS Mapping"
        ;;
    --tier-3|"--tier 3")
        FILTER_PROVIDERS="T3"
        TIER_LABEL="T3 LLM + Skill, No OS Mapping"
        ;;
    --tier-4|"--tier 4")
        FILTER_PROVIDERS="T4"
        TIER_LABEL="T4 LLM + MCP Tools"
        ;;
    --tier)
        # Handle --tier N as two arguments
        FILTER_PROVIDERS="T${2:-}"
        TIER_LABEL="T${2:-}"
        ;;
    "")
        # Run all tiers
        ;;
    *)
        echo "Usage: bash run_eval.sh [--tier N | --mcp-only]"
        exit 1
        ;;
esac

echo "=== Running eval: $TIER_LABEL ==="

if [[ -n "$FILTER_PROVIDERS" ]]; then
    promptfoo eval \
        --config promptfooconfig.yaml \
        --filter-providers "$FILTER_PROVIDERS" \
        --no-cache 2>&1
else
    promptfoo eval \
        --config promptfooconfig.yaml \
        --no-cache 2>&1
fi

echo ""

# --- Show report artifacts ---
if [ -d "$REPORT_ARTIFACT_DIR" ] && [ "$(ls -A "$REPORT_ARTIFACT_DIR" 2>/dev/null)" ]; then
    echo "Report artifacts:"
    for f in "$REPORT_ARTIFACT_DIR"/*.md; do
        [ -f "$f" ] && echo "  $(basename "$f")  ($(wc -l < "$f") lines)"
    done
    echo "  Location: $REPORT_ARTIFACT_DIR/"
    echo ""
fi

echo "Run 'promptfoo view' to see detailed eval results."
