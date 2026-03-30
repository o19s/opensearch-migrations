#!/usr/bin/env bash
# ============================================================================
# Tier 2: Skill Code Provider
# ============================================================================
# Tests the real skill code (skill.handle_message) via promptfoo's exec
# provider. No LLM involved — deterministic Python converters only.
#
# This is the same code path that Kiro/Claude Code would use via MCP.
#
# Usage:
#   bash run_tier2_skill.sh
#
# Prerequisites:
#   - promptfoo installed (npm install -g promptfoo)
#   - Python 3.11+ with skill dependencies installed
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Tier 2: Skill Code Provider (deterministic, no LLM) ==="
echo ""

cd "$SCRIPT_DIR"
promptfoo eval --config promptfooconfig-skill.yaml --no-cache 2>&1

echo ""
echo "============================================================"
echo "  TIER 2 RESULTS — Skill Code Provider"
echo "============================================================"
echo ""
echo "This test used the real skill code (handle_message + converters)"
echo "with NO LLM involved. The skill deterministically converted"
echo "the schema and translated the query."
echo ""
echo "This is the same code path that Kiro/Claude Code calls via MCP."
echo "============================================================"
