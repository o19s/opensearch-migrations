#!/bin/bash
#
# Container integration test: builds the image, runs unit tests inside it,
# and verifies a skill tool can be invoked.
#
# ============================================================================
#  NOTE: THIS SCRIPT IS NOT YET WIRED INTO CI
#
#  This test must be run manually before merging changes to the Dockerfile,
#  docker-compose.yml, or .dockerignore.
#
#  PENDING DECISION: Should this be added as a job in .github/workflows/CI.yml?
#    - Adds ~2-3 min to CI for PRs touching AIAdvisor/skills/solr-opensearch-*
#    - Uses Docker on ubuntu-latest runner (no secrets needed)
#    - Would catch Dockerfile breakage before merge
#    - ~20 lines to add to CI.yml with a paths filter
#
#  Usage:
#    cd AIAdvisor/skills/solr-opensearch-migration-advisor
#    bash tests/scripts/test_container.sh
#
#  Requires: Docker
# ============================================================================
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
IMAGE_NAME="solr-advisor-test"

echo "=== Building container ==="
docker build -t "$IMAGE_NAME" "$SKILL_DIR"

echo ""
echo "=== Running unit tests inside container ==="
docker run --rm "$IMAGE_NAME"

echo ""
echo "=== Verifying skill tool invocation ==="
docker run --rm "$IMAGE_NAME" \
    uv run python -c "
from scripts.skill import SolrToOpenSearchMigrationSkill
skill = SolrToOpenSearchMigrationSkill()

# Test schema conversion
result = skill.convert_query('title:opensearch AND price:[10 TO 100]')
assert 'bool' in result, f'Expected bool query, got: {result}'

# Test session handling
response = skill.handle_message('Hello', session_id='container-test')
assert len(response) > 0, 'Expected non-empty response'

print('All container integration checks passed.')
"

echo ""
echo "=== Verifying session persistence with volume ==="
TMPDIR=$(mktemp -d)
docker run --rm -v "$TMPDIR:/app/sessions" "$IMAGE_NAME" \
    uv run python -c "
from scripts.skill import SolrToOpenSearchMigrationSkill
skill = SolrToOpenSearchMigrationSkill()
skill.handle_message('Hello', session_id='persist-test')
print('Session written.')
"

if [ -f "$TMPDIR/persist-test.json" ]; then
    echo "Session file persisted to volume: OK"
else
    echo "ERROR: Session file not found in mounted volume"
    rm -rf "$TMPDIR"
    exit 1
fi

rm -rf "$TMPDIR"

echo ""
echo "=== All container integration tests passed ==="
