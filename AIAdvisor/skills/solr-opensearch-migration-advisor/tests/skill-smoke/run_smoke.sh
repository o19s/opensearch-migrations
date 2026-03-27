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
# Provider selection (automatic — see below):
#   ./run_smoke.sh                        # auto-detect: Ollama if local, else Bedrock
#   ./run_smoke.sh --provider ollama      # force Ollama
#   ./run_smoke.sh --provider bedrock     # force Bedrock
#
# Provider auto-detection priority:
#   1. --provider flag or SMOKE_PROVIDER env var   → use what you said
#   2. AWS_ACCESS_KEY_ID / AWS_PROFILE is set      → Bedrock (you configured cloud)
#   3. Ollama is running on localhost               → Ollama (free, fast, local)
#   4. None of the above                           → try Bedrock (instance profile?)
#
# Model override:
#   OLLAMA_MODEL=llama3.1:8b ./run_smoke.sh         # default: qwen2.5:7b
#   BEDROCK_MODEL=amazon.nova-pro-v1:0 ./run_smoke.sh  # default: nova-micro
#
# Prerequisites:
#   - jq (for JSON handling — all steps)
#   - curl (for Ollama calls and step 5 Solr queries)
#   - Node.js 18+ with npx (for steps 3, 4 only — promptfoo)
#   - AWS CLI v2 with Bedrock access (only if using Bedrock provider)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NUGGETS_DIR="$SCRIPT_DIR/nuggets"
CONNECTED_COMPOSE="$SCRIPT_DIR/../connected/docker-compose.ports.yml"

# ---------------------------------------------------------------------------
# Defaults — overridable via env vars
# ---------------------------------------------------------------------------
# Ollama
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
# OLLAMA_MODEL is resolved below after Ollama is detected.
# If you set it explicitly, that model is used (and must be pulled).
# Otherwise, auto-detection picks the best available model.
#
# Recommended for 12 GB VRAM:
#   qwen3:14b      — best instruction-following, ~9 GB
#   llama3:8b      — solid general-purpose, ~5 GB
#   mistral:latest — fast, good quality, ~4 GB
#   qwen2.5:7b     — good instruction-following, ~5 GB
OLLAMA_MODEL_EXPLICIT="${OLLAMA_MODEL:-}"  # empty = auto-detect
OLLAMA_MODEL=""  # set by _resolve_ollama_model

# Bedrock
BEDROCK_MODEL="${BEDROCK_MODEL:-amazon.nova-micro-v1:0}"
BEDROCK_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

SOLR_URL=""
START_DOCKER=false
STEPS_TO_RUN=()
PROVIDER_OVERRIDE=""  # set by --provider flag

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --step)        STEPS_TO_RUN=("$2"); shift 2 ;;
    --steps)       IFS=',' read -ra STEPS_TO_RUN <<< "$2"; shift 2 ;;
    --solr-url)    SOLR_URL="$2"; shift 2 ;;
    --start-docker) START_DOCKER=true; shift ;;
    --provider)    PROVIDER_OVERRIDE="$2"; shift 2 ;;
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
MAGENTA='\033[0;35m'

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
EXPECTED_FAIL_COUNT=0

assert_contains() {
  local desc="$1" needle="$2" haystack="$3" expected_fail="${4:-false}"
  if echo "$haystack" | grep -qiF "$needle"; then
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

# =============================================================================
# PROVIDER DETECTION
# =============================================================================
# Priority:
#   1. --provider flag / SMOKE_PROVIDER env var   (explicit wins)
#   2. AWS_ACCESS_KEY_ID or AWS_PROFILE is set    (user configured cloud creds)
#   3. Ollama is running on localhost              (free, fast, no cloud needed)
#   4. Fall through to Bedrock                    (might work via instance profile)
# =============================================================================

PROVIDER=""       # "ollama" or "bedrock" — set by detect_provider
PROVIDER_WHY=""   # human-readable reason for the choice

detect_provider() {
  # 1. Explicit override
  if [[ -n "$PROVIDER_OVERRIDE" ]]; then
    case "$PROVIDER_OVERRIDE" in
      ollama)   PROVIDER="ollama";  PROVIDER_WHY="--provider ollama flag" ;;
      bedrock)  PROVIDER="bedrock"; PROVIDER_WHY="--provider bedrock flag" ;;
      *) echo "Unknown provider: $PROVIDER_OVERRIDE (use 'ollama' or 'bedrock')"; exit 1 ;;
    esac
    return
  fi

  if [[ -n "${SMOKE_PROVIDER:-}" ]]; then
    if [[ "$SMOKE_PROVIDER" == ollama* ]]; then
      PROVIDER="ollama";  PROVIDER_WHY="SMOKE_PROVIDER env var"
    else
      PROVIDER="bedrock"; PROVIDER_WHY="SMOKE_PROVIDER env var"
    fi
    return
  fi

  # 2. AWS credentials explicitly set → user wants cloud
  if [[ -n "${AWS_ACCESS_KEY_ID:-}" || -n "${AWS_PROFILE:-}" ]]; then
    PROVIDER="bedrock"
    if [[ -n "${AWS_ACCESS_KEY_ID:-}" ]]; then
      PROVIDER_WHY="AWS_ACCESS_KEY_ID is set"
    else
      PROVIDER_WHY="AWS_PROFILE is set (${AWS_PROFILE})"
    fi
    return
  fi

  # 3. Ollama running locally → use it (free, fast, no cloud dependency)
  if curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
    PROVIDER="ollama"
    PROVIDER_WHY="Ollama detected at ${OLLAMA_URL} (no AWS credentials in env)"
    return
  fi

  # 4. Fallback: Bedrock (might work via instance profile / SSO session)
  PROVIDER="bedrock"
  PROVIDER_WHY="default fallback (no Ollama found, no explicit AWS creds — will try instance profile)"
}

detect_provider

# ---------------------------------------------------------------------------
# Ollama model resolution — pick the best available model
# ---------------------------------------------------------------------------
# Preference order: models known to follow structured instructions well.
# Larger models follow formatting rules (EXPRESS MODE banner, [ASSUMED:])
# much more reliably than 7B models.
OLLAMA_PREFERRED_MODELS=(
  "qwen3:14b"
  "qwen2.5:14b"
  "llama3.1:8b"
  "llama3:8b"
  "gemma2:9b"
  "mistral-nemo:latest"
  "mistral:latest"
  "qwen2.5:7b"
  "qwen3:8b"
  "llama3.2:latest"
  "phi3:14b"
  "deepseek-r1:14b"
)

_resolve_ollama_model() {
  # If user explicitly set OLLAMA_MODEL, use it (even if not pulled)
  if [[ -n "$OLLAMA_MODEL_EXPLICIT" ]]; then
    OLLAMA_MODEL="$OLLAMA_MODEL_EXPLICIT"
    return
  fi

  # Query Ollama for available models
  local available
  available=$(curl -sf "$OLLAMA_URL/api/tags" 2>/dev/null | jq -r '.models[].name' 2>/dev/null) || {
    OLLAMA_MODEL="qwen3:14b"  # fallback default if can't query
    return
  }

  # Try each preferred model in order
  for candidate in "${OLLAMA_PREFERRED_MODELS[@]}"; do
    if echo "$available" | grep -qxF "$candidate"; then
      OLLAMA_MODEL="$candidate"
      return
    fi
  done

  # No preferred model found — pick the first non-embedding model available
  local fallback
  fallback=$(echo "$available" | grep -ivE 'embed|nomic|snowflake|mxbai' | head -1)
  if [[ -n "$fallback" ]]; then
    OLLAMA_MODEL="$fallback"
    return
  fi

  # Nothing at all
  OLLAMA_MODEL="qwen3:14b"  # will fail at preflight with helpful message
}

if [[ "$PROVIDER" == "ollama" ]]; then
  _resolve_ollama_model
fi

# Set display names and the promptfoo provider ID (exported for YAML configs)
if [[ "$PROVIDER" == "ollama" ]]; then
  DISPLAY_MODEL="$OLLAMA_MODEL"
  DISPLAY_ENDPOINT="$OLLAMA_URL"
  export SMOKE_PROVIDER="ollama:chat:${OLLAMA_MODEL}"
else
  DISPLAY_MODEL="$BEDROCK_MODEL"
  DISPLAY_ENDPOINT="Bedrock (${BEDROCK_REGION})"
  export SMOKE_PROVIDER="bedrock:${BEDROCK_MODEL}"
fi

# ---------------------------------------------------------------------------
# Provider banner — big and loud so you always know what's calling what
# ---------------------------------------------------------------------------
if [[ "$PROVIDER" == "ollama" ]]; then
  _P_COLOR="$MAGENTA"
  _P_LABEL="OLLAMA (local)"
else
  _P_COLOR="$CYAN"
  _P_LABEL="AWS BEDROCK (cloud)"
fi

echo ""
echo -e "${BOLD}${_P_COLOR}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${_P_COLOR}║  PROVIDER: ${_P_LABEL}$(printf '%*s' $((40 - ${#_P_LABEL})) '')║${RESET}"
echo -e "${BOLD}${_P_COLOR}║                                                              ║${RESET}"
echo -e "${BOLD}${_P_COLOR}║${RESET}  Model:    ${BOLD}${DISPLAY_MODEL}${RESET}$(printf '%*s' $((48 - ${#DISPLAY_MODEL})) '')${BOLD}${_P_COLOR}║${RESET}"
echo -e "${BOLD}${_P_COLOR}║${RESET}  Endpoint: ${DISPLAY_ENDPOINT}$(printf '%*s' $((48 - ${#DISPLAY_ENDPOINT})) '')${BOLD}${_P_COLOR}║${RESET}"
echo -e "${BOLD}${_P_COLOR}║${RESET}  Why:      ${PROVIDER_WHY:0:48}$(printf '%*s' $((48 - ${#PROVIDER_WHY})) '')${BOLD}${_P_COLOR}║${RESET}"
echo -e "${BOLD}${_P_COLOR}║                                                              ║${RESET}"
if [[ "$PROVIDER" == "ollama" ]]; then
  echo -e "${BOLD}${_P_COLOR}║${RESET}  ${DIM}To use Bedrock:  export AWS_ACCESS_KEY_ID=... or${RESET}       ${BOLD}${_P_COLOR}║${RESET}"
  echo -e "${BOLD}${_P_COLOR}║${RESET}  ${DIM}                 ./run_smoke.sh --provider bedrock${RESET}      ${BOLD}${_P_COLOR}║${RESET}"
else
  echo -e "${BOLD}${_P_COLOR}║${RESET}  ${DIM}To use Ollama:   ollama serve && ollama pull ${OLLAMA_MODEL}${RESET}$(printf '%*s' $((14 - ${#OLLAMA_MODEL})) '')${BOLD}${_P_COLOR}║${RESET}"
  echo -e "${BOLD}${_P_COLOR}║${RESET}  ${DIM}                 ./run_smoke.sh --provider ollama${RESET}       ${BOLD}${_P_COLOR}║${RESET}"
fi
echo -e "${BOLD}${_P_COLOR}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# =============================================================================
# LLM call functions — Ollama and Bedrock backends
# =============================================================================
# Both providers use the same interface:
#   call_llm "system prompt" "user message"       → prints response text
#   call_llm_multi "system prompt" "messages_json" → prints response text
#
# Conversation history (messages_json) uses the OpenAI-compatible format:
#   [{"role":"user","content":"hello"}, {"role":"assistant","content":"hi"}, ...]
# The Bedrock backend converts this to Bedrock's nested format internally.
# =============================================================================

# --- Ollama backend ---------------------------------------------------------

_call_llm_ollama() {
  local system_prompt="$1" user_message="$2"

  local messages
  if [[ -n "$system_prompt" ]]; then
    messages=$(jq -nc --arg sys "$system_prompt" --arg user "$user_message" \
      '[{"role":"system","content":$sys},{"role":"user","content":$user}]')
  else
    messages=$(jq -nc --arg user "$user_message" \
      '[{"role":"user","content":$user}]')
  fi

  local body
  body=$(jq -nc --arg model "$OLLAMA_MODEL" --argjson msgs "$messages" \
    '{"model":$model,"messages":$msgs,"stream":false}')

  local raw
  raw=$(curl -s "$OLLAMA_URL/api/chat" -d "$body") || {
    warn "Ollama call failed — is Ollama running at $OLLAMA_URL?"
    info "Start it:  ollama serve"
    info "Pull model: ollama pull $OLLAMA_MODEL"
    return 1
  }

  # Check for Ollama error responses (e.g. model not found)
  local err
  err=$(echo "$raw" | jq -r '.error // empty' 2>/dev/null)
  if [[ -n "$err" ]]; then
    warn "Ollama error: $err"
    return 1
  fi

  echo "$raw" | jq -r '.message.content // empty'
}

_call_llm_ollama_multi() {
  local system_prompt="$1" messages_json="$2"

  local messages
  if [[ -n "$system_prompt" ]]; then
    messages=$(echo "$messages_json" | jq --arg sys "$system_prompt" \
      '[{"role":"system","content":$sys}] + .')
  else
    messages="$messages_json"
  fi

  local body
  body=$(jq -nc --arg model "$OLLAMA_MODEL" --argjson msgs "$messages" \
    '{"model":$model,"messages":$msgs,"stream":false}')

  local raw
  raw=$(curl -s "$OLLAMA_URL/api/chat" -d "$body") || {
    warn "Ollama call failed"
    return 1
  }

  local err
  err=$(echo "$raw" | jq -r '.error // empty' 2>/dev/null)
  if [[ -n "$err" ]]; then
    warn "Ollama error: $err"
    return 1
  fi

  echo "$raw" | jq -r '.message.content // empty'
}

# --- Bedrock backend --------------------------------------------------------

_call_llm_bedrock() {
  local system_prompt="$1" user_message="$2"

  local messages
  messages=$(jq -nc --arg t "$user_message" \
    '[{"role":"user","content":[{"text":$t}]}]')

  local cmd=(aws bedrock-runtime converse
    --model-id "$BEDROCK_MODEL"
    --region "$BEDROCK_REGION"
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

_call_llm_bedrock_multi() {
  local system_prompt="$1" messages_json="$2"

  # Convert OpenAI-format messages to Bedrock's nested format:
  #   {"role":"user","content":"hello"} → {"role":"user","content":[{"text":"hello"}]}
  local bedrock_messages
  bedrock_messages=$(echo "$messages_json" | jq \
    '[.[] | {"role":.role,"content":[{"text":.content}]}]')

  local cmd=(aws bedrock-runtime converse
    --model-id "$BEDROCK_MODEL"
    --region "$BEDROCK_REGION"
    --messages "$bedrock_messages"
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

# --- Dispatch layer ---------------------------------------------------------

call_llm() {
  if [[ "$PROVIDER" == "ollama" ]]; then
    _call_llm_ollama "$@"
  else
    _call_llm_bedrock "$@"
  fi
}

call_llm_multi() {
  if [[ "$PROVIDER" == "ollama" ]]; then
    _call_llm_ollama_multi "$@"
  else
    _call_llm_bedrock_multi "$@"
  fi
}

# --- Conversation helpers (OpenAI-compatible format) ------------------------
# Both providers accept this format. Bedrock converts internally.

new_turn() {
  local role="$1" text="$2"
  jq -nc --arg r "$role" --arg t "$text" \
    '[{"role":$r,"content":$t}]'
}

append_turn() {
  local history="$1" role="$2" text="$3"
  echo "$history" | jq --arg r "$role" --arg t "$text" \
    '. + [{"role":$r,"content":$t}]'
}

# --- Provider readiness check -----------------------------------------------

check_provider() {
  if ! command -v jq &>/dev/null; then
    warn "jq not found — skipping this step"
    info "Install: sudo apt install jq  OR  brew install jq"
    return 1
  fi
  if [[ "$PROVIDER" == "ollama" ]]; then
    if ! curl -sf "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
      warn "Ollama not reachable at $OLLAMA_URL — skipping this step"
      info "Start it: ollama serve && ollama pull $OLLAMA_MODEL"
      return 1
    fi
  else
    if ! command -v aws &>/dev/null; then
      warn "aws CLI not found — skipping this step"
      info "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
      return 1
    fi
  fi
  return 0
}

# --- Nugget assembly --------------------------------------------------------

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
  local expect_1="${2:-true}"
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
  info "Provider: $PROVIDER ($DISPLAY_MODEL)"
  echo ""

  check_provider || return 0

  step "Calling $DISPLAY_MODEL with NO system prompt..."
  echo ""

  local response
  response=$(call_llm "" "$NUGGET_TEST_PROMPT") || {
    warn "LLM call failed — skipping rest of step 1"
    return 0
  }

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
  info "Provider: $PROVIDER ($DISPLAY_MODEL)"
  echo ""

  check_provider || return 0

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
    response=$(call_llm "$skill" "$NUGGET_TEST_PROMPT") || {
      warn "LLM call failed with $n_nuggets nugget(s) — skipping"
      continue
    }

    echo -e "${DIM}  --- Response (first 300 chars) ---${RESET}"
    echo -e "${DIM}  ${response:0:300}${RESET}"
    echo ""

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
  info "Provider: $SMOKE_PROVIDER"
  echo ""

  if ! command -v npx &>/dev/null; then
    warn "npx not found — skipping step 3"
    info "Install Node.js 18+: https://nodejs.org/"
    return 0
  fi

  local config="$SCRIPT_DIR/promptfooconfig-inline.yaml"
  step "Running: npx promptfoo eval --config $config"
  echo ""

  # SMOKE_PROVIDER is already exported for the YAML to pick up
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
  info "Provider: $SMOKE_PROVIDER"
  echo ""

  if ! command -v npx &>/dev/null; then
    warn "npx not found — skipping step 4"
    return 0
  fi

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

  check_provider || return 0

  info "Using Solr: $SOLR_URL"
  info "Provider: $PROVIDER ($DISPLAY_MODEL)"
  echo ""

  local skill
  skill=$(assemble_nuggets 3)

  # -----------------------------------------------------------------------
  # 5a. YOLO mode
  # -----------------------------------------------------------------------
  step "5a. YOLO mode — fetch live schema, generate spec in one shot"
  echo ""

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
  yolo_response=$(call_llm "$skill" "$yolo_prompt") || {
    warn "LLM call failed — skipping rest of step 5"
    return 0
  }

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

  # Use only nuggets 2+3 (domain knowledge) for interactive mode.
  # Nugget 1 (express mode) is deliberately excluded — it teaches the model
  # to respond in YOLO mode, which conflicts with the interactive test's goal
  # of proving the advisor asks clarifying questions first.
  local interactive_skill
  interactive_skill="You are a Solr-to-OpenSearch migration advisor.
When the user has NOT said \"YOLO\", \"express mode\", or \"just do it\",
ask clarifying questions before generating a migration plan.
$(cat "$NUGGETS_DIR/nugget-02-bm25.txt")
$(cat "$NUGGETS_DIR/nugget-03-translations.txt")"

  # Turn 1: vague migration request — no YOLO trigger
  local turn1_user="I need to migrate my Solr setup to OpenSearch. Where do I start?"
  detail "Turn 1 →  $turn1_user"

  local turns
  turns=$(new_turn "user" "$turn1_user")
  local turn1_resp
  turn1_resp=$(call_llm_multi "$interactive_skill" "$turns") || {
    warn "LLM call failed — skipping interactive test"
    return 0
  }

  echo ""
  echo -e "${DIM}  --- Turn 1 Response ---${RESET}"
  echo "$turn1_resp" | head -10 | while IFS= read -r line; do echo -e "${DIM}  $line${RESET}"; done
  echo ""

  assert_contains \
    "Interactive Turn 1: advisor asks at least one clarifying question" \
    "?" "$turn1_resp"

  # Turn 2: provide context
  local turn2_user="We have a SolrCloud cluster with 2 collections, using SolrJ in a Spring Boot app. Index is about 500GB, ~200 QPS peak. We want to move to OpenSearch."
  detail "Turn 2 →  $turn2_user"

  turns=$(append_turn "$turns" "assistant" "$turn1_resp")
  turns=$(append_turn "$turns" "user" "$turn2_user")
  local turn2_resp
  turn2_resp=$(call_llm_multi "$interactive_skill" "$turns") || {
    warn "LLM call failed — skipping turn 2"
    return 0
  }

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
should_run() {
  local s="$1"
  for r in "${STEPS_TO_RUN[@]}"; do [[ "$r" == "$s" ]] && return 0; done
  return 1
}

echo -e "${BOLD}Skill Smoke Test${RESET}"
echo -e "  Steps:  ${STEPS_TO_RUN[*]}"
echo ""

# ---------------------------------------------------------------------------
# Pre-flight: check minimum tools
# ---------------------------------------------------------------------------
PREFLIGHT_OK=true
MISSING_ITEMS=()

if ! command -v jq &>/dev/null; then
  warn "MISSING: jq (required for all steps)"
  info "  Install: sudo apt install jq  OR  brew install jq"
  MISSING_ITEMS+=("jq")
  PREFLIGHT_OK=false
fi

if ! command -v curl &>/dev/null; then
  warn "MISSING: curl (required for Ollama calls and step 5)"
  MISSING_ITEMS+=("curl")
  PREFLIGHT_OK=false
fi

# Bedrock-specific
NEED_AWS=false
for s in "${STEPS_TO_RUN[@]}"; do
  [[ "$s" == "1" || "$s" == "2" || "$s" == "5" ]] && NEED_AWS=true
done
if [[ "$PROVIDER" == "bedrock" && "$NEED_AWS" == true ]] && ! command -v aws &>/dev/null; then
  warn "MISSING: aws CLI v2 (required for Bedrock provider, steps 1, 2, 5)"
  info "  Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
  info "  Or switch to Ollama: ollama serve && ./run_smoke.sh --provider ollama"
  MISSING_ITEMS+=("aws-cli")
  PREFLIGHT_OK=false
fi

# Node.js for promptfoo steps
NEED_NPX=false
for s in "${STEPS_TO_RUN[@]}"; do
  [[ "$s" == "3" || "$s" == "4" ]] && NEED_NPX=true
done
if [[ "$NEED_NPX" == true ]] && ! command -v npx &>/dev/null; then
  warn "MISSING: npx / Node.js 18+ (required for steps 3, 4)"
  info "  Install: https://nodejs.org/ or: nvm install 18"
  MISSING_ITEMS+=("npx/node")
  PREFLIGHT_OK=false
fi

# Ollama model check — verify the model is actually pulled
if [[ "$PROVIDER" == "ollama" ]]; then
  local_models=$(curl -sf "$OLLAMA_URL/api/tags" 2>/dev/null | jq -r '.models[].name' 2>/dev/null)
  if ! echo "$local_models" | grep -qxF "$OLLAMA_MODEL" 2>/dev/null; then
    warn "MISSING: Ollama model '${OLLAMA_MODEL}' is not pulled"
    info "  Pull it:  ollama pull ${OLLAMA_MODEL}"
    echo ""
    info "  Models you DO have:"
    echo "$local_models" | grep -ivE 'embed|nomic|snowflake|mxbai' | head -8 | while IFS= read -r m; do
      info "    $m"
    done
    info "  Override:  OLLAMA_MODEL=<name> ./run_smoke.sh"
    MISSING_ITEMS+=("model:${OLLAMA_MODEL}")
    PREFLIGHT_OK=false
  else
    info "Ollama model verified: ${OLLAMA_MODEL}"
  fi
fi

if [[ "$PREFLIGHT_OK" == false ]]; then
  echo ""
  warn "Missing: ${MISSING_ITEMS[*]}"
  warn "Steps that need these will be skipped. Install them and re-run."
  info "See README.md → Prerequisites for install instructions."
fi
echo ""

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
