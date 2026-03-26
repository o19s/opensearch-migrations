#!/usr/bin/env bash
# =============================================================================
# Test Helpers — assertion functions and report generation
#
# Source this file from test scripts:
#   source "$(dirname "${BASH_SOURCE[0]}")/test_helpers.sh"
#
# After running assertions, call:
#   write_reports "$OUTPUT_DIR"   # writes JUnit XML + plain text (if OUTPUT_DIR set)
#   print_summary                 # prints colorized summary to stdout
# =============================================================================

# --- Colors & formatting ----------------------------------------------------
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
DIM='\033[2m'
RESET='\033[0m'

banner()  { echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════════════════${RESET}"; echo -e "${BOLD}${CYAN}  $1${RESET}"; echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${RESET}\n"; }
step()    { echo -e "${BOLD}${GREEN}▶ $1${RESET}"; }
info()    { echo -e "${DIM}  $1${RESET}"; }
warn()    { echo -e "${YELLOW}⚠ $1${RESET}"; }
detail()  { echo -e "  ${CYAN}→${RESET} $1"; }

# --- State -------------------------------------------------------------------
PASS_COUNT=0
FAIL_COUNT=0

# Parallel arrays to collect results for reports
declare -a TEST_NAMES=()
declare -a TEST_STATUSES=()   # "pass" or "fail"
declare -a TEST_MESSAGES=()   # failure detail (empty for passes)
declare -a TEST_GROUPS=()     # current group name
_CURRENT_GROUP="ungrouped"

# Start a named test group (used for JUnit testsuite name)
test_group() {
  _CURRENT_GROUP="$1"
}

# --- Assertion functions -----------------------------------------------------
_record() {
  local name="$1" status="$2" message="${3:-}"
  TEST_NAMES+=("$name")
  TEST_STATUSES+=("$status")
  TEST_MESSAGES+=("$message")
  TEST_GROUPS+=("$_CURRENT_GROUP")
}

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo -e "  ${GREEN}✓ PASS${RESET}  $desc"
    PASS_COUNT=$((PASS_COUNT + 1))
    _record "$desc" "pass"
  else
    echo -e "  ${RED}✗ FAIL${RESET}  $desc"
    echo -e "         expected: ${BOLD}$expected${RESET}"
    echo -e "         actual:   ${BOLD}$actual${RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    _record "$desc" "fail" "expected [$expected] but got [$actual]"
  fi
}

assert_contains() {
  local desc="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -qi "$needle"; then
    echo -e "  ${GREEN}✓ PASS${RESET}  $desc"
    PASS_COUNT=$((PASS_COUNT + 1))
    _record "$desc" "pass"
  else
    echo -e "  ${RED}✗ FAIL${RESET}  $desc"
    echo -e "         expected to contain: ${BOLD}$needle${RESET}"
    echo -e "         response (first 200 chars): ${DIM}${haystack:0:200}${RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    _record "$desc" "fail" "expected to contain [$needle] in [${haystack:0:200}]"
  fi
}

assert_http_ok() {
  local desc="$1" url="$2"
  local status
  status=$(curl -sf -o /dev/null -w "%{http_code}" "$url" 2>/dev/null) || status="000"
  if [ "$status" = "200" ]; then
    echo -e "  ${GREEN}✓ PASS${RESET}  $desc"
    PASS_COUNT=$((PASS_COUNT + 1))
    _record "$desc" "pass"
  else
    echo -e "  ${RED}✗ FAIL${RESET}  $desc"
    echo -e "         expected HTTP 200, got: ${BOLD}$status${RESET}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    _record "$desc" "fail" "expected HTTP 200, got $status"
  fi
}

# --- Utility -----------------------------------------------------------------
wait_for() {
  local name="$1" url="$2" max_wait="${3:-120}"
  info "Waiting for $name at $url ..."
  local elapsed=0
  while ! curl -sf "$url" >/dev/null 2>&1; do
    sleep 2; elapsed=$((elapsed + 2))
    if [ "$elapsed" -ge "$max_wait" ]; then
      echo -e "${RED}✗ $name did not become healthy after ${max_wait}s${RESET}"; exit 1
    fi
  done
  info "$name is ready (${elapsed}s)"
}

# --- Report generation -------------------------------------------------------

# Escape XML special characters
_xml_escape() {
  local s="$1"
  s="${s//&/&amp;}"
  s="${s//</&lt;}"
  s="${s//>/&gt;}"
  s="${s//\"/&quot;}"
  s="${s//\'/&apos;}"
  echo "$s"
}

# Write JUnit XML report
_write_junit_xml() {
  local outfile="$1"
  local total=$((PASS_COUNT + FAIL_COUNT))
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  {
    echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo "<testsuites tests=\"$total\" failures=\"$FAIL_COUNT\" time=\"0\">"

    # Group test cases by their group
    local prev_group=""
    local group_tests=0 group_failures=0
    local i

    # Collect unique groups in order
    declare -A seen_groups
    declare -a ordered_groups=()
    for i in "${!TEST_GROUPS[@]}"; do
      local g="${TEST_GROUPS[$i]}"
      if [[ -z "${seen_groups[$g]:-}" ]]; then
        seen_groups["$g"]=1
        ordered_groups+=("$g")
      fi
    done

    for group in "${ordered_groups[@]}"; do
      # Count tests and failures in this group
      group_tests=0
      group_failures=0
      for i in "${!TEST_GROUPS[@]}"; do
        if [[ "${TEST_GROUPS[$i]}" == "$group" ]]; then
          group_tests=$((group_tests + 1))
          if [[ "${TEST_STATUSES[$i]}" == "fail" ]]; then
            group_failures=$((group_failures + 1))
          fi
        fi
      done

      echo "  <testsuite name=\"$(_xml_escape "$group")\" tests=\"$group_tests\" failures=\"$group_failures\" timestamp=\"$timestamp\">"

      for i in "${!TEST_GROUPS[@]}"; do
        if [[ "${TEST_GROUPS[$i]}" == "$group" ]]; then
          local name
          name=$(_xml_escape "${TEST_NAMES[$i]}")
          echo "    <testcase name=\"$name\" classname=\"$(_xml_escape "$group")\">"
          if [[ "${TEST_STATUSES[$i]}" == "fail" ]]; then
            local msg
            msg=$(_xml_escape "${TEST_MESSAGES[$i]}")
            echo "      <failure message=\"$msg\">$msg</failure>"
          fi
          echo "    </testcase>"
        fi
      done

      echo "  </testsuite>"
    done

    echo "</testsuites>"
  } > "$outfile"
}

# Write plain text report
_write_text_report() {
  local outfile="$1"
  local total=$((PASS_COUNT + FAIL_COUNT))
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  {
    echo "Connected Smoke Test Report"
    echo "Generated: $timestamp"
    echo "========================================"
    echo ""
    echo "Result: ${PASS_COUNT} passed, ${FAIL_COUNT} failed, ${total} total"
    echo ""

    local current_group=""
    for i in "${!TEST_NAMES[@]}"; do
      if [[ "${TEST_GROUPS[$i]}" != "$current_group" ]]; then
        current_group="${TEST_GROUPS[$i]}"
        echo "--- $current_group ---"
      fi
      if [[ "${TEST_STATUSES[$i]}" == "pass" ]]; then
        echo "  PASS  ${TEST_NAMES[$i]}"
      else
        echo "  FAIL  ${TEST_NAMES[$i]}"
        echo "        ${TEST_MESSAGES[$i]}"
      fi
    done

    echo ""
    echo "========================================"
    if [ "$FAIL_COUNT" -eq 0 ]; then
      echo "All assertions passed."
    else
      echo "${FAIL_COUNT} assertion(s) FAILED."
    fi
  } > "$outfile"
}

# Write both reports to the given directory (creates it if needed)
write_reports() {
  local outdir="$1"
  if [ -z "$outdir" ]; then
    return
  fi
  mkdir -p "$outdir"

  local timestamp
  timestamp=$(date +"%Y%m%d-%H%M%S")

  local xml_file="$outdir/results-${timestamp}.xml"
  local txt_file="$outdir/results-${timestamp}.txt"

  _write_junit_xml "$xml_file"
  _write_text_report "$txt_file"

  echo ""
  info "Reports written:"
  detail "$xml_file"
  detail "$txt_file"
}

# Print colorized summary to stdout
print_summary() {
  local total=$((PASS_COUNT + FAIL_COUNT))
  echo -e "  ${BOLD}Passed: ${GREEN}${PASS_COUNT}${RESET}${BOLD} / ${total}${RESET}"

  if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "  ${BOLD}Failed: ${RED}${FAIL_COUNT}${RESET}"
  else
    echo -e "  ${GREEN}All assertions passed.${RESET}"
  fi
}
