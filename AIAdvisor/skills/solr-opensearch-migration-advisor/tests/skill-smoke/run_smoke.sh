#!/usr/bin/env bash
# =============================================================================
# Skill Smoke Test — Step-by-step skill loading and evaluation
#
# Walks through five stages to prove: (a) the LLM is reachable, (b) adding
# skill content (nuggets) makes previously-failing assertions pass, and
# (c) promptfoo can drive the same evaluations at scale.
#
#   Step 1 — Bare metal baseline: call the LLM with NO skill. Verify it
#             responds. Shows the "before" picture: unpredictable output.
#
#   Step 2 — Nugget progression: load nuggets one at a time and run 3
#             assertions. Shows 1/3 → 2/3 → 3/3 as skill content grows.
#
#   Step 3 — Promptfoo inline: same assertions via promptfoo, prompt
#             content hardcoded in the YAML. Passes 1/3 (nugget 1 only).
#
#   Step 4 — Promptfoo external: assemble all 3 nuggets into a file,
#             reference it with file://. Passes 3/3.
#
#   Step 5 — Live Solr: run against a real Solr instance in YOLO mode,
#             then in interactive (multi-turn) mode.
#
# Usage:
#   ./run_smoke.sh                  # all steps (skips step 5 if no Solr)
#   ./run_smoke.sh --step 2         # single step
#   ./run_smoke.sh --steps 1,2,3    # specific steps
#   ./run_smoke.sh --step 5 --solr-url http://localhost:38983
#   ./run_smoke.sh --step 5 --start-docker  # spin up via connected tests compose
#
# Prerequisites:
#   - AWS CLI v2 with Bedrock access (for steps 1, 2, 5)
#   - Node.js 18+ with npx (for steps 3, 4)
#   - jq (for JSON handling)
#   - curl (for step 5 Solr queries)
#
# AWS credentials: set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN
# or use an SSO profile (aws sso login).
#
# Model override:
#   SMOKE_MODEL=amazon.nova-pro-v1:0 ./run_smoke.sh   # default: nova-micro
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NUGGETS_DIR="$SCRIPT_DIR/nuggets"
CONNECTED_COMPOSE="$SCRIPT_DIR/../connected/docker-compose.ports.yml"

MODEL_ID="${SMOKE_MODEL:-amazon.nova-micro-v1:0}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"

SOLR_URL=""
START_DOCKER=false
STEPS_TO_RUN=()

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --step)    STEPS_TO_RUN=("$2"); shift 2 ;;
    --steps)   IFS=',' read -ra STEPS_TO_RUN <<< "$2"; shift 2 ;;
    --solr-url)    SOLR_URL="$2"; shift 2 ;;
    --start-docker) START_DOCKER=true; shift ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

if [[ ${#STEPS_TO_RUN[@]} -eq 0 ]]; then
  STEPS_TO_RUN=(1 2 3 4 5)
fi

# ---------------------------------------------------------------------------
# Colors & output helpers
# ---------------------------------------------------------------------------
BOLD='\033[1m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[0;33m'; RED='\033[0;31m'; DIM='\033[2m'; RESET='\033[0m'

banner() { echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════════════${RESET}"; echo -e "${BOLD}${CYAN}  $1${RESET}"; echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════${RESET}\n"; }
step()   { echo -e "${BOLD}${GREEN}▶ $1${RESET}"; }
info()   { echo -e "${DIM}  $1${RESET}"; }
warn()   { echo -e "${YELLOW}⚠  $1${RESET}"; }
detail() { echo -e "  ${CYAN}→${RESET} $1"; }

# ---------------------------------------------------------------------------
# Assertion helpers (pass/fail with counts)
# ---------------------------------------------------------------------------
PASS_COUNT=0
FAIL_COUNT=0
EXPECTED_FAIL_COUNT=0  # expected failures (documented, non-fatal)

assert_contains() {
  local desc="$1" needle="$2" haystack="$3" expected_fail="${4:-false}"
  if echo "$haystack" | grep -qi "$needle"; then
    echo -e "  ${GREEN}✓ PASS${RESET}  $desc"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    if [[ "$expected_fail" == "true" ]]; then
      echo -e "  ${YELLOW}✗ EXPECTED FAIL${RESET}  $desc"
      echo -e "  ${DIM}       (proves skill nugget is needed — will pass once added)${RESET}"
      EXPECTED_FAIL_COUNT=$((EXPECTED_FAIL_COUNT + 1))
    else
      echo -e "  ${RED}✗ FAIL${RESET}  $desc"
      echo -e "         expected to find: ${BOLD}${needle}${RESET}"
      echo -e "         in: ${DIM}${haystack:0:200}${RESET}"
      FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
  fi
}

assert_nonempty() {
  local desc="$1" value="$2"
  if [[ -n "$value" ]]; then
    echo -e "  ${GREEN}✓ PASS${RESET}  $desc"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo -e "  ${RED}✗ FAIL${RESET}  $desc (empty response)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

print_summary() {
  local total=$((PASS_COUNT + FAIL_COUNT))
  echo ""
  echo -e "  ${BOLD}Passed:         ${GREEN}${PASS_COUNT}${RESET} / ${total}${RESET}"
  if [[ $EXPECTED_FAIL_COUNT -gt 0 ]]; then
    echo -e "  ${BOLD}Expected fails: ${YELLOW}${EXPECTED_FAIL_COUNT}${RESET} (intentional — prove skill is needed)${RESET}"
  fi
  if [[ $FAIL_COUNT -gt 0 ]]; then
    echo -e "  ${BOLD}Unexpected:     ${RED}${FAIL_COUNT}${RESET} (investigate)${RESET}"
  fi
}

# ---------------------------------------------------------------------------
# LLM call helpers (bare metal — AWS CLI only, no promptfoo)
# ---------------------------------------------------------------------------

check_aws_cli() {
  if ! command -v aws &>/dev/null; then
    warn "aws CLI not found — skipping this step"
    info "Install AWS CLI v2: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    return 1
  fi
  if ! command -v jq &>/dev/null; then
    warn "jq not found — skipping this step"
    info "Install jq: https://jqlang.github.io/jq/download/"
    return 1
  fi
  return 0
}

# call_llm SYSTEM_PROMPT USER_MESSAGE
# Prints the assistant response text. Returns 1 if the call fails.
call_llm() {
  local system_prompt="$1"
  local user_message="$2"

  local messages
  messages=$(jq -nc --arg t "$user_message" \
    '[{"role":"user","content":[{"text":$t}]}]')

  local cmd=(aws bedrock-runtime converse
    --model-id "$MODEL_ID"
    --region "$REGION"
    --messages "$messages"
  )

  if [[ -n "$system_prompt" ]]; then
    local sys_json
    sys_json=$(jq -nc --arg t "$system_prompt" '[{"text":$t}]')
    cmd+=(--system "$sys_json")
  fi

  local raw
  raw=$("${cmd[@]}" 2>/dev/null) || {
    warn "Bedrock call failed — check AWS credentials and region"
    return 1
  }

  echo "$raw" | jq -r '.output.message.content[0].text // empty'
}

# call_llm_multi SYSTEM_PROMPT MESSAGES_JSON
# Multi-turn version: pass the full conversation history as a JSON array.
call_llm_multi() {
  local system_prompt="$1"
  local messages_json="$2"

  local cmd=(aws bedrock-runtime converse
    --model-id "$MODEL_ID"
    --region "$REGION"
    --messages "$messages_json"
  )

  if [[ -n "$system_prompt" ]]; then
    local sys_json
    sys_json=$(jq -nc --arg t "$system_prompt" '[{"text":$t}]')
    cmd+=(--system "$sys_json")
  fi

  local raw
  raw=$("${cmd[@]}" 2>/dev/null) || {
    warn "Bedrock call failed"
    return 1
  }

  echo "$raw" | jq -r '.output.message.content[0].text // empty'
}

# Build a conversation turn array. Usage:
#   turns=$(new_turn "user" "hello")
#   turns=$(append_turn "$turns" "assistant" "hi there")
#   turns=$(append_turn "$turns" "user" "what is BM25?")
new_turn() {
  local role="$1" text="$2"
  jq -nc --arg r "$role" --arg t "$text" \
    '[{"role":$r,"content":[{"text":$t}]}]'
}

append_turn() {
  local history="$1" role="$2" text="$3"
  echo "$history" | jq --arg r "$role" --arg t "$text" \
    '. + [{"role":$r,"content":[{"text":$t}]}]'
}

# Assemble nuggets 1..N into a system prompt string
assemble_nuggets() {
  local count="$1"
  local skill=""
  for i in $(seq 1 "$count"); do
    local f
    f=$(ls "$NUGGETS_DIR/nugget-0${i}-"*.txt 2>/dev/null | head -1)
    if [[ -n "$f" ]]; then
      skill+=$'\n'"$(cat "$f")"$'\n'
    fi
  done
  echo -e "You are a Solr-to-OpenSearch migration advisor.\n${skill}"
}

# User question used for all nugget progression tests
NUGGET_TEST_PROMPT="YOLO — list the 3 most critical things to address when migrating from Solr 8 to OpenSearch."

# The 3 assertions (shared across steps 2, 3, 4)
run_three_assertions() {
  local response="$1"
  local expect_1="${2:-true}"  # true = expect pass
  local expect_2="${3:-true}"
  local expect_3="${4:-true}"

  assert_contains \
    "Response opens with EXPRESS MODE banner" \
    "EXPRESS MODE" "$response" \
    "$( [[ $expect_1 == true ]] && echo false || echo true )"

  assert_contains \
    "Response flags BM25 vs TF-IDF incompatibility" \
    "BM25 vs TF-IDF" "$response" \
    "$( [[ $expect_2 == true ]] && echo false || echo true )"

  assert_contains \
    "Response mentions opensearch-java client migration" \
    "opensearch-java" "$response" \
    "$( [[ $expect_3 == true ]] && echo false || echo true )"
}

# =============================================================================
# STEP 1 — Bare metal baseline: no skill, just prove the LLM is reachable
# =============================================================================
step1_bare_metal() {
  banner "Step 1 — Bare Metal Baseline (no skill)"
  info "Goal: prove the LLM is reachable and responds."
  info "No system prompt. Shows the 'before skill' behavior."
  echo ""

  check_aws_cli || return 0

  step "Calling $MODEL_ID with NO system prompt..."
  detail "aws bedrock-runtime converse --model-id $MODEL_ID"
  echo ""

  local response
  response=$(call_llm "" "$NUGGET_TEST_PROMPT") || return 0

  assert_nonempty "LLM returned a non-empty response" "$response"
  echo ""

  echo -e "${DIM}  --- Response (first 400 chars) ---${RESET}"
  echo -e "${DIM}  ${response:0:400}${RESET}"
  echo ""
  info "Note: without skill guidance, the model may or may not mention"
  info "EXPRESS MODE, BM25 vs TF-IDF, or opensearch-java — and it won't"
  info "format them consistently. That's what the skill fixes."
  echo ""

  # Run the 3 assertions but mark them all as expected-fail
  step "Running 3 assertions (all expected to fail without skill)..."
  run_three_assertions "$response" false false false
}

# =============================================================================
# STEP 2 — Nugget progression: 1/3 → 2/3 → 3/3
# =============================================================================
step2_nuggets() {
  banner "Step 2 — Nugget Progression"
  info "Goal: show how adding skill nuggets makes previously-failing tests pass."
  info "Same 3 assertions, same user question, different system prompts."
  echo ""

  check_aws_cli || return 0

  local n_nuggets
  for n_nuggets in 1 2 3; do
    local skill
    skill=$(assemble_nuggets "$n_nuggets")

    step "Loading $n_nuggets nugget(s) — assembling system prompt..."
    for i in $(seq 1 "$n_nuggets"); do
      local f
      f=$(ls "$NUGGETS_DIR/nugget-0${i}-"*.txt 2>/dev/null | head -1)
      [[ -n "$f" ]] && detail "$(basename "$f")"
    done
    echo ""

    local response
    response=$(call_llm "$skill" "$NUGGET_TEST_PROMPT") || continue

    echo -e "${DIM}  --- Response (first 300 chars) ---${RESET}"
    echo -e "${DIM}  ${response:0:300}${RESET}"
    echo ""

    # Which assertions are expected to pass at this nugget count?
    local e1 e2 e3
    e1=$( [[ $n_nuggets -ge 1 ]] && echo true || echo false )
    e2=$( [[ $n_nuggets -ge 2 ]] && echo true || echo false )
    e3=$( [[ $n_nuggets -ge 3 ]] && echo true || echo false )

    echo -e "  ${BOLD}Assertions with $n_nuggets nugget(s) (expect ${n_nuggets}/3 to pass):${RESET}"
    run_three_assertions "$response" "$e1" "$e2" "$e3"
    echo ""
  done
}

# =============================================================================
# STEP 3 — Promptfoo inline: prompt hardcoded in YAML, 1/3 pass
# =============================================================================
step3_promptfoo_inline() {
  banner "Step 3 — Promptfoo Inline (1/3 expected)"
  info "Goal: run the same 3 assertions via promptfoo."
  info "The system prompt is hardcoded inside promptfooconfig-inline.yaml."
  info "Only nugget 1 is loaded → expect 1 pass, 2 expected failures."
  echo ""

  if ! command -v npx &>/dev/null; then
    warn "npx not found — skipping step 3"
    info "Install Node.js 18+: https://nodejs.org/"
    return 0
  fi

  local config="$SCRIPT_DIR/promptfooconfig-inline.yaml"
  step "Running: npx promptfoo eval --config $config"
  echo ""

  # promptfoo exits non-zero when assertions fail — that's expected here
  npx promptfoo eval --config "$config" --no-cache 2>&1 || true
  echo ""
  info "Expected: 1/3 pass. Tests 2 and 3 intentionally fail — they need nuggets 2 and 3."
}

# =============================================================================
# STEP 4 — Promptfoo external: assembled prompt from file, 3/3 pass
# =============================================================================
step4_promptfoo_external() {
  banner "Step 4 — Promptfoo External (3/3 expected)"
  info "Goal: assemble all 3 nuggets into a file, then run promptfoo with file://."
  info "All 3 assertions should now pass."
  echo ""

  if ! command -v npx &>/dev/null; then
    warn "npx not found — skipping step 4"
    return 0
  fi

  # Assemble the full skill into a file for file:// reference
  local assembled="$SCRIPT_DIR/skill-assembled.txt"
  step "Assembling all 3 nuggets into skill-assembled.txt..."
  assemble_nuggets 3 > "$assembled"
  detail "$(wc -l < "$assembled") lines written to $assembled"
  echo ""

  local config="$SCRIPT_DIR/promptfooconfig-external.yaml"
  step "Running: npx promptfoo eval --config $config"
  echo ""

  npx promptfoo eval --config "$config" --no-cache 2>&1 || {
    warn "promptfoo reported failures — check output above"
    return 0
  }

  echo ""
  info "Expected: 3/3 pass. All nuggets loaded, all assertions satisfied."
}

# =============================================================================
# STEP 5 — Live Solr: YOLO mode then interactive multi-turn
# =============================================================================
step5_live_solr() {
  banner "Step 5 — Live Solr Integration"

  # ---------------------------------------------------------------------------
  # Resolve Solr URL
  # ---------------------------------------------------------------------------
  if [[ "$START_DOCKER" == true ]]; then
    step "Starting Docker services (from connected tests)..."
    if [[ ! -f "$CONNECTED_COMPOSE" ]]; then
      warn "docker-compose.ports.yml not found at: $CONNECTED_COMPOSE"
      return 0
    fi
    docker compose -f "$CONNECTED_COMPOSE" up -d
    SOLR_URL="http://localhost:38983"
    info "Waiting for Solr..."
    local elapsed=0
    while ! curl -sf "$SOLR_URL/solr/admin/info/system" >/dev/null 2>&1; do
      sleep 2; elapsed=$((elapsed + 2))
      [[ $elapsed -ge 60 ]] && { warn "Solr did not start in 60s"; return 0; }
    done
    info "Solr ready"
  elif [[ -z "$SOLR_URL" ]]; then
    # Auto-detect: check if connected tests' Solr is already running
    if curl -sf "http://localhost:38983/solr/admin/info/system" >/dev/null 2>&1; then
      SOLR_URL="http://localhost:38983"
      info "Auto-detected running Solr at $SOLR_URL"
    else
      warn "No Solr instance found. Skipping step 5."
      info "Options:"
      info "  ./run_smoke.sh --step 5 --solr-url http://your-solr:8983"
      info "  ./run_smoke.sh --step 5 --start-docker"
      info "  cd ../connected && ./run_connected_tests.sh --no-teardown  # then re-run"
      return 0
    fi
  fi

  check_aws_cli || return 0

  info "Using Solr: $SOLR_URL"
  echo ""

  # Load the full skill
  local skill
  skill=$(assemble_nuggets 3)

  # -----------------------------------------------------------------------
  # 5a. YOLO mode — no questions, just generate
  # -----------------------------------------------------------------------
  step "5a. YOLO mode — fetch live schema, generate spec in one shot"
  echo ""

  # Fetch available collections
  local collections_resp
  collections_resp=$(curl -sf "$SOLR_URL/solr/admin/collections?action=LIST&wt=json" 2>/dev/null) || {
    warn "Could not reach Solr collections API at $SOLR_URL"
    return 0
  }
  local collections
  collections=$(echo "$collections_resp" | jq -r '.collections[]?' 2>/dev/null | head -3)

  if [[ -z "$collections" ]]; then
    warn "No collections found — Solr may be empty."
    info "Seed first: cd ../connected && ./run_connected_tests.sh --no-teardown"
    return 0
  fi

  local collection
  collection=$(echo "$collections" | head -1)
  detail "Found collection: $collection"
  detail "Fetching schema fields..."

  local schema_resp
  schema_resp=$(curl -sf "$SOLR_URL/solr/$collection/schema/fields?wt=json" 2>/dev/null)
  local fields
  fields=$(echo "$schema_resp" | jq -r '.fields[]? | "  \(.name) (\(.type))"' 2>/dev/null | head -20)

  info "Schema fields (first 20):"
  echo "$fields" | while IFS= read -r line; do info "  $line"; done
  echo ""

  local yolo_prompt
  yolo_prompt=$(cat <<EOF
YOLO — Generate a complete migration spec for the '$collection' Solr collection.

Schema fields:
$fields

Stack: assume Spring Boot application with SolrJ client.
EOF
)

  step "Calling LLM in YOLO mode..."
  local yolo_response
  yolo_response=$(call_llm "$skill" "$yolo_prompt") || return 0

  echo ""
  echo -e "${DIM}  --- YOLO Response (first 600 chars) ---${RESET}"
  echo "$yolo_response" | head -20 | while IFS= read -r line; do echo -e "${DIM}  $line${RESET}"; done
  echo ""

  assert_contains "YOLO: opens with EXPRESS MODE banner"   "EXPRESS MODE"    "$yolo_response"
  assert_contains "YOLO: flags BM25 vs TF-IDF"            "BM25 vs TF-IDF"  "$yolo_response"
  assert_contains "YOLO: recommends opensearch-java"       "opensearch-java" "$yolo_response"
  assert_contains "YOLO: marks at least one assumption"    "[ASSUMED:"       "$yolo_response"
  echo ""

  # -----------------------------------------------------------------------
  # 5b. Interactive mode — multi-turn conversation
  # -----------------------------------------------------------------------
  step "5b. Interactive mode — scripted multi-turn conversation"
  info "Demonstrates: without YOLO, the advisor asks clarifying questions."
  info "The conversation is scripted (pre-canned turns) to keep the test deterministic."
  echo ""

  # Turn 1: vague migration request — no YOLO trigger
  local turn1_user="I need to migrate my Solr setup to OpenSearch. Where do I start?"
  detail "Turn 1 →  $turn1_user"

  local turns
  turns=$(new_turn "user" "$turn1_user")
  local turn1_resp
  turn1_resp=$(call_llm_multi "$skill" "$turns") || return 0

  echo ""
  echo -e "${DIM}  --- Turn 1 Response ---${RESET}"
  echo "$turn1_resp" | head -10 | while IFS= read -r line; do echo -e "${DIM}  $line${RESET}"; done
  echo ""

  assert_contains \
    "Interactive Turn 1: advisor asks at least one clarifying question" \
    "?" "$turn1_resp"

  # Turn 2: provide context the advisor might have asked about
  local turn2_user="We have a SolrCloud cluster with 2 collections, using SolrJ in a Spring Boot app. Index is about 500GB, ~200 QPS peak. We want to move to OpenSearch."
  detail "Turn 2 →  $turn2_user"

  turns=$(append_turn "$turns" "assistant" "$turn1_resp")
  turns=$(append_turn "$turns" "user" "$turn2_user")
  local turn2_resp
  turn2_resp=$(call_llm_multi "$skill" "$turns") || return 0

  echo ""
  echo -e "${DIM}  --- Turn 2 Response ---${RESET}"
  echo "$turn2_resp" | head -10 | while IFS= read -r line; do echo -e "${DIM}  $line${RESET}"; done
  echo ""

  assert_contains \
    "Interactive Turn 2: response references the provided context (SolrJ)" \
    "SolrJ" "$turn2_resp"

  assert_contains \
    "Interactive Turn 2: mentions BM25 scoring difference (nugget 2 in play)" \
    "BM25" "$turn2_resp"
}

# =============================================================================
# Main
# =============================================================================
ALL_STEPS=(1 2 3 4 5)

should_run() {
  local s="$1"
  for r in "${STEPS_TO_RUN[@]}"; do [[ "$r" == "$s" ]] && return 0; done
  return 1
}

echo ""
echo -e "${BOLD}Skill Smoke Test${RESET}"
echo -e "  Steps:  ${STEPS_TO_RUN[*]}"
echo -e "  Model:  $MODEL_ID"
echo -e "  Region: $REGION"

should_run 1 && step1_bare_metal
should_run 2 && step2_nuggets
should_run 3 && step3_promptfoo_inline
should_run 4 && step4_promptfoo_external
should_run 5 && step5_live_solr

banner "Summary"
print_summary

if [[ $FAIL_COUNT -gt 0 ]]; then
  echo ""
  warn "$FAIL_COUNT unexpected failure(s) — see output above"
  exit 1
fi
exit 0
