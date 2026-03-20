#!/usr/bin/env bash
# Usage: ./bump-version.sh <new-version>
# Example: ./bump-version.sh 0.3.0

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <new-version>"
  echo "Example: $0 0.3.0"
  exit 1
fi

NEW_VERSION="$1"
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Update VERSION file
echo "$NEW_VERSION" > "$REPO_ROOT/VERSION"

# Update SKILL.md frontmatter
sed -i "s/^version: .*/version: $NEW_VERSION/" \
  "$REPO_ROOT/04-skills/solr-to-opensearch-migration/SKILL.md"

echo "Version bumped to $NEW_VERSION"
echo "  - VERSION"
echo "  - 04-skills/solr-to-opensearch-migration/SKILL.md"
