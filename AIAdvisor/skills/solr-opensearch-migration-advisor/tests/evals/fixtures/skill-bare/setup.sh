#!/bin/bash
# Create the bare skill fixture — symlinks to the real skill but with empty steering/.
# Run this once before running eval-guidance-impact.yaml.
#
# Usage: bash fixtures/skill-bare/setup.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../../../../solr-opensearch-migration-advisor" && pwd)"

echo "Creating bare skill fixture at $SCRIPT_DIR"
echo "Linking to real skill at $SKILL_DIR"

# Symlink everything except steering/
for item in SKILL.md scripts references pyproject.toml README.md uv.lock .env.example .gitignore; do
  if [ -e "$SKILL_DIR/$item" ]; then
    ln -sf "$SKILL_DIR/$item" "$SCRIPT_DIR/$item"
    echo "  linked $item"
  fi
done

# Ensure steering/ exists but is empty (just a README)
mkdir -p "$SCRIPT_DIR/steering"
echo "# No steering content (bare skill for comparison testing)" > "$SCRIPT_DIR/steering/README.md"

echo "Done. Bare skill fixture ready."
