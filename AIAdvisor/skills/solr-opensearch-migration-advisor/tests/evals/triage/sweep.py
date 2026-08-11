#!/usr/bin/env python3
"""
Bare-model triage sweep for stumper candidates.

For each question in stumper-candidates.md, run it bare against:
  - Anthropic Claude Haiku 4.5 (via `claude --print`, cwd=/tmp for isolation)
  - Local Ollama qwen2.5:7b (via HTTP API)

Apply each question's two contains-any criteria. Emit:
  - responses/<qid>.<model>.txt   raw response per question/model (latest)
  - cache/<sha256>.json           addressable cache by hash(model + prompt)
  - triage-results.md             markdown table (qid x model x A/B pass)

Caching: results are cached by sha256(model_id + "\n" + prompt). Edit a
prompt and the hash changes -> cache miss -> fresh call. Errors are
never cached; criteria are re-evaluated from cached responses every run
so you can iterate on assertions for free.

Flags:
  --refresh             ignore cache for all models
  --refresh-model NAME  ignore cache for one model (haiku|qwen)
  <qid> [<qid> ...]     only run these question ids

Exit 0 always; this is a data-collection run, not a pass/fail gate.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESP_DIR = ROOT / "responses"
RESP_DIR.mkdir(exist_ok=True)
CACHE_DIR = ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)
RESULTS_MD = ROOT / "triage-results.md"

HAIKU_MODEL = "claude-haiku-4-5-20251001"
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Each question: id, short title, prompt, two criteria (a, b).
# Each criterion: ("any", [substrings])  -> case-insensitive substring match.
# Sourced verbatim from tests/evals/stumper-candidates.md.
STUMPERS = [
    {
        "id": "q01-querqy-class",
        "title": "Querqy OpenSearch class names",
        "prompt": "What is the exact fully-qualified Java class name for registering a CommonRules rewriter in the OpenSearch Querqy plugin REST API? Give just the class string.",
        "a": ("any", ["CommonRulesRewriterFactory"]),
        "b": ("any", ["querqy.opensearch.rewriter"]),
    },
    {
        "id": "q02-querqy-infologging",
        "title": "Querqy infoLogging field names",
        "prompt": "In the OpenSearch Querqy plugin, what is the exact JSON field name you add inside a querqy query clause to enable debug logging of which rules fired? And what is the exact field name in the response that contains the decoration/rule-match data? Give just the two field names.",
        "a": ("any", ["info_logging", "infoLogging"]),
        "b": ("any", ["querqy_decorations", "decorations"]),
    },
    {
        "id": "q03-querqy-chain-order",
        "title": "Querqy rewriter chain order mechanism",
        "prompt": "In Solr, Querqy rewriter chain order is defined in querqy.xml. In the OpenSearch Querqy plugin, where is the chain order defined? Is it in a config file, the cluster state, or per-query? Give the exact mechanism.",
        "a": ("any", ["per-query", "per query", "query time", "in the query"]),
        "b": ("any", ["rewriters array", "rewriters list"]),
    },
    {
        "id": "q04-smui-deploy",
        "title": "SMUI deployment mechanism change",
        "prompt": "SMUI deploys Querqy rules to Solr by copying a rules text file to Solr's config directory and triggering a config reload. When targeting OpenSearch instead, what specific mechanism replaces the file-copy deployment? Name the exact API endpoint.",
        "a": ("any", ["_querqy/rewriter", "_plugins/_querqy"]),
        "b": ("any", ["PUT"]),
    },
    {
        "id": "q05-smui-opensearch-scope",
        "title": "SMUI v4.0.11 OpenSearch scope (labelling vs deployment)",
        "prompt": "SMUI v4.0.11 added OpenSearch support according to the release notes. As a migration consultant, what specifically did v4.0.11 add — full OpenSearch deployment parity with Solr, or something narrower? What does this mean for a team planning to use SMUI as their rules-management UI on OpenSearch?",
        "a": ("any", ["label", "labelling", "labeling", "front-end", "frontend", "button", "cosmetic", "rename", "renaming", "ui-only", "ui only"]),
        "b": ("any", ["doesn't deploy", "does not deploy", "no deployment", "not deploy", "manually", "still need", "additional work", "not full parity", "not at parity", "outside smui", "outside of smui", "lacks deployment", "no deploy"]),
    },
    {
        "id": "q06-querqy-down-conv",
        "title": "Querqy DOWN -> negative_boost conversion",
        "prompt": "In Querqy, a DOWN(500) rule penalizes matches. To translate this to OpenSearch's boosting query with negative_boost, what is the exact formula to convert the DOWN weight to a negative_boost value? Show the formula and the result for DOWN(500).",
        "a": ("any", ["negative_boost"]),
        "b": ("any", ["0.002", "0.001", "1/(1+", "1 / (1 +"]),
    },
    {
        "id": "q07-smui-export-format",
        "title": "SMUI rule export format",
        "prompt": "What is the format of a SMUI rules export file? Is it JSON, XML, or something else? Show an example of what the export looks like for a term with SYNONYM and UP rules.",
        "a": ("any", ["plain text", "Common Rules", "text format"]),
        "b": ("any", ["=>"]),
    },
    {
        "id": "q08-copyfield-multifields",
        "title": "copyField -> multi-fields vs copy_to",
        "prompt": "In our TMDB Solr schema, we have copyField rules that copy title to title_en (English analyzer) and title_bidirect_syn (bidirectional synonym analyzer). How should we represent these in OpenSearch? Should we use copy_to or multi-fields? Explain why.",
        "a": ("any", ["multi-field", "multi field", "multifield", "fields\":"]),
        "b": ("any", ["copy_to does not re-analyze", "copy_to copies raw", "not copy_to", "copy_to only copies", "copy_to is for"]),
    },
    {
        "id": "q09-pos-incr-gap",
        "title": "positionIncrementGap default difference",
        "prompt": "Solr's default positionIncrementGap is 0. What is OpenSearch's default position_increment_gap value? A client migrating from Solr has multi-valued text fields where they INTENTIONALLY allow phrase matches across value boundaries (positionIncrementGap=0). What specific OpenSearch mapping change preserves this behavior?",
        "a": ("any", ["100", "default is 100", "defaults to 100"]),
        "b": ("any", ["position_increment_gap"]),
    },
    {
        "id": "q10-dynamic-fields-limit",
        "title": "Dynamic field mapping explosion limit",
        "prompt": "Our Solr schema uses 800+ dynamic fields (*_s, *_i, *_txt, *_dt). What specific OpenSearch setting will we hit, what is its default value, and what are the risks of increasing it?",
        "a": ("any", ["total_fields.limit", "total_fields"]),
        "b": ("any", ["1000", "1,000"]),
    },
    {
        "id": "q11-localparams-arch",
        "title": "LocalParams replacement architecture",
        "prompt": "We use Solr LocalParams extensively: {!boost b=recip(ms(NOW,date),3.16e-11,1,1) v=$qq} and {!type=edismax qf='title^2 body' v=$qq}. OpenSearch has no LocalParams. Give the specific architectural pattern we should use to replace this — not just \"rewrite as Query DSL\".",
        "a": ("any", ["search template", "search_template", "mustache"]),
        "b": ("any", ["application layer", "application-layer", "query builder", "client-side", "client side"]),
    },
    {
        "id": "q12-search-pipelines",
        "title": "Search Pipelines for conditional query rewrite",
        "prompt": "Querqy's DELETE rule conditionally removes terms from a query (e.g., 'cheap laptop => DELETE: cheap'). Without the Querqy plugin in OpenSearch, name the specific OpenSearch 2.x feature that can intercept and modify queries before execution. What is it called and when was it introduced?",
        "a": ("any", ["search pipeline"]),
        "b": ("any", ["request processor", "script processor", "search request processor"]),
    },
    {
        "id": "q13-bf-vs-boost",
        "title": "bf additive vs boost multiplicative",
        "prompt": "In Solr eDisMax, what is the exact difference between bf and boost in terms of how they combine with the relevance score? For each, give the exact OpenSearch function_score boost_mode value.",
        "a": ("any", ["additive", "adds to", "addition", "sum"]),
        "b": ("any", ["multiplicative", "multiplies", "multiply", "multiplication"]),
    },
    {
        "id": "q14-tfidf-bm25-k1",
        "title": "TF-IDF -> BM25 on short fields",
        "prompt": "When migrating from Solr 6.x (ClassicSimilarity/TF-IDF) to OpenSearch (BM25), what specific ranking behavior changes on short text fields like product titles? Name the exact BM25 parameter that controls term frequency saturation and what value approximates TF-IDF behavior.",
        "a": ("any", ["k1"]),
        "b": ("any", ["saturation", "term frequency"]),
    },
    {
        "id": "q15-querqy-aws-managed",
        "title": "Querqy NOT on AWS OpenSearch Service",
        "prompt": "We use Querqy in Solr for query rewriting. We're migrating to AWS OpenSearch Service (the managed service). Can we install the Querqy plugin? If not, what must we do instead?",
        "a": ("any", ["cannot", "can't", "not available", "not supported", "no.", "not allow"]),
        "b": ("any", ["native", "bool", "should", "synonym"]),
    },
    {
        "id": "q16-collection-aliases",
        "title": "Collection aliases write routing",
        "prompt": "Our Solr uses collection aliases that route writes to the latest time-partitioned collection while searching across all. OpenSearch index aliases can search multiple indices but can only write to one. How do we handle our rolling-window architecture?",
        "a": ("any", ["ISM", "Index State Management", "rollover"]),
        "b": ("any", ["is_write_index"]),
    },
    {
        "id": "q17-atomic-no-source",
        "title": "Atomic updates without _source",
        "prompt": "Our Solr index has stored=false on most fields but supports atomic updates via docValues. We're migrating to OpenSearch. What specific problem will we hit with partial updates?",
        "a": ("any", ["_source"]),
        "b": ("any", ["cannot", "not possible", "requires", "must", "needs"]),
    },
    {
        "id": "q18-lucene-fallacy",
        "title": "Lucene-underneath fallacy",
        "prompt": "A client says \"It's all Lucene underneath, so most of it ports directly.\" As a migration consultant, give your response. Be specific about where this assumption breaks.",
        "a": ("any", ["query parser", "parser"]),
        "b": ("any", ["BM25", "scoring", "similarity"]),
    },
    {
        "id": "q19-mechanical-translation",
        "title": "Mechanical translation fantasy",
        "prompt": "A client says their Solr-to-OpenSearch migration is \"mostly config conversion work.\" Name 3 specific areas that require genuine redesign, not just translation.",
        "a": ("any", ["redesign", "re-design", "rethink", "re-architect", "rearchitect"]),
        "b": ("any", ["analyzer", "handler", "scoring", "relevance"]),
    },
    {
        "id": "q20-plugin-audit",
        "title": "Plugin/custom handler dependency audit",
        "prompt": "A client says \"We didn't think any custom Solr components were important.\" What specific component types should be inventoried, and why is this claim dangerous?",
        "a": ("any", ["request handler", "requesthandler"]),
        "b": ("any", ["update processor", "updateprocessor", "search component", "searchcomponent"]),
    },
]


def check(text: str, criterion) -> bool:
    mode, needles = criterion
    lower = text.lower()
    hits = [n for n in needles if n.lower() in lower]
    if mode == "any":
        return len(hits) > 0
    if mode == "not_any":
        return len(hits) == 0
    raise ValueError(f"unknown mode {mode}")


def _cache_path(model_id: str, prompt: str) -> Path:
    key = hashlib.sha256(f"{model_id}\n{prompt}".encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{key}.json"


def _is_error_response(text: str) -> bool:
    return text.startswith("[ERROR]") or text.startswith("[TIMEOUT]") or text == "[EMPTY]"


def cached_call(model_id: str, prompt: str, fn, refresh: bool) -> tuple[str, bool]:
    """Return (response, was_cached). Errors never cache."""
    path = _cache_path(model_id, prompt)
    if not refresh and path.exists():
        try:
            data = json.loads(path.read_text())
            return data["response"], True
        except Exception:
            pass  # corrupt cache entry; fall through and re-call
    resp = fn(prompt)
    if not _is_error_response(resp):
        path.write_text(json.dumps({
            "model": model_id,
            "prompt": prompt,
            "response": resp,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }, indent=2))
    return resp, False


def call_haiku(prompt: str, timeout: int = 90) -> str:
    """Run Claude Haiku via the CLI from /tmp for isolation."""
    tmpdir = tempfile.mkdtemp(prefix="sma-haiku-")
    try:
        proc = subprocess.run(
            ["claude", "--model", HAIKU_MODEL, "--print", prompt],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = proc.stdout.strip()
        if not out and proc.stderr:
            out = f"[STDERR] {proc.stderr.strip()}"
        return out
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR] {e}"


def call_ollama(prompt: str, timeout: int = 180) -> str:
    """Call local Ollama HTTP API; no streaming, no thinking spinners."""
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 1024},
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data.get("response", "").strip() or "[EMPTY]"
    except urllib.error.URLError as e:
        return f"[ERROR] {e}"
    except Exception as e:
        return f"[ERROR] {e}"


MODEL_IDS = {"haiku": HAIKU_MODEL, "qwen": OLLAMA_MODEL}
MODEL_FNS = {"haiku": call_haiku, "qwen": call_ollama}


def main():
    args = sys.argv[1:]
    refresh_all = "--refresh" in args
    refresh_models = set()
    cleaned = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--refresh":
            i += 1
            continue
        if a == "--refresh-model":
            if i + 1 < len(args):
                refresh_models.add(args[i + 1])
                i += 2
                continue
        cleaned.append(a)
        i += 1
    only = set(cleaned)  # optional: filter by qid

    rows = []
    for q in STUMPERS:
        qid = q["id"]
        if only and qid not in only:
            continue
        print(f"\n=== {qid}: {q['title']} ===", flush=True)

        for label in ("haiku", "qwen"):
            model_id = MODEL_IDS[label]
            fn = MODEL_FNS[label]
            refresh = refresh_all or (label in refresh_models)
            t0 = time.time()
            print(f"  -> {label} ...", end="", flush=True)
            resp, was_cached = cached_call(model_id, q["prompt"], fn, refresh)
            elapsed = time.time() - t0
            (RESP_DIR / f"{qid}.{label}.txt").write_text(resp)
            a_pass = check(resp, q["a"])
            b_pass = check(resp, q["b"])
            mark = lambda p: "GREEN" if p else "RED"
            tag = "cache" if was_cached else "live"
            print(f" {elapsed:.1f}s ({tag})  A={mark(a_pass)} B={mark(b_pass)}", flush=True)
            rows.append({
                "qid": qid,
                "title": q["title"],
                "model": label,
                "a": a_pass,
                "b": b_pass,
                "elapsed": elapsed,
                "cached": was_cached,
            })

    # Emit markdown summary
    lines = [
        "# Stumper triage — bare model results",
        "",
        "Both models run from `/tmp` with no skill discovery, no references.",
        f"Targets: `{HAIKU_MODEL}` (cloud) and `{OLLAMA_MODEL}` (local Ollama).",
        "Criteria are the contains-any patterns from `stumper-candidates.md`.",
        "RED = criterion missed = candidate stumper for this model.",
        "",
        "| QID | Title | Haiku A | Haiku B | Qwen A | Qwen B | Both fail? |",
        "| --- | ----- | :-----: | :-----: | :----: | :----: | :--------: |",
    ]
    by_qid = {}
    for r in rows:
        by_qid.setdefault(r["qid"], {"title": r["title"]})[r["model"]] = r

    for qid, group in by_qid.items():
        h = group.get("haiku", {})
        q = group.get("qwen", {})
        h_red = (not h.get("a", True)) or (not h.get("b", True))
        q_red = (not q.get("a", True)) or (not q.get("b", True))
        both = "YES" if (h_red and q_red) else ("haiku" if h_red else ("qwen" if q_red else "no"))
        cell = lambda v: ("GREEN" if v else "RED") if v is not None else "-"
        lines.append(
            f"| {qid} | {group['title']} | {cell(h.get('a'))} | {cell(h.get('b'))} | {cell(q.get('a'))} | {cell(q.get('b'))} | {both} |"
        )
    lines.append("")
    lines.append(f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')}.")
    RESULTS_MD.write_text("\n".join(lines))
    print(f"\nWrote {RESULTS_MD}")


if __name__ == "__main__":
    main()
