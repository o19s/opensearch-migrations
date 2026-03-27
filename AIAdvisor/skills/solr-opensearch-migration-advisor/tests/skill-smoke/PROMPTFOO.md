# Promptfoo Primer

A plain-English introduction to [promptfoo](https://promptfoo.dev/) for people
who have never used it. Focuses on the concepts you need to understand the two
config files in this directory.

## What is promptfoo?

Promptfoo is an **LLM evaluation framework**. It sends prompts to an LLM,
captures the responses, and checks them against assertions you define. Think
of it as "unit tests for prompts."

```
┌──────────────┐      ┌───────────┐      ┌──────────────┐
│  YAML config │─────▶│ promptfoo │─────▶│  LLM (e.g.   │
│  (prompts +  │      │   engine  │      │   Bedrock)   │
│  assertions) │      │           │◀─────│              │
│              │      │  ✓ PASS   │      └──────────────┘
│              │      │  ✗ FAIL   │
└──────────────┘      └───────────┘
```

You don't write code. You write a YAML file that says:
1. **Provider** — which LLM to call (Bedrock, OpenAI, HTTP endpoint, etc.)
2. **Prompt** — what to send
3. **Assertions** — what the response must contain or satisfy

Promptfoo calls the LLM, checks the assertions, and prints a pass/fail report.

## Installing and running

```bash
# No install needed — npx downloads it on first use
npx promptfoo eval --config your-config.yaml

# View results in a browser
npx promptfoo view

# Optional global install (faster subsequent runs)
npm install -g promptfoo
promptfoo eval --config your-config.yaml
```

**Requirements:** Node.js 18+ (which gives you `npm` and `npx`).

## The four key concepts

### 1. Providers

A provider tells promptfoo *how to call the LLM*. In our configs we use
Amazon Bedrock:

```yaml
providers:
  - id: bedrock:amazon.nova-micro-v1:0    # model ID
    config:
      region: us-east-1                    # AWS region
      max_tokens: 500                      # response length limit
```

Promptfoo supports many providers out of the box: OpenAI, Anthropic, Bedrock,
Azure, Ollama, HTTP endpoints, etc. You can switch models by changing the `id`.

The `label` field is optional — it gives the provider a human-readable name
that shows up in reports and can be referenced in test-level `providers:` filters.

### 2. Prompts

The prompt template defines *what text is sent to the LLM*. Variables are
injected using `{{double braces}}`:

```yaml
prompts:
  - "{{prompt}}"    # The entire prompt comes from the test's `vars.prompt`
```

This is intentionally simple. The actual content is built in the `vars` section
of each test (see below).

### 3. Tests and vars

Each test defines:
- **vars** — key/value pairs that fill in the prompt template
- **assert** — checks to run on the LLM's response

```yaml
tests:
  - description: "My test"
    vars:
      prompt: |
        You are a migration advisor.
        ---
        User: YOLO — what should I know about migrating Solr?
    assert:
      - type: icontains
        value: "EXPRESS MODE"
```

When this test runs, promptfoo:
1. Substitutes `{{prompt}}` in the template with the value from `vars.prompt`
2. Sends that text to the provider (Bedrock)
3. Gets back the LLM's response
4. Checks: does the response contain "EXPRESS MODE" (case-insensitive)?
5. Reports PASS or FAIL

### 4. Assertions

Assertions are the "test expectations." Common types:

| Type | What it checks | Example |
|------|---------------|---------|
| `icontains` | Response contains string (case-insensitive) | `value: "BM25"` |
| `contains` | Response contains string (case-sensitive) | `value: "[ASSUMED:"` |
| `is-json` | Response is valid JSON | (no value needed) |
| `javascript` | Custom JS expression returns truthy | `value: "output.length > 100"` |
| `llm-rubric` | Another LLM judges the response | `value: "Response is helpful"` |

In our smoke tests we only use `icontains` — the simplest assertion type.
The connected tests (`../connected/promptfooconfig.yaml`) use `javascript`
and `llm-rubric` for more sophisticated checks.

## How our two config files work

### `promptfooconfig-inline.yaml` — everything in one file

```
┌─ promptfooconfig-inline.yaml ──────────────────────────────────────┐
│                                                                     │
│  provider: bedrock:nova-micro                                       │
│                                                                     │
│  test 1/3:                                                          │
│    vars.prompt: "You are a migration advisor.                       │
│                  ## Express Mode (YOLO)                              │
│                  Trigger: user says YOLO...                          │  ◄── Nugget 1
│                  ---                                                 │      pasted here
│                  User: YOLO — list the 3 most critical things..."   │
│    assert: icontains "EXPRESS MODE"  ──────────────────▶ ✓ PASS     │
│                                                                     │
│  test 2/3:                                                          │
│    vars.prompt: (same as above — only nugget 1)                     │
│    assert: icontains "BM25 vs TF-IDF"  ───────────────▶ ✗ FAIL     │  ◄── Nugget 2
│                                                          (expected)  │      NOT loaded
│  test 3/3:                                                          │
│    vars.prompt: (same as above — only nugget 1)                     │
│    assert: icontains "opensearch-java"  ───────────────▶ ✗ FAIL     │  ◄── Nugget 3
│                                                          (expected)  │      NOT loaded
└─────────────────────────────────────────────────────────────────────┘
```

The prompt text is **copy-pasted directly into the YAML**. This makes the file
self-contained but means only nugget 1 is present — tests 2 and 3 intentionally
fail to prove the other nuggets are needed.

### `promptfooconfig-external.yaml` — prompt loaded from a file

```
┌─ promptfooconfig-external.yaml ────────────────────────────────────┐
│                                                                     │
│  provider: bedrock:nova-micro                                       │
│                                                                     │
│  test 1/3:                                                          │
│    vars:                                                            │
│      system_prompt: file://skill-assembled.txt  ──────┐             │
│      user_prompt: "YOLO — list the 3 most..."         │             │
│      prompt: "{{system_prompt}}\n---\nUser: {{user_prompt}}"        │
│    assert: icontains "EXPRESS MODE"  ──────────────▶ ✓ PASS         │
│                                                       │             │
│  test 2/3: (same vars)                                │             │
│    assert: icontains "BM25 vs TF-IDF"  ───────────▶ ✓ PASS         │
│                                                       │             │
│  test 3/3: (same vars)                                │             │
│    assert: icontains "opensearch-java"  ───────────▶ ✓ PASS         │
│                                                       │             │
└───────────────────────────────────────────────────────┘             │
                                                                      │
┌─ skill-assembled.txt (GENERATED) ──────────────────────────────────┐
│                                                                     │
│  You are a Solr-to-OpenSearch migration advisor.                    │
│                                                                     │
│  ## Express Mode (YOLO)                        ◄── nugget-01        │
│  Trigger: user says "YOLO"...                                       │
│                                                                     │
│  ## Critical Behavioral Incompatibility        ◄── nugget-02        │
│  BM25 (OpenSearch default) scores differently...                    │
│                                                                     │
│  ## Key Query and Schema Translations          ◄── nugget-03        │
│  SolrJ → opensearch-java...                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

The YAML says `file://skill-assembled.txt` and promptfoo reads that file at
eval time. The file is **generated by `run_smoke.sh --step 4`** from the
three nugget files. All 3 nuggets are present → all 3 tests pass.

### The key difference, summarized

| | Inline | External |
|--|--------|----------|
| Prompt lives in | The YAML file | A separate `.txt` file |
| How content gets there | You paste it | `file://` reference (promptfoo loads it) |
| Nuggets included | 1 (hardcoded) | All 3 (generated from nuggets/) |
| Expected result | 1/3 pass | 3/3 pass |
| When to use | Getting started, experimenting | CI, production, shared prompts |

## Reading promptfoo output

When you run `npx promptfoo eval`, you'll see a table like:

```
┌─────────────────────────────────────────────────────────────────────┐
│ migration-advisor-external                                          │
├─────────────────────────────────────────────────────────────────────┤
│ 1/3: EXPRESS MODE banner                              [PASS]        │
│ 2/3: BM25 vs TF-IDF incompatibility                  [PASS]        │
│ 3/3: opensearch-java client translation               [PASS]        │
└─────────────────────────────────────────────────────────────────────┘

Successes: 3
Failures:  0
```

For more detail, run `npx promptfoo view` to open an interactive web UI that
shows the full LLM responses, which assertions passed/failed, and why.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | All assertions passed |
| 1 | One or more assertions failed |
| 2 | Configuration error (bad YAML, missing file, etc.) |

`run_smoke.sh` handles exit code 1 gracefully for Step 3 (where failures are
expected).

## Promptfoo YAML anatomy — annotated

Here's the complete structure with annotations:

```yaml
# Human-readable label for this eval suite
description: "my eval suite"

# Which LLM(s) to call. You can list multiple to compare models.
providers:
  - id: bedrock:amazon.nova-micro-v1:0     # provider:model-id
    label: my-model                         # optional friendly name
    config:
      region: us-east-1                     # provider-specific settings
      max_tokens: 500

# Prompt template(s). {{vars}} are replaced per-test.
prompts:
  - "{{prompt}}"

# Optional: shared settings for all tests
defaultTest:
  options:
    provider:                               # LLM used for llm-rubric judging
      id: bedrock:amazon.nova-micro-v1:0    # (can be a cheaper model)

# The actual test cases
tests:
  - description: "What this test proves"
    providers: [my-model]                   # optional: filter to specific provider
    vars:                                   # values injected into prompt template
      prompt: "the text sent to the LLM"
      system_prompt: "file://path.txt"      # file:// loads from disk
    assert:                                 # checks on the LLM response
      - type: icontains
        value: "expected substring"
        description: "why this matters"     # shows in reports
```

### `file://` paths

- Paths are **relative to the YAML file's directory**, not the working directory.
- `file://skill-assembled.txt` means "load `skill-assembled.txt` from the same
  directory as this YAML file."
- The file must exist before `promptfoo eval` runs. For generated files (like
  ours), the orchestration script creates them first.

### Environment variables

Use `{{env.VAR_NAME | default('fallback')}}` in the YAML:

```yaml
providers:
  - id: "bedrock:{{env.SMOKE_MODEL | default('amazon.nova-micro-v1:0')}}"
```

This lets you override the model at runtime:
```bash
SMOKE_MODEL=amazon.nova-pro-v1:0 npx promptfoo eval --config ...
```

## Where to go from here

1. **Run the smoke tests** — `./run_smoke.sh` and read the output
2. **Edit a nugget** — change `nuggets/nugget-02-bm25.txt` and re-run `--step 2`
   to see how the LLM's behavior changes
3. **Add a nugget** — create `nuggets/nugget-04-your-topic.txt`, add a 4th
   assertion, and re-run
4. **Try the connected tests** — `../connected/run_connected_tests.sh` for the
   full E2E pipeline with Docker
5. **Read the promptfoo docs** — [promptfoo.dev/docs](https://promptfoo.dev/docs/intro)
   for assertion types, custom scorers, CI integration, etc.
