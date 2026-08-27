"""Thin async subprocess helpers used by every pipeline step.

Two shapes are needed:

- `run_streamed`: run a command to completion, yielding output lines as they
  arrive (used to feed the live pipeline log in the TUI).
- `BackgroundProcess`: start a long-running command (port-forwards) and keep
  a handle to it so a later step can terminate it cleanly.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class StepFailed(RuntimeError):
    def __init__(self, command: list[str], returncode: int, tail: str):
        self.command = command
        self.returncode = returncode
        self.tail = tail
        super().__init__(f"Command failed ({returncode}): {' '.join(command)}\n{tail}")


async def run_streamed(command: list[str], *, cwd: str | None = None) -> AsyncIterator[str]:
    """Run `command`, yielding each line of combined stdout/stderr as it arrives.

    Raises StepFailed if the process exits non-zero. Caller decides what to
    do with lines (e.g. append to a pipeline-log widget).
    """

    logger.info("running: %s", " ".join(command))

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    tail: list[str] = []
    assert process.stdout is not None

    async for raw_line in process.stdout:
        line = raw_line.decode(errors="replace").rstrip("\n")
        tail.append(line)
        if len(tail) > 40:
            tail.pop(0)
        yield line

    returncode = await process.wait()
    if returncode != 0:
        raise StepFailed(command, returncode, "\n".join(tail))


async def run_capture(command: list[str], *, cwd: str | None = None, input_text: str | None = None) -> str:
    """Run `command` to completion and return its stdout as text."""

    logger.info("running: %s", " ".join(command))

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=cwd,
        stdin=asyncio.subprocess.PIPE if input_text is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdin_bytes = input_text.encode() if input_text is not None else None
    stdout, stderr = await process.communicate(stdin_bytes)

    if process.returncode != 0:
        raise StepFailed(command, process.returncode or -1, stderr.decode(errors="replace"))

    return stdout.decode(errors="replace")


@dataclass
class BackgroundProcess:
    command: list[str]
    _process: asyncio.subprocess.Process | None = None

    async def start(self) -> None:
        logger.info("starting background process: %s", " ".join(self.command))
        self._process = await asyncio.create_subprocess_exec(
            *self.command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

    async def stop(self) -> None:
        if self._process is None or self._process.returncode is not None:
            return
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=5)
        except asyncio.TimeoutError:
            self._process.kill()
            await self._process.wait()

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.returncode is None


async def wait_for_port(host: str, port: int, *, timeout: float = 30.0, interval: float = 0.5) -> None:
    """Poll a TCP port until it accepts connections or timeout elapses."""

    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout

    while loop.time() < deadline:
        try:
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError:
            await asyncio.sleep(interval)

    raise TimeoutError(f"Port {host}:{port} did not become ready within {timeout}s")
