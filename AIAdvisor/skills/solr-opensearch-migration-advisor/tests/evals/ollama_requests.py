"""
Promptfoo provider for local Ollama models.

Mirrors the shape of claude_requests.py — same `cwd:` config field
points at a fixture dir; the fixture's CLAUDE.md is loaded as the
system prompt. The user prompt is whatever promptfoo passes in.

Why: Ollama isn't an agent, so /tmp isolation is moot — there's no tool
use, no file traversal, just LLM completion. The bare-vs-guided distinction
is enforced at the system-prompt level by which fixture's CLAUDE.md gets
loaded.

Config:
  cwd:              fixture dir (relative to this script). Its CLAUDE.md
                    is read as the system prompt. Required.
  model:            Ollama model tag, e.g. "qwen2.5:7b". Required.
  ollama_url:       Override base URL (default http://localhost:11434).
  num_predict:      Max tokens (default 1024).
  temperature:      Default 0.2.
"""
import json
import os
import urllib.error
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def _load_system_prompt(cwd_config: str) -> str:
    if not cwd_config:
        raise ValueError("ollama_requests provider requires `cwd` in config")
    cwd = cwd_config if os.path.isabs(cwd_config) else os.path.join(SCRIPT_DIR, cwd_config)
    claude_md = os.path.join(cwd, "CLAUDE.md")
    with open(claude_md, "r", encoding="utf-8") as f:
        return f.read()


def call_api(prompt: str, options: dict, context: dict) -> dict:
    config = options.get("config", {})
    model = config.get("model")
    if not model:
        return {"error": "ollama_requests: `model` is required in provider config"}

    ollama_url = config.get("ollama_url", "http://localhost:11434").rstrip("/")
    num_predict = int(config.get("num_predict", 1024))
    temperature = float(config.get("temperature", 0.2))

    try:
        system_prompt = _load_system_prompt(config.get("cwd"))
    except Exception as e:
        return {"error": f"ollama_requests: failed to load system prompt: {e}"}

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{ollama_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read().decode("utf-8"))
            content = (data.get("message") or {}).get("content", "")
            return {"output": content.strip() or "[EMPTY]"}
    except urllib.error.URLError as e:
        return {"error": f"ollama_requests: HTTP error: {e}"}
    except Exception as e:
        return {"error": f"ollama_requests: {e}"}
