#!/usr/bin/env bash
# ============================================================================
# Skill Impact Demo
# ============================================================================
# Proves the migration advisor's steering content measurably changes
# LLM output by running the same questions with and without skill context.
#
# Usage:
#   bash run_impact_demo.sh              # Bedrock (required by default)
#   bash run_impact_demo.sh --ollama     # Ollama (optional alternative)
#
# Prerequisites:
#   - promptfoo installed (npm install -g promptfoo)
#   - For Bedrock: AWS credentials configured, AWS_DEFAULT_REGION set
#   - For Ollama: ollama running locally with a model pulled
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ASSEMBLED="$SCRIPT_DIR/system-prompt-assembled.txt"

# --- Parse arguments ---
USE_OLLAMA=false
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.1:8b}"

for arg in "$@"; do
    case "$arg" in
        --ollama) USE_OLLAMA=true ;;
        *) echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

# --- Configure provider ---
PROVIDER_OVERRIDE=""
if [ "$USE_OLLAMA" = true ]; then
    echo "=== Provider: Ollama ($OLLAMA_MODEL) ==="
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "ERROR: Ollama not running at localhost:11434"
        exit 1
    fi
    PROVIDER_OVERRIDE="--providers ollama:chat:${OLLAMA_MODEL}"
else
    echo "=== Provider: Amazon Bedrock ==="
    if [ -z "${AWS_DEFAULT_REGION:-}" ] && [ -z "${AWS_REGION:-}" ]; then
        echo "ERROR: AWS_DEFAULT_REGION or AWS_REGION must be set for Bedrock"
        echo "  export AWS_DEFAULT_REGION=us-east-1"
        exit 1
    fi
fi

# --- Step 1: Assemble system prompt from skill content ---
echo ""
echo "--- Assembling system prompt from skill content ---"

{
    echo "# MIGRATION ADVISOR SKILL CONTEXT"
    echo "# This context is injected to test whether it changes LLM behavior."
    echo ""
    echo "## SKILL.md (Agent Skill Definition)"
    echo ""
    cat "$SKILL_DIR/SKILL.md"
    echo ""

    for f in "$SKILL_DIR"/steering/*.md; do
        if [ -s "$f" ]; then
            echo ""
            echo "## Steering: $(basename "$f")"
            echo ""
            cat "$f"
        fi
    done

    if [ -d "$SKILL_DIR/references" ]; then
        for f in "$SKILL_DIR"/references/*.md; do
            if [ -s "$f" ]; then
                echo ""
                echo "## Reference: $(basename "$f")"
                echo ""
                cat "$f"
            fi
        done
    fi
} > "$ASSEMBLED"

LINES=$(wc -l < "$ASSEMBLED")
echo "Assembled $LINES lines into system-prompt-assembled.txt"

# --- Step 2: Run the eval ---
echo ""
echo "--- Running promptfoo eval (bare vs with-skill) ---"
echo ""

cd "$SCRIPT_DIR"
promptfoo eval --config promptfooconfig-stuffing.yaml --no-cache $PROVIDER_OVERRIDE 2>&1

# --- Step 3: Print summary ---
echo ""
echo "============================================================"
echo "  SKILL IMPACT RESULTS"
echo "============================================================"
echo ""
echo "The eval above ran each question twice:"
echo "  1. WITHOUT skill context (bare LLM)"
echo "  2. WITH skill context (SKILL.md + steering injected)"
echo ""
echo "If the skill adds value, the 'bare' variant should FAIL"
echo "some assertions and the 'with-skill' variant should PASS."
echo ""
echo "Run 'promptfoo view' to see detailed results in the browser."
echo "============================================================"
