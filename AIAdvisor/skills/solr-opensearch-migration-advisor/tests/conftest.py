"""Shared fixtures and CLI options for the migration advisor test suite.

Every test run creates a timestamped session directory under
tests/artifacts/ and symlinks it as tests/artifacts/latest/.
Pytest junit XML, LLM response reports, and run metadata all land
in the same session directory.

Modes:
  --mode=test (default)  Artifacts stay local (gitignored).
  --mode=demo            Also copies human-readable reports to
                         tests/reports/ (tracked in git), commits
                         them, and prints the push command.
"""

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ARTIFACTS_ROOT = Path(__file__).resolve().parent / "artifacts"
REPORTS_ROOT = Path(__file__).resolve().parent / "reports"
STEERING_DIR = Path(__file__).resolve().parents[1] / "steering"
SKILL_ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    parser.addoption(
        "--extended",
        action="store_true",
        default=False,
        help=(
            "Include 'above and beyond' tests in test_deliverables.py. "
            "These go deeper than the AWS deliverable requirements."
        ),
    )
    parser.addoption(
        "--mode",
        default="test",
        choices=["test", "demo"],
        help=(
            "Run mode. 'test' keeps artifacts local (gitignored). "
            "'demo' also copies human-readable reports to tests/reports/ "
            "(tracked in git), commits them, and prints the push command."
        ),
    )
    parser.addoption(
        "--llm-backend",
        default="auto",
        choices=["ollama", "bedrock", "auto"],
        help=(
            "LLM backend for guidance-impact tests. "
            "'ollama' or 'bedrock' require that backend to be available (fail if not). "
            "'auto' tries bedrock then ollama, skips if neither is reachable."
        ),
    )
    parser.addoption(
        "--ollama-base-url",
        default=None,
        help="Ollama base URL (default: http://localhost:11434)",
    )
    parser.addoption(
        "--ollama-model",
        default=None,
        help="Ollama model name (default: llama3.2:latest)",
    )
    parser.addoption(
        "--bedrock-model-id",
        default=None,
        help="Bedrock model ID (default: anthropic.claude-3-haiku-20240307-v1:0)",
    )
    parser.addoption(
        "--bedrock-region",
        default=None,
        help="AWS region for Bedrock (default: from AWS_DEFAULT_REGION or us-east-1)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests marked @extended unless --extended is passed."""
    import pytest as _pytest
    if config.getoption("--extended"):
        return
    skip_extended = _pytest.mark.skip(
        reason="Extended test — run with --extended to include"
    )
    for item in items:
        if "extended" in item.keywords:
            item.add_marker(skip_extended)


# ── session artifact directory ───────────────────────────────────────────

def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _steering_hashes() -> dict[str, str]:
    """Return {filename: sha256[:12]} for every steering file."""
    result = {}
    if STEERING_DIR.is_dir():
        for path in sorted(STEERING_DIR.glob("*.md")):
            content = path.read_bytes()
            result[path.name] = hashlib.sha256(content).hexdigest()[:12]
    return result


def pytest_configure(config):
    """Create the session artifact directory and point latest/ at it.

    Also rewrite the junitxml path so pytest writes results into
    the session directory instead of a fixed location.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    session_dir = ARTIFACTS_ROOT / ts
    session_dir.mkdir(parents=True, exist_ok=True)

    # Store on config so fixtures can find it
    config._artifact_session_dir = session_dir
    config._artifact_timestamp = ts
    config._run_mode = config.getoption("--mode")

    # Rewrite junitxml into the session directory
    config.option.xmlpath = str(session_dir / "pytest-results.xml")

    # Update latest symlink
    latest = ARTIFACTS_ROOT / "latest"
    latest.unlink(missing_ok=True)
    latest.symlink_to(session_dir.name)

    # Write run metadata
    metadata = {
        "timestamp": ts,
        "git_sha": _git_sha(),
        "mode": config._run_mode,
        "steering_hashes": _steering_hashes(),
        "llm_backend": config.getoption("--llm-backend"),
        "ollama_model": config.getoption("--ollama-model"),
        "bedrock_model_id": config.getoption("--bedrock-model-id"),
    }
    (session_dir / "run-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )


def pytest_sessionfinish(session, exitstatus):
    """In demo mode, copy human-readable reports to the tracked
    tests/reports/ directory and commit them."""
    config = session.config
    if getattr(config, "_run_mode", "test") != "demo":
        return

    session_dir = config._artifact_session_dir
    ts = config._artifact_timestamp

    # Find all .md reports in the session directory
    reports = list(session_dir.glob("*.md"))
    if not reports:
        return

    # Copy to tracked reports directory
    report_dir = REPORTS_ROOT / ts
    report_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for report in reports:
        dest = report_dir / report.name
        shutil.copy2(report, dest)
        copied.append(dest)

    # Also copy run metadata for context
    metadata_src = session_dir / "run-metadata.json"
    if metadata_src.exists():
        shutil.copy2(metadata_src, report_dir / "run-metadata.json")

    # Update latest symlink in reports/
    latest = REPORTS_ROOT / "latest"
    latest.unlink(missing_ok=True)
    latest.symlink_to(ts)

    # Git commit
    try:
        # Stage the reports directory
        subprocess.run(
            ["git", "add", str(report_dir), str(latest)],
            cwd=str(SKILL_ROOT),
            check=True,
            capture_output=True,
        )
        commit_msg = f"Demo report: guidance impact test results ({ts})"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(SKILL_ROOT),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        # Commit may fail if nothing changed or git is in a weird state
        pass

    # Print next steps
    print()
    print("=" * 60)
    print("DEMO MODE: Report committed to tests/reports/")
    print(f"  {report_dir}/")
    for f in copied:
        print(f"    {f.name}")
    print()
    print("To share with the team:")
    print("  git push")
    print("=" * 60)
