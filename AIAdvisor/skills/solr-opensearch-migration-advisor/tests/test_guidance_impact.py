"""
Guidance impact tests: prove that steering content measurably improves
advisor output from an LLM.

Each test sends the same migration scenario to an LLM twice:
  1. WITHOUT steering content → assert the response LACKS specific terms
  2. WITH steering content    → assert the response CONTAINS those terms

This demonstrates that the prose guidance we maintain in steering/ is not
decorative — it changes what the model says in ways we can verify with
simple keyword assertions.

Backend selection (--llm-backend):
  ollama   — Use Ollama (FAIL if unavailable)
  bedrock  — Use AWS Bedrock (FAIL if no credentials/access)
  auto     — Try Bedrock, then Ollama, SKIP if neither works

Additional options:
  --ollama-base-url   (default: http://localhost:11434)
  --ollama-model      (default: llama3.2:latest)
  --bedrock-model-id  (default: anthropic.claude-3-haiku-20240307-v1:0)
  --bedrock-region    (default: AWS_DEFAULT_REGION or us-east-1)

Run:
  pytest tests/test_guidance_impact.py -v
  pytest tests/test_guidance_impact.py -v --llm-backend=ollama
  pytest tests/test_guidance_impact.py -v --llm-backend=bedrock

Artifacts:
  Each run writes artifacts to a timestamped session directory
  under tests/artifacts/<timestamp>/ (symlinked as tests/artifacts/latest/).
  Includes pytest junit XML, LLM response report, and run metadata.

  The guidance-impact-report.md is the primary human-readable artifact.
  It includes per-test pass/fail detail, a concept-by-concept scorecard
  showing which phrase variant matched, and LLM-generated diagnosis for
  any missed concepts.

Model size and guidance impact
------------------------------
Smaller models show a more dramatic delta because they have less
built-in knowledge to fall back on:

  llama3.2 (3B)   Bare: ~1/4 concepts  →  Guided: 3-4/4   (~8s)
  qwen3 (14B)     Bare: ~3/4 concepts  →  Guided: 4/4     (~144s)

The 3B model is the default because it runs fast and makes the
guidance impact visually obvious.  Larger models are useful for
one-off comparisons but too slow for routine CI.

To compare models manually::

  pytest tests/test_guidance_impact.py -v -s --ollama-model=llama3.2:latest
  pytest tests/test_guidance_impact.py -v -s --ollama-model=qwen3:14b
"""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path

import pytest

STEERING_DIR = Path(__file__).resolve().parents[1] / "steering"
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))

# ── LLM backend abstraction ─────────────────────────────────────────────


class OllamaBackend:
    """Generate text via a local Ollama instance."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
        self.name = f"ollama ({model})"

    def generate(self, prompt: str, *, system: str = "") -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 500},
        }
        if system:
            payload["system"] = system

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            return json.loads(resp.read())["response"]


class BedrockBackend:
    """Generate text via AWS Bedrock Converse API."""

    def __init__(self, model_id: str, region: str):
        import boto3
        self.model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.name = f"bedrock ({model_id})"

    def generate(self, prompt: str, *, system: str = "") -> str:
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        kwargs = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": {
                "temperature": 0.3,
                "maxTokens": 500,
            },
        }
        if system:
            kwargs["system"] = [{"text": system}]

        response = self.client.converse(**kwargs)
        return response["output"]["message"]["content"][0]["text"]


def _ollama_available(base_url: str) -> bool:
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5):
            return True
    except (urllib.error.URLError, OSError):
        return False


def _bedrock_available(model_id: str, region: str) -> bool:
    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name=region)
        # Minimal Converse call to verify credentials + model access.
        client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": "Say OK"}]}],
            inferenceConfig={"maxTokens": 5},
        )
        return True
    except ImportError:
        return False
    except Exception:
        return False


# ── helpers ──────────────────────────────────────────────────────────────


def _load_steering(*filenames: str) -> str:
    parts = []
    for name in filenames:
        path = STEERING_DIR / name
        parts.append(path.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def _count_concept_hits(text: str, concepts: dict[str, list[str]]) -> dict[str, bool]:
    """Check whether each named concept appears in text.

    A concept is 'hit' if ANY of its variant phrases match
    (case-insensitive).  This handles small-model paraphrasing:
    the model might say "not directly equivalent" instead of
    "no direct equivalent" — both count.
    """
    lower = text.lower()
    return {
        name: any(variant.lower() in lower for variant in variants)
        for name, variants in concepts.items()
    }


def _matched_variant(text: str, variants: list[str]) -> str | None:
    """Return the first variant phrase found in text, or None."""
    lower = text.lower()
    for v in variants:
        if v.lower() in lower:
            return v
    return None


def _diagnose_misses(
    backend,
    concept_name: str,
    variants: list[str],
    steering_line: str,
    guided_response: str,
) -> str:
    """Ask the LLM why it didn't mention a concept, given that the
    steering told it to.  Returns the diagnosis text."""
    prompt = (
        f"You were given this steering guidance:\n\n"
        f"  {steering_line}\n\n"
        f"You were asked about a Solr-to-OpenSearch migration and your "
        f"response did not mention any of these phrases: "
        f"{', '.join(repr(v) for v in variants)}.\n\n"
        f"Your response was:\n\n"
        f"{guided_response}\n\n"
        f"In 2-3 sentences: why might you have omitted this concept? "
        f"What change to the steering content or prompt would make you "
        f"more likely to include it?"
    )
    try:
        return backend.generate(prompt)
    except Exception as exc:
        return f"(diagnosis failed: {exc})"


# ── concept definitions ──────────────────────────────────────────────────

# Each concept has:
#   variants:      acceptable phrases (case-insensitive)
#   steering_file: which file contains the guidance
#   steering_line: the specific line the concept comes from
CONCEPT_DEFINITIONS = {
    "script_score": {
        "variants": ["script_score"],
        "steering_file": "incompatibilities.md",
        "steering_line": (
            "Function Queries: OpenSearch `script_score` is the "
            "replacement, but syntax differs."
        ),
    },
    "rebuild_handlers": {
        "variants": [
            "no direct equivalent",
            "not directly equivalent",
            "no equivalent",
            "must rebuild",
            "must be rebuilt",
            "rebuild using",
            "rebuilt using",
            "need to be rewritten",
            "needs to be rewritten",
            "require significant rework",
        ],
        "steering_file": "incompatibilities.md",
        "steering_line": (
            "Custom Request Handlers: No direct equivalent; must "
            "rebuild using standard Search API + Client-side logic."
        ),
    },
    "nested_mapping": {
        "variants": ["nested"],
        "steering_file": "incompatibilities.md",
        "steering_line": (
            "Nested Docs: Solr `_childDocuments_` maps to `nested` "
            "objects or parent-child joining."
        ),
    },
    "join_replacement": {
        "variants": [
            "terms lookup",
            "terms query",
            "flattened",
            "denormalize",
            "denormaliz",
        ],
        "steering_file": "incompatibilities.md",
        "steering_line": (
            "Joins: Solr `!join` maps to `terms` lookup query or "
            "flattened index design."
        ),
    },
}

# Build the simple {name: [variants]} dict the test assertions use
GUIDED_CONCEPTS = {
    name: defn["variants"] for name, defn in CONCEPT_DEFINITIONS.items()
}

MAX_ATTEMPTS = 5       # retry budget for small-model variance
MIN_GUIDED_CONCEPTS = 3  # require at least this many of the concepts


# ── report writer ────────────────────────────────────────────────────────


def _write_report(
    session_dir: Path,
    backend,
    scenario: str,
    bare_response: str,
    guided_response: str,
    test_details: list[dict],
) -> Path:
    """Write the human-readable guidance impact report.

    This is the primary artifact — designed to be opened by a person
    who wants to understand whether the steering content is working,
    what passed, what failed, and what to do next.
    """
    bare_hits = _count_concept_hits(bare_response, GUIDED_CONCEPTS)
    guided_hits = _count_concept_hits(guided_response, GUIDED_CONCEPTS)
    bare_count = sum(bare_hits.values())
    guided_count = sum(guided_hits.values())
    total = len(GUIDED_CONCEPTS)
    pass_count = sum(1 for t in test_details if t["passed"])
    fail_count = len(test_details) - pass_count

    lines = []

    # ── header ───────────────────────────────────────────────────────
    lines.append("# Guidance Impact Report")
    lines.append("")
    lines.append(
        "| Backend | Session | Bare | Guided | Delta | Tests |"
    )
    lines.append("|---------|---------|------|--------|-------|-------|")
    overall = "\u2705" if fail_count == 0 else "\u274c"
    lines.append(
        f"| {backend.name} | {session_dir.name} | "
        f"{bare_count}/{total} terms | {guided_count}/{total} terms | "
        f"+{guided_count - bare_count} | "
        f"{overall} {pass_count} passed, {fail_count} failed |"
    )
    lines.append("")

    # ── test results table ───────────────────────────────────────────
    lines.append("## Test Results")
    lines.append("")
    lines.append(
        "| # | Test | Result | What it checks | Evidence | Next Step |"
    )
    lines.append(
        "|---|------|--------|----------------|----------|-----------|"
    )
    for i, t in enumerate(test_details, 1):
        icon = "\u2705" if t["passed"] else "\u274c"
        lines.append(
            f"| {i} | {t['name']} | {icon} | {t['description']} | "
            f"{t['evidence']} | {t['next_step']} |"
        )
    lines.append("")

    # ── failed test detail ───────────────────────────────────────────
    failed = [
        (i, t) for i, t in enumerate(test_details, 1) if not t["passed"]
    ]
    if failed:
        lines.append("## \u274c Failed Tests — Detail")
        lines.append("")
        for i, t in failed:
            lines.append(f"### Test #{i}: {t['name']}")
            lines.append("")
            lines.append(f"**Assertion:** `{t['assertion']}`")
            lines.append("")
            lines.append(f"**Evidence:** {t['evidence']}")
            lines.append("")
            lines.append(f"**Why it failed:** {t['why']}")
            lines.append("")
            lines.append(f"**Next step:** {t['next_step']}")
            lines.append("")

    # ── term scorecard ───────────────────────────────────────────────
    lines.append("## Expected Term Scorecard")
    lines.append("")
    lines.append(
        "Each row is a technical term the steering content should "
        "cause the model to produce."
    )
    lines.append("")
    lines.append(
        "| Term | Bare | Guided | Matched Phrase | "
        "Source | Next Step |"
    )
    lines.append(
        "|------|------|--------|----------------|"
        "--------|-----------|"
    )

    missed_concepts = []
    for name, defn in CONCEPT_DEFINITIONS.items():
        bare_match = _matched_variant(bare_response, defn["variants"])
        guided_match = _matched_variant(guided_response, defn["variants"])
        bare_status = (
            f"\u2705 `{bare_match}`" if bare_match else "\u2796 miss"
        )
        guided_status = (
            f"\u2705 `{guided_match}`" if guided_match
            else "\u274c **miss**"
        )
        if guided_match and not bare_match:
            next_step = (
                "\u2705 Guidance is adding this term. No action needed."
            )
        elif guided_match and bare_match:
            next_step = (
                "\u2699\ufe0f Model already knows this. Consider a "
                "harder variant."
            )
        else:
            next_step = (
                "\u274c See Diagnosis below for LLM analysis."
            )
            missed_concepts.append(name)

        lines.append(
            f"| {name} | {bare_status} | {guided_status} | "
            f"`{guided_match or '—'}` | "
            f"`{defn['steering_file']}` | {next_step} |"
        )

    lines.append("")

    # ── failure diagnosis (LLM self-analysis) ────────────────────────
    if missed_concepts:
        lines.append("## Diagnosis: Missed Terms")
        lines.append("")
        lines.append(
            "For each expected term the guided model missed, the LLM "
            "was asked: *\"Why didn't you mention this, and what change "
            "to the steering would fix it?\"*"
        )
        lines.append("")

        for name in missed_concepts:
            defn = CONCEPT_DEFINITIONS[name]
            lines.append(f"### {name}")
            lines.append("")
            lines.append(
                f"**Steering says:** {defn['steering_line']}"
            )
            lines.append("")
            lines.append(
                f"**Looked for:** "
                f"{', '.join(f'`{v}`' for v in defn['variants'])}"
            )
            lines.append("")
            diagnosis = _diagnose_misses(
                backend,
                name,
                defn["variants"],
                defn["steering_line"],
                guided_response,
            )
            lines.append("**LLM self-diagnosis:**")
            lines.append("")
            # Indent each line of diagnosis as a blockquote
            for diag_line in diagnosis.split("\n"):
                lines.append(f"> {diag_line}")
            lines.append("")
            lines.append(
                f"**Suggested next step:** Strengthen the `{name}` "
                f"section in `{defn['steering_file']}` based on the "
                f"diagnosis above, then re-run this test."
            )
            lines.append("")

    # ── scenario ─────────────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("## Appendix A: Scenario")
    lines.append("")
    lines.append(f"> {scenario}")
    lines.append("")

    # ── full responses ───────────────────────────────────────────────
    lines.append("## Appendix B: Bare Response (no steering)")
    lines.append("")
    lines.append(bare_response)
    lines.append("")

    lines.append("## Appendix C: Guided Response (with steering)")
    lines.append("")
    lines.append(guided_response)
    lines.append("")

    path = session_dir / "guidance-impact-report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ── fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def llm_backend(request):
    """Resolve the LLM backend based on --llm-backend flag.

    Priority:
      ollama  → must work, fail if not
      bedrock → must work, fail if not
      auto    → try bedrock, then ollama, skip if neither
    """
    choice = request.config.getoption("--llm-backend")

    ollama_url = (
        request.config.getoption("--ollama-base-url")
        or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    ollama_model = (
        request.config.getoption("--ollama-model")
        or os.environ.get("OLLAMA_MODEL", "llama3.2:latest")
    )
    bedrock_model = (
        request.config.getoption("--bedrock-model-id")
        or os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    )
    bedrock_region = (
        request.config.getoption("--bedrock-region")
        or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    )

    if choice == "ollama":
        if not _ollama_available(ollama_url):
            pytest.fail(
                f"--llm-backend=ollama but Ollama is not available at {ollama_url}"
            )
        return OllamaBackend(ollama_url, ollama_model)

    if choice == "bedrock":
        if not _bedrock_available(bedrock_model, bedrock_region):
            pytest.fail(
                f"--llm-backend=bedrock but Bedrock is not available "
                f"(model={bedrock_model}, region={bedrock_region}). "
                f"Check AWS credentials and model access."
            )
        return BedrockBackend(bedrock_model, bedrock_region)

    # auto: try bedrock first, then ollama, skip if neither
    if _bedrock_available(bedrock_model, bedrock_region):
        return BedrockBackend(bedrock_model, bedrock_region)
    if _ollama_available(ollama_url):
        return OllamaBackend(ollama_url, ollama_model)

    pytest.skip("No LLM backend available (tried Bedrock, then Ollama)")


# ── scenario ─────────────────────────────────────────────────────────────

SCENARIO_INCOMPATIBILITIES = (
    "A client is migrating from Solr to OpenSearch. They have function "
    "queries for custom scoring, filter queries (fq) for faceted navigation, "
    "custom request handlers with business logic, Solr join queries between "
    "collections, and nested child documents. They say: 'It's all Lucene "
    "underneath, so most of it ports directly.' Respond as a migration "
    "consultant in 2-3 paragraphs."
)


# ── tests ────────────────────────────────────────────────────────────────


class TestIncompatibilitySteering:
    """Prove that steering/incompatibilities.md + query_translation.md
    change model output in measurable ways."""

    @pytest.fixture(scope="class")
    def bare_response(self, llm_backend):
        """Run the bare model up to MAX_ATTEMPTS times, return the
        response with the MOST concept hits.

        We give the bare model every chance to succeed so the
        comparison test is conservative: if guided still wins against
        bare's best effort, the signal is strong.
        """
        best_response = ""
        best_hits = -1
        for attempt in range(MAX_ATTEMPTS):
            response = llm_backend.generate(SCENARIO_INCOMPATIBILITIES)
            hits = _count_concept_hits(response, GUIDED_CONCEPTS)
            hit_count = sum(hits.values())
            if hit_count > best_hits:
                best_response = response
                best_hits = hit_count
            if hit_count == len(GUIDED_CONCEPTS):
                break  # bare already knows everything — stop early
        return best_response

    @pytest.fixture(scope="class")
    def guided_response(self, llm_backend):
        """Run the guided model up to MAX_ATTEMPTS times, return the
        best response.

        A small model sometimes paraphrases away from expected terms on
        any single run.  Retrying is cheap and reflects real usage — the
        guidance is valuable if it produces the right terms *reliably*,
        not necessarily on every single token sequence.
        """
        steering = _load_steering(
            "accuracy.md",
            "incompatibilities.md",
            "query_translation.md",
        )
        system = (
            "You are a Solr-to-OpenSearch migration consultant. "
            "Follow the guidance below strictly.\n\n" + steering
        )
        best_response = ""
        best_hits = -1
        for attempt in range(MAX_ATTEMPTS):
            response = llm_backend.generate(
                SCENARIO_INCOMPATIBILITIES, system=system
            )
            hits = _count_concept_hits(response, GUIDED_CONCEPTS)
            hit_count = sum(hits.values())
            if hit_count > best_hits:
                best_response = response
                best_hits = hit_count
            if hit_count == len(GUIDED_CONCEPTS):
                break
        return best_response

    def test_bare_lacks_guided_terms(self, llm_backend, bare_response):
        """Without steering, the model should miss at least one of our
        expected terms — confirming these aren't 'obvious' baseline
        knowledge."""
        hits = _count_concept_hits(bare_response, GUIDED_CONCEPTS)
        found = [k for k, v in hits.items() if v]
        missed = [k for k, v in hits.items() if not v]

        print(f"\n--- BARE response [{llm_backend.name}] ---\n{bare_response}")
        print(f"\nTerms found: {found}")
        print(f"Terms missed: {missed}")

        assert missed, (
            f"Bare model already produces all expected terms "
            f"{list(GUIDED_CONCEPTS)} — guidance impact cannot be "
            f"demonstrated with this scenario."
        )

    def test_guided_hits_most_terms(self, llm_backend, guided_response):
        """With steering loaded, the model should produce at least
        MIN_GUIDED_CONCEPTS of the expected terms.

        We require a supermajority rather than 100% because a small
        model may not surface every term on every run, even with
        retries.  The comparison test (guided > bare) is the stronger
        signal; this test gates a minimum quality bar.
        """
        hits = _count_concept_hits(guided_response, GUIDED_CONCEPTS)
        found = [k for k, v in hits.items() if v]
        missed = [k for k, v in hits.items() if not v]

        print(f"\n--- GUIDED response [{llm_backend.name}] ---")
        print(f"{guided_response}")
        print(f"\nTerms found ({len(found)}/{len(GUIDED_CONCEPTS)}): {found}")
        print(f"Terms missed: {missed}")

        assert len(found) >= MIN_GUIDED_CONCEPTS, (
            f"Guided model hit only {len(found)}/{len(GUIDED_CONCEPTS)} "
            f"terms (minimum {MIN_GUIDED_CONCEPTS}). "
            f"Missing: {missed}. Steering content may need "
            f"strengthening or model may be too small."
        )

    def test_guidance_improves_term_coverage(
        self, request, llm_backend, bare_response, guided_response
    ):
        """The guided response should hit MORE of our expected concepts
        than the bare response.

        Also writes the guidance impact report — the primary
        human-readable artifact for this test suite.
        """
        bare_hits = _count_concept_hits(bare_response, GUIDED_CONCEPTS)
        guided_hits = _count_concept_hits(guided_response, GUIDED_CONCEPTS)
        bare_count = sum(bare_hits.values())
        guided_count = sum(guided_hits.values())

        print(f"\n[{llm_backend.name}]")
        print(f"Bare:   {bare_count}/{len(GUIDED_CONCEPTS)} — {bare_hits}")
        print(f"Guided: {guided_count}/{len(GUIDED_CONCEPTS)} — {guided_hits}")

        # Build detailed test results for the report
        bare_missed = [k for k, v in bare_hits.items() if not v]
        guided_found = [k for k, v in guided_hits.items() if v]
        guided_missed = [k for k, v in guided_hits.items() if not v]

        test_details = [
            {
                "name": "bare_lacks_guided_terms",
                "description": (
                    "Bare model misses at least one expected term, "
                    "proving guidance adds knowledge"
                ),
                "assertion": "bare misses >= 1 term",
                "evidence": (
                    f"Bare missed {len(bare_missed)}/{len(GUIDED_CONCEPTS)}: "
                    f"{bare_missed or 'none'}"
                ),
                "passed": len(bare_missed) > 0,
                "why": (
                    "The bare model already produced all expected "
                    "terms — the scenario is too easy or the terms "
                    "are common in training data."
                    if not bare_missed else ""
                ),
                "next_step": (
                    "No action — guidance is adding value the bare "
                    "model lacks."
                    if bare_missed else
                    "Choose more specific or opinionated terms "
                    "that a bare model wouldn't know."
                ),
            },
            {
                "name": "guided_hits_most_terms",
                "description": (
                    f"Guided model produces >= {MIN_GUIDED_CONCEPTS}/"
                    f"{len(GUIDED_CONCEPTS)} expected terms"
                ),
                "assertion": (
                    f"guided hits >= {MIN_GUIDED_CONCEPTS} terms"
                ),
                "evidence": (
                    f"Hit {len(guided_found)}/{len(GUIDED_CONCEPTS)}: "
                    f"{guided_found}"
                    + (f" | missed: {guided_missed}" if guided_missed else "")
                ),
                "passed": len(guided_found) >= MIN_GUIDED_CONCEPTS,
                "why": (
                    f"Only hit {len(guided_found)} terms. The "
                    f"model may need stronger steering for: "
                    f"{guided_missed}."
                    if len(guided_found) < MIN_GUIDED_CONCEPTS else ""
                ),
                "next_step": (
                    "Steering is effective. Review scorecard for "
                    "per-term detail."
                    if len(guided_found) >= MIN_GUIDED_CONCEPTS else
                    "See Diagnosis section for LLM-suggested "
                    "steering improvements."
                ),
            },
            {
                "name": "guidance_improves_term_coverage",
                "description": (
                    "Guided response produces more expected terms "
                    "than bare"
                ),
                "assertion": "guided_count > bare_count",
                "evidence": (
                    f"Guided: {guided_count}, Bare: {bare_count}, "
                    f"Delta: +{guided_count - bare_count}"
                ),
                "passed": guided_count > bare_count,
                "why": (
                    f"Guided ({guided_count}) did not exceed bare "
                    f"({bare_count}). Steering may not add value for "
                    f"this scenario, or the bare model got lucky."
                    if guided_count <= bare_count else ""
                ),
                "next_step": (
                    "Guidance adds measurable value. Ready for "
                    "PR/review."
                    if guided_count > bare_count else
                    "Review steering content or try a different "
                    "scenario where bare model has less prior "
                    "knowledge."
                ),
            },
        ]

        session_dir = request.config._artifact_session_dir
        path = _write_report(
            session_dir=session_dir,
            backend=llm_backend,
            scenario=SCENARIO_INCOMPATIBILITIES,
            bare_response=bare_response,
            guided_response=guided_response,
            test_details=test_details,
        )
        print(f"\nReport: {path}")

        assert guided_count > bare_count, (
            f"Guided response ({guided_count} concepts) should cover "
            f"more than bare ({bare_count} concepts)"
        )
