# Skill Smoke Test — Step-by-Step Skill Loading and Evaluation

Proves the migration advisor skill works by building it up from nothing, one
piece at a time. If you're new to the project, start here before looking at
the full [connected tests](../connected/).

## The point of this test

We have an LLM (local via Ollama or cloud via Amazon Bedrock) and a "skill" —
a system prompt that tells the LLM how to advise on Solr-to-OpenSearch
migrations. This test answers three questions in order:

1. **Can we talk to the LLM at all?** (bare-metal API call, no skill loaded)
2. **Does loading skill content change the LLM's behavior?** (add skill pieces
   one at a time, watch assertions flip from FAIL to PASS)
3. **Can we automate this with promptfoo?** (move from hand-rolled bash to a
   proper eval framework)

## LLM provider: Ollama (local) vs Bedrock (cloud)

The script auto-detects which LLM to use. **You don't have to configure
anything** if you have Ollama running locally — it just works.

### Detection priority

| Priority | Condition | Provider used |
|----------|-----------|---------------|
| 1 | `--provider ollama` or `--provider bedrock` flag | What you said |
| 2 | `AWS_ACCESS_KEY_ID` or `AWS_PROFILE` is set in env | **Bedrock** (you set up cloud creds) |
| 3 | Ollama is running on `localhost:11434` | **Ollama** (free, fast, no cloud needed) |
| 4 | None of the above | Bedrock (tries instance profile) |

**The practical default:** if you have Ollama running and haven't exported AWS
credentials in your current shell, the script uses Ollama. If you `export
AWS_ACCESS_KEY_ID=...`, it switches to Bedrock. A loud colored banner at the
top of every run tells you which provider was chosen and why.

### Ollama setup (recommended for local dev)

```bash
# Install (if not already)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the default model — qwen2.5:7b fits in 12 GB VRAM with room to spare
ollama pull qwen2.5:7b

# Verify it works
ollama run qwen2.5:7b "Say hello"
```

**Model recommendations for 12 GB VRAM:**

| Model | Size | Notes |
|-------|------|-------|
| **qwen2.5:7b** (default) | ~5 GB | Best instruction-following at this size. Our default. |
| llama3.1:8b | ~5 GB | Solid general-purpose, Meta |
| gemma2:9b | ~6 GB | Good quality, Google |
| mistral:7b | ~4 GB | Fast, Mistral AI |
| qwen2.5:14b | ~9 GB | Better quality, tight fit at 12 GB |

Override the model:
```bash
OLLAMA_MODEL=llama3.1:8b ./run_smoke.sh
```

### Bedrock setup (for CI / cloud)

```bash
# Option A: environment variables
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...        # if using temporary credentials
export AWS_DEFAULT_REGION=us-east-1

# Option B: SSO login
aws sso login --profile your-profile

# Option C: IAM instance profile (EC2/ECS/Lambda — automatic)
```

Override the model:
```bash
BEDROCK_MODEL=amazon.nova-pro-v1:0 ./run_smoke.sh --provider bedrock
```

**Quick sanity check** (Bedrock):
```bash
aws bedrock-runtime converse \
  --model-id amazon.nova-micro-v1:0 \
  --region us-east-1 \
  --messages '[{"role":"user","content":[{"text":"Say hello"}]}]' \
  | jq -r '.output.message.content[0].text'
```

## Prerequisites

| Tool | Required for | Install |
|------|-------------|---------|
| **jq** | All steps (JSON parsing) | `sudo apt install jq` / `brew install jq` |
| **curl** | All steps (Ollama + Solr) | Usually pre-installed |
| **Ollama** | Steps 1, 2, 5 if using local provider | [ollama.com](https://ollama.com/) |
| **AWS CLI v2** | Steps 1, 2, 5 if using Bedrock provider | [Install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| **Node.js 18+** | Steps 3, 4 (promptfoo) | [nodejs.org](https://nodejs.org/) or `nvm install 18` |
| **Docker** | Step 5 with `--start-docker` only | [docker.com](https://docs.docker.com/get-docker/) |

### Node.js / promptfoo (Steps 3–4 only)

Promptfoo runs via `npx` — no global install needed. The first run downloads
it automatically. If you prefer to pin a version:

```bash
npm install -g promptfoo    # global install (optional)
```

> **Why not `uv` / Python venv?** Promptfoo is a Node.js tool (TypeScript).
> It has no Python dependency. The `uv` / `pip` ecosystem isn't relevant here.
> If a future test step adds Python-based evaluation (e.g. a custom scorer),
> we'd add a `uv venv` setup at that point. For now, Node.js + npx is all
> you need.

## Quick start

```bash
cd skills/solr-opensearch-migration-advisor/tests/skill-smoke

# Run everything — auto-detects Ollama or Bedrock
./run_smoke.sh

# Run a single step
./run_smoke.sh --step 2

# Run specific steps
./run_smoke.sh --steps 1,2

# Force a specific provider
./run_smoke.sh --provider ollama               # local Ollama
./run_smoke.sh --provider bedrock              # cloud Bedrock

# Override the model
OLLAMA_MODEL=llama3.1:8b ./run_smoke.sh                      # local
BEDROCK_MODEL=amazon.nova-pro-v1:0 ./run_smoke.sh --provider bedrock  # cloud

# Step 5 with live Solr (pick one)
./run_smoke.sh --step 5 --start-docker         # spin up Docker for you
./run_smoke.sh --step 5 --solr-url http://localhost:8983   # existing Solr
```

## What each step does

### Step 1 — Bare metal baseline

**What:** Calls the LLM directly via `aws bedrock-runtime converse` with **no
system prompt** — just a raw user question about Solr migration.

**Why:** Proves the API connection works. Also shows what the LLM says
*without* any skill guidance: the output is unpredictable, unstructured,
and may or may not mention the right things.

**Assertions:**
- LLM response is non-empty (**should PASS**)
- Contains "EXPRESS MODE" (**expected FAIL** — model has no reason to use this format)
- Contains "BM25 vs TF-IDF" (**expected FAIL** — might get lucky, but not reliable)
- Contains "opensearch-java" (**expected FAIL** — might get lucky, but not reliable)

"Expected FAIL" means the test deliberately fails to prove the skill is needed.
The output renders in yellow, not red.

### Step 2 — Nugget progression

**What:** Loads skill "nuggets" (small text files) into the system prompt one at
a time. Each nugget teaches the LLM one specific thing. After adding each
nugget, the same 3 assertions are re-run.

**Why:** Demonstrates that skill content directly controls LLM behavior. When a
nugget is missing, its assertion fails. When you add it, the assertion passes.
This is the core insight: **the skill is not decoration — it's load-bearing.**

**The three nuggets:**

| File | What it teaches the LLM | Assertion it unlocks |
|------|------------------------|---------------------|
| `nuggets/nugget-01-express-mode.txt` | When user says "YOLO", open with an EXPRESS MODE banner and mark assumptions with `[ASSUMED: ...]` | Response contains "EXPRESS MODE" |
| `nuggets/nugget-02-bm25.txt` | Always flag "BM25 vs TF-IDF scoring incompatibility" as a HIGH-severity issue | Response contains "BM25 vs TF-IDF" |
| `nuggets/nugget-03-translations.txt` | SolrJ must be replaced with opensearch-java; eDisMax → multi_match; etc. | Response contains "opensearch-java" |

**Expected results:**

| Nuggets loaded | Assertions passed | Detail |
|---------------|-------------------|--------|
| 1 (express mode only) | 1/3 | EXPRESS MODE passes; BM25 and opensearch-java fail |
| 2 (+ BM25) | 2/3 | EXPRESS MODE + BM25 pass; opensearch-java still fails |
| 3 (+ translations) | 3/3 | All pass |

### Step 3 — Promptfoo with inline prompt

**What:** Runs the same 3 assertions, but now through **promptfoo** instead of
hand-rolled bash. The prompt text is written directly inside the YAML config
file (`promptfooconfig-inline.yaml`).

**Why:** Introduces promptfoo as a tool. Shows the simplest possible integration:
everything in one file, no external dependencies. But because only nugget 1 is
pasted into the YAML, only 1/3 assertions pass — same as Step 2 with 1 nugget.

**See also:** [Appendix: Promptfoo Primer](#appendix-promptfoo-primer) below and
the detailed [PROMPTFOO.md](PROMPTFOO.md) companion doc.

### Step 4 — Promptfoo with external prompt file

**What:** Same 3 assertions via promptfoo, but now the prompt is loaded from an
external file (`skill-assembled.txt`) using promptfoo's `file://` syntax.
The script generates that file by concatenating all 3 nuggets before running.

**Why:** Shows the production pattern: prompts live in version-controlled files,
not buried in YAML. Makes it easy to iterate on prompt content without touching
test config. Because all 3 nuggets are included, all 3 assertions pass (3/3).

### Step 5 — Live Solr (YOLO + interactive)

**What:** Connects to a real running Solr instance, fetches its schema, and
runs two types of conversations:

- **5a. YOLO mode** — one-shot: "here's the schema, generate a migration spec."
  Asserts: EXPRESS MODE banner, BM25 flag, opensearch-java, `[ASSUMED:]` markers.
- **5b. Interactive mode** — multi-turn: a scripted 2-turn conversation where
  the advisor first asks clarifying questions, then the user provides details.
  Asserts: Turn 1 contains a question mark (advisor is asking); Turn 2 references
  what the user said.

**Why:** Proves the skill works against live data, not just canned test inputs.
The interactive test shows that without the "YOLO" trigger, the advisor behaves
differently (asks questions instead of assuming).

**Solr source options:**
```bash
# Auto-detect (checks localhost:38983 from the connected tests)
./run_smoke.sh --step 5

# Start Docker containers for you
./run_smoke.sh --step 5 --start-docker

# Point at any running Solr
./run_smoke.sh --step 5 --solr-url http://solr.example.com:8983
```

If no Solr is found and `--start-docker` isn't set, step 5 skips gracefully.

## Why two promptfoo config files?

There are two YAML files because they demonstrate two different approaches to
the same problem: how to get prompt content into a promptfoo test.

### `promptfooconfig-inline.yaml` (Step 3)

```yaml
# The prompt text is WRITTEN DIRECTLY in the YAML:
vars:
  prompt: |
    You are a Solr-to-OpenSearch migration advisor.
    ## Express Mode (YOLO)
    Trigger: user says "YOLO"...
    ---
    User: YOLO — list the 3 most critical things...
```

**Pros:**
- Self-contained — one file, nothing else to manage
- Easy to understand — you can read the entire test top to bottom
- Good for quick experiments and getting started

**Cons:**
- Prompt content is duplicated (not shared with the actual skill)
- Hard to keep in sync if the skill evolves
- Gets unwieldy for long prompts (indentation, escaping)
- Only has nugget 1 hardcoded → tests 2/3 intentionally FAIL

### `promptfooconfig-external.yaml` (Step 4)

```yaml
# The prompt text is LOADED FROM A FILE:
vars:
  system_prompt: "file://skill-assembled.txt"     # <-- THIS is the difference
  user_prompt: "YOLO — list the 3 most critical things..."
  prompt: |
    {{system_prompt}}
    ---
    User: {{user_prompt}}
```

**Pros:**
- Prompt content lives in its own file — edit the skill without touching tests
- The file can be generated (as we do: concatenate nuggets) or hand-maintained
- Multiple test configs can share the same prompt file
- All 3 nuggets are included → all 3 tests PASS

**Cons:**
- Requires the file to exist before running (`run_smoke.sh --step 4` generates it)
- Slightly more moving parts

### Which should I use?

| Situation | Use |
|-----------|-----|
| Getting started / experimenting | Inline |
| CI / production evals | External |
| Prompt is short (< 20 lines) | Either |
| Prompt is shared across test configs | External |
| You want to iterate on prompt content | External |

The progression in this test suite is **intentional**: start simple (inline),
then graduate to the production pattern (external) once you see why it's better.

## File inventory

```
skill-smoke/
├── run_smoke.sh                    # Main orchestrator — runs all 5 steps
├── nuggets/
│   ├── nugget-01-express-mode.txt  # Skill piece: YOLO banner + [ASSUMED:] markers
│   ├── nugget-02-bm25.txt          # Skill piece: BM25 vs TF-IDF incompatibility
│   └── nugget-03-translations.txt  # Skill piece: opensearch-java, multi_match, etc.
├── promptfooconfig-inline.yaml     # Step 3: prompt hardcoded in YAML (1/3 pass)
├── promptfooconfig-external.yaml   # Step 4: prompt from file:// (3/3 pass)
├── skill-assembled.txt             # GENERATED at runtime by step 4 (gitignored)
├── .gitignore                      # Excludes skill-assembled.txt
├── README.md                       # This file
└── PROMPTFOO.md                    # Promptfoo primer for newcomers
```

## Relationship to other test suites

| Suite | Scope | When to use |
|-------|-------|-------------|
| **skill-smoke** (this) | Does the skill work? Does adding content change behavior? | First. Start here. |
| **connected** (`../connected/`) | Full E2E with Docker: Solr seeding, data migration, verification | After skill-smoke passes and you want to test the complete pipeline. |

## Troubleshooting

### "Ollama call failed — is Ollama running?"

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags | jq .

# Start it
ollama serve

# Pull the model (if not already)
ollama pull qwen2.5:7b

# Verify
ollama run qwen2.5:7b "Say hello"
```

### "Bedrock call failed — check AWS credentials and region"

```bash
# Verify credentials are configured
aws sts get-caller-identity

# Verify Bedrock model access (must be enabled in the AWS console)
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?modelId=='amazon.nova-micro-v1:0'].modelId" \
  --output text
```

If the model ID comes back empty, you need to enable model access in the
[Bedrock console](https://console.aws.amazon.com/bedrock/home#/modelaccess).

### Script is using Bedrock but I want Ollama (or vice versa)

The provider banner at the top of every run tells you which was chosen and why.
Common cause: you have `AWS_ACCESS_KEY_ID` exported in your shell profile, so
the script picks Bedrock even though Ollama is running.

```bash
# Force Ollama regardless of AWS env vars
./run_smoke.sh --provider ollama

# Or unset the AWS vars for this session
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
./run_smoke.sh
```

### "npx not found — skipping step 3"

Steps 3 and 4 need Node.js. Install it:

```bash
# Via nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
nvm install 18

# Or via package manager
sudo apt install nodejs npm   # Debian/Ubuntu
brew install node              # macOS
```

### Step 5 skips with "No Solr instance found"

Step 5 needs a running Solr. Easiest path:

```bash
# Start the connected tests' Docker services and leave them running
cd ../connected
./run_connected_tests.sh --no-teardown

# Now step 5 will auto-detect Solr on localhost:38983
cd ../skill-smoke
./run_smoke.sh --step 5
```

### "Expected FAIL" tests are PASSING

If a test marked "expected FAIL" actually passes, it means the LLM happened to
produce the right content without being explicitly instructed. This can happen
with more capable models (e.g. nova-pro). It's not a bug — it just means that
particular model already "knows" the concept. The test is still useful because
it proves behavior is **reliable** with the skill vs. **coincidental** without it.

## Appendix: Promptfoo primer

See [PROMPTFOO.md](PROMPTFOO.md) for a detailed introduction to promptfoo:
what it is, how it works, how the configs in this directory map to its concepts,
and how to read its output.
