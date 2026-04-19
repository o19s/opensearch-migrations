#!/bin/bash

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "$SKILL_DIR/.env"

# Auto-detect venv for promptfoo Python provider
if [[ -z "${PROMPTFOO_PYTHON:-}" ]] && [[ -x "$SKILL_DIR/.venv/bin/python" ]]; then
    export PROMPTFOO_PYTHON="$SKILL_DIR/.venv/bin/python"
fi

# creating symlink to path where claude sdk expects the skills
mkdir -p "$SKILL_DIR/.claude/skills/migration-advisor"
ln -sf "$SKILL_DIR/SKILL.md" "$SKILL_DIR/.claude/skills/migration-advisor/SKILL.md"

AWS_REGION=$AWS_REGION \
AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION \
AWS_BEARER_TOKEN_BEDROCK=$AWS_BEARER_TOKEN_BEDROCK \
BEDROCK_INFERENCE_PROFILE_ARN=$BEDROCK_INFERENCE_PROFILE_ARN \
promptfoo eval -c "$SCRIPT_DIR/../evals/eval.yaml" --no-cache --max-concurrency 1