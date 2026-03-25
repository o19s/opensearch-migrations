#!/usr/bin/env bash
# run_demo.sh — YOLO TechProducts Migration: generate spec + run SSCCE eval
#
# Usage:
#   ./run_demo.sh              # uses AWS Bedrock (default provider in config)
#   OPENAI_API_KEY=sk-... ./run_demo.sh   # override to OpenAI
#
# What this does:
#   1. Resets artifacts directory (clears previous run)
#   2. Runs the promptfoo SSCCE — this IS the YOLO migration:
#      the LLM generates the techproducts migration spec and the
#      assertions evaluate it in the same pass
#   3. Extracts and saves the generated migration spec as a readable artifact
#   4. Prints a human-readable summary

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="$SCRIPT_DIR/artifacts"
EVAL_OUTPUT="$ARTIFACTS_DIR/eval-result.json"
SPEC_OUTPUT="$ARTIFACTS_DIR/yolo-techproducts-spec.md"

# ── Step 1: Reset ──────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 1/3 — Reset artifacts"
echo "═══════════════════════════════════════════════════════════════"
rm -rf "$ARTIFACTS_DIR"
mkdir -p "$ARTIFACTS_DIR"
echo "  Cleared: $ARTIFACTS_DIR"

# ── Step 2: Run YOLO migration + SSCCE eval ────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 2/3 — Run YOLO migration (LLM generates spec + eval)"
echo "═══════════════════════════════════════════════════════════════"
echo "  Config:  $SCRIPT_DIR/promptfooconfig.yaml"
echo "  Output:  $EVAL_OUTPUT"
echo ""

npx promptfoo eval \
  --config "$SCRIPT_DIR/promptfooconfig.yaml" \
  --output "$EVAL_OUTPUT" \
  --no-cache

# ── Step 3: Extract spec + print summary ───────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 3/3 — Extract migration spec and summarise results"
echo "═══════════════════════════════════════════════════════════════"

export ARTIFACTS_DIR

python3 - <<'PYEOF'
import json, sys, os

artifacts_dir = os.environ.get("ARTIFACTS_DIR", "artifacts")
eval_output   = os.path.join(artifacts_dir, "eval-result.json")
spec_output   = os.path.join(artifacts_dir, "yolo-techproducts-spec.md")

with open(eval_output) as f:
    data = json.load(f)

results = data["results"]["results"]
stats   = data["results"]["stats"]
result  = results[0]

# Save the migration spec
spec_text = result["response"]["output"]
with open(spec_output, "w") as f:
    f.write(spec_text)

# Print assertions breakdown
grading = result.get("gradingResult", {})
component_results = grading.get("componentResults", [])

print(f"\n  Migration spec saved → {spec_output}")
print(f"  ({len(spec_text):,} characters)\n")

print("  Assertion results:")
for cr in component_results:
    icon  = "✓" if cr.get("pass") else "✗"
    desc  = cr.get("assertion", {}).get("description") or cr.get("assertion", {}).get("value", "")[:60]
    print(f"    {icon}  {desc}")

passed  = stats.get("successes", 0)
failed  = stats.get("failures",  0)
total   = passed + failed
tokens  = data["results"].get("stats", {}).get("tokenUsage", {})
cost    = result.get("cost", 0) or 0

print(f"\n  Tests:  {passed}/{total} passed")
if cost:
    print(f"  Cost:   ${cost:.4f}")
print()
PYEOF

# Export for the heredoc
export ARTIFACTS_DIR="$ARTIFACTS_DIR"

echo "  To read the full migration spec:"
echo "    cat $SPEC_OUTPUT"
echo ""
echo "  To explore results in the browser:"
echo "    npx promptfoo view"
echo ""
