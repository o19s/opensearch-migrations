#!/bin/bash
#
# Generate eval reports for a single SMA eval file.
#
# Produces three outputs:
#   1. Markdown summary  → tests/artifacts/<timestamp>/<name>-report.md
#   2. HTML dashboard    → tests/artifacts/<timestamp>/<name>-report.html
#   3. Interactive web   → `promptfoo view` (printed as a reminder)
#
# Usage:
#   ./tests/scripts/generate_report.sh tests/evals/eval-fully-loaded.yaml
#   ./tests/scripts/generate_report.sh tests/evals/eval-blue-sky.yaml
#   ./tests/scripts/generate_report.sh tests/evals/eval-yolo.yaml
#   ./tests/scripts/generate_report.sh tests/evals/eval.yaml
#
#   # With filter (only run matching tests):
#   ./tests/scripts/generate_report.sh tests/evals/eval-fully-loaded.yaml "^det-"
#
# Prerequisites:
#   cd AIAdvisor/skills/solr-opensearch-migration-advisor
#   uv sync --extra eval
#   source .venv/bin/activate
#   cp .env.example .env   # fill in CLAUDE_CODE_OAUTH_TOKEN
#   export PROMPTFOO_PYTHON=$(pwd)/.venv/bin/python

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
EVAL_FILE="${1:?Usage: $0 <eval-yaml> [filter-pattern]}"
FILTER="${2:-}"

# Resolve eval file path
if [[ ! -f "$EVAL_FILE" ]]; then
    EVAL_FILE="$SKILL_DIR/$EVAL_FILE"
fi

if [[ ! -f "$EVAL_FILE" ]]; then
    echo "Error: eval file not found: $1" >&2
    exit 1
fi

EVAL_NAME="$(basename "$EVAL_FILE" .yaml)"
TIMESTAMP="$(date -u +%Y-%m-%dT%H%M%SZ)"
ARTIFACT_DIR="$SKILL_DIR/tests/artifacts/$TIMESTAMP"
mkdir -p "$ARTIFACT_DIR"

JSON_OUT="$ARTIFACT_DIR/${EVAL_NAME}-results.json"
HTML_OUT="$ARTIFACT_DIR/${EVAL_NAME}-report.html"
MD_OUT="$ARTIFACT_DIR/${EVAL_NAME}-report.md"

# Source env if available
if [[ -f "$SKILL_DIR/.env" ]]; then
    set -a
    source "$SKILL_DIR/.env"
    set +a
fi

# Ensure skill symlink exists
mkdir -p "$SKILL_DIR/.claude/skills/migration-advisor"
ln -sf "$SKILL_DIR/SKILL.md" "$SKILL_DIR/.claude/skills/migration-advisor/SKILL.md" 2>/dev/null || true

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " SMA Eval Report Generator"
echo " Eval:   $EVAL_NAME"
echo " Output: $ARTIFACT_DIR/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Build promptfoo command
PROMPTFOO_CMD="promptfoo eval -c $EVAL_FILE --no-cache --max-concurrency 1 --output $JSON_OUT --output $HTML_OUT"
if [[ -n "$FILTER" ]]; then
    PROMPTFOO_CMD="$PROMPTFOO_CMD --filter-pattern $FILTER"
    echo " Filter: $FILTER"
fi

echo ""
echo "Running promptfoo eval..."
echo ""

eval "$PROMPTFOO_CMD"
EVAL_EXIT=$?

if [[ ! -f "$JSON_OUT" ]]; then
    echo "Error: promptfoo did not produce JSON output" >&2
    exit 1
fi

# Generate markdown report from JSON
echo ""
echo "Generating markdown report..."

cat > "$MD_OUT" << 'HEADER'
# SMA Eval Report
HEADER

# Add metadata
cat >> "$MD_OUT" << EOF

**Eval file:** \`$EVAL_NAME.yaml\`
**Run date:** $TIMESTAMP
**Filter:** ${FILTER:-none}

---

## Summary

EOF

# Parse JSON and generate summary table
jq -r '
  # Extract results
  .results.results as $results |

  # Count totals
  ($results | length) as $total |
  ([$results[] | select(.success == true)] | length) as $passed |
  ([$results[] | select(.success == false)] | length) as $failed |

  # Pass rate
  (if $total > 0 then ($passed * 100 / $total | floor) else 0 end) as $rate |

  "| Metric | Value |\n|--------|-------|\n| Total tests | \($total) |\n| Passed | \($passed) |\n| Failed | \($failed) |\n| Pass rate | \($rate)% |"
' "$JSON_OUT" >> "$MD_OUT"

# Group by tier prefix
cat >> "$MD_OUT" << 'EOF'

## Results by Tier

EOF

jq -r '
  .results.results as $results |

  # Extract tier prefix from description
  [
    $results[] |
    {
      tier: (.description // "unknown" | capture("^(?<t>[a-z]+-)[0-9]") // {t: "other-"} | .t | rtrimstr("-")),
      success: .success
    }
  ] |
  group_by(.tier) |
  map({
    tier: .[0].tier,
    total: length,
    passed: [.[] | select(.success == true)] | length,
    failed: [.[] | select(.success == false)] | length
  }) |

  "| Tier | Total | Passed | Failed | Rate |\n|------|-------|--------|--------|------|\n" +
  (map("| \(.tier) | \(.total) | \(.passed) | \(.failed) | \(if .total > 0 then (.passed * 100 / .total | floor) else 0 end)% |") | join("\n"))
' "$JSON_OUT" >> "$MD_OUT"

# Individual test results
cat >> "$MD_OUT" << 'EOF'

## Individual Test Results

EOF

jq -r '
  .results.results[] |
  {
    desc: (.description // "unknown"),
    status: (if .success then "PASS" else "FAIL" end),
    assertions_pass: ([.gradingResult.componentResults[]? | select(.pass == true)] | length),
    assertions_total: ([.gradingResult.componentResults[]?] | length),
    failures: [.gradingResult.componentResults[]? | select(.pass == false) | .reason // "no reason"] | join("; ")
  } |
  if .status == "PASS" then
    "- [x] **\(.desc)** (\(.assertions_pass)/\(.assertions_total) assertions)"
  else
    "- [ ] **\(.desc)** (\(.assertions_pass)/\(.assertions_total) assertions)\n  > \(.failures)"
  end
' "$JSON_OUT" >> "$MD_OUT"

# Footer
cat >> "$MD_OUT" << EOF

---

## Artifacts

- JSON results: \`$(basename "$JSON_OUT")\`
- HTML report: \`$(basename "$HTML_OUT")\`
- Interactive: run \`promptfoo view\` from the evals directory

*Generated by generate_report.sh*
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Reports generated:"
echo ""
echo "   Markdown: $MD_OUT"
echo "   HTML:     $HTML_OUT"
echo "   JSON:     $JSON_OUT"
echo ""
echo "   Interactive: cd tests/evals && promptfoo view"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $EVAL_EXIT
