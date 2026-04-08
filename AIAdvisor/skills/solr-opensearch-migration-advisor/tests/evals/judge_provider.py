"""
Cascading LLM-as-judge provider for promptfoo.

Tries providers in order:
  1. AWS Bedrock (if AWS credentials are configured)
  2. Ollama (if running locally)
  3. Fails fast with actionable error message

Usage in eval.yaml:
  defaultTest:
    options:
      provider: 'file://../../evals/judge_provider.py'
"""

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request


def _check_aws_credentials():
    """Check if AWS credentials are available (env vars or CLI config)."""
    # Check env vars first
    if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        return True
    # Check AWS CLI config
    if shutil.which("aws"):
        try:
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return False


def _check_ollama():
    """Check if Ollama is running and has a usable model."""
    try:
        resp = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        # Prefer larger models for judging quality
        for preferred in ["mistral-nemo", "llama3:8b", "mistral"]:
            for m in models:
                if preferred in m:
                    return m
        return models[0] if models else None
    except (urllib.error.URLError, OSError):
        return None


def _call_bedrock(prompt, options):
    """Call Bedrock as judge. Returns result or raises with actionable message."""
    import boto3

    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"

    try:
        client = boto3.client("bedrock-runtime", region_name=region)
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
        })
        response = client.invoke_model(modelId=model_id, body=body, contentType="application/json")
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]
    except Exception as e:
        error_msg = str(e)
        if "ResourceNotFoundException" in error_msg or "use case details" in error_msg:
            raise RuntimeError(
                f"Bedrock model access denied for {model_id}.\n"
                f"  Fix: Go to AWS Console → Bedrock → Model access → Request access for Anthropic models.\n"
                f"  See: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html\n"
                f"  Note: Access requests can take up to 15 minutes to propagate."
            )
        elif "ExpiredTokenException" in error_msg or "credentials" in error_msg.lower():
            raise RuntimeError(
                f"AWS credentials expired or invalid.\n"
                f"  Fix: Run 'aws sso login' or refresh your credentials.\n"
                f"  Current region: {region}"
            )
        elif "UnrecognizedClientException" in error_msg:
            raise RuntimeError(
                f"AWS credentials not recognized.\n"
                f"  Fix: Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, or run 'aws configure'."
            )
        else:
            raise RuntimeError(f"Bedrock call failed: {error_msg}")


def _call_ollama(prompt, model):
    """Call Ollama as judge."""
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
    })
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=body.encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read())
    return data["response"]


def call_api(prompt, options, context):
    """Promptfoo provider entry point. Cascades through available judge backends."""
    errors = []

    # 1. Try Bedrock if AWS is configured
    if _check_aws_credentials():
        try:
            output = _call_bedrock(prompt, options)
            return {"output": output}
        except RuntimeError as e:
            errors.append(f"Bedrock: {e}")
        except ImportError:
            errors.append(
                "Bedrock: boto3 not installed.\n"
                "  Fix: pip install boto3 (or uv pip install boto3)"
            )

    # 2. Try Ollama if available
    ollama_model = _check_ollama()
    if ollama_model:
        try:
            output = _call_ollama(prompt, ollama_model)
            return {"output": output}
        except Exception as e:
            errors.append(f"Ollama ({ollama_model}): {e}")

    # 3. Fail fast with actionable guidance
    if not errors:
        return {
            "error": (
                "No LLM judge available. Configure one of:\n"
                "  1. AWS Bedrock: Set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY env vars,\n"
                "     or run 'aws configure'. Then request Anthropic model access in Bedrock console.\n"
                "  2. Ollama: Install from https://ollama.com, then 'ollama pull mistral-nemo'\n"
            )
        }

    return {"error": "All judge providers failed:\n" + "\n".join(f"  - {e}" for e in errors)}
