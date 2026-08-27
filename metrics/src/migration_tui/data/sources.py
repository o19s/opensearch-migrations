"""Tailing sources for the tuple log: local file, S3 object, or a k8s pod.

All three expose the same tiny async interface (`poll()` returns newly
available bytes since the last call, or b"" if nothing new) so the dashboard
doesn't care which one is in play. Each source tracks its own byte offset
and only fetches the delta -- important for S3 and pod-exec sources where a
full re-read would be wasteful on a growing multi-MB log.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from migration_tui.config import LocalSourceConfig, PodSourceConfig, S3SourceConfig, TupleSourceConfig

logger = logging.getLogger(__name__)


class TupleSource(ABC):
    poll_interval_seconds: float

    @abstractmethod
    async def poll(self) -> bytes:
        """Return newly available bytes since the last call (b"" if none)."""

    async def close(self) -> None:  # pragma: no cover - default no-op
        return None


class LocalFileSource(TupleSource):
    """Tails a local file, à la `tail -f`. Handles the file not existing yet."""

    def __init__(self, cfg: LocalSourceConfig) -> None:
        self.path = Path(cfg.path)
        self.poll_interval_seconds = cfg.poll_interval_seconds
        self._offset = 0

    async def poll(self) -> bytes:
        if not self.path.exists():
            return b""

        def _read() -> bytes:
            with self.path.open("rb") as f:
                f.seek(self._offset)
                data = f.read()
                self._offset += len(data)
                return data

        return await asyncio.to_thread(_read)


class S3Source(TupleSource):
    """Tails an S3 object using ranged GETs so we only pay for new bytes.

    Migration Assistant replayers can be configured to write tuple logs to
    S3; this assumes the object is append-only (new bytes only appear at
    the end), which matches that behavior.
    """

    def __init__(self, cfg: S3SourceConfig) -> None:
        import boto3  # local import: keep boto3 optional for local-only users

        self.bucket = cfg.bucket
        self.key = cfg.key
        self.poll_interval_seconds = cfg.poll_interval_seconds
        self._offset = 0
        self._client = boto3.client("s3", region_name=cfg.region)

    async def poll(self) -> bytes:
        return await asyncio.to_thread(self._poll_sync)

    def _poll_sync(self) -> bytes:
        from botocore.exceptions import ClientError

        try:
            if self._offset == 0:
                response = self._client.get_object(Bucket=self.bucket, Key=self.key)
            else:
                response = self._client.get_object(
                    Bucket=self.bucket, Key=self.key, Range=f"bytes={self._offset}-"
                )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in ("InvalidRange", "NoSuchKey"):
                # Nothing new (or object not created yet).
                return b""
            raise

        data = response["Body"].read()
        self._offset += len(data)
        return data


class PodSource(TupleSource):
    """Tails a file inside a pod via `kubectl exec ... tail -c +N`.

    Deliberately avoids `kubectl cp` (not available in the replayer image
    per the pod's minimal shell) -- instead it shells out to `tail -c +N`
    to fetch only the bytes appended since the last poll.
    """

    def __init__(self, cfg: PodSourceConfig) -> None:
        self.cfg = cfg
        self.poll_interval_seconds = cfg.poll_interval_seconds
        self._offset = 0

    def _kubectl_args(self, *tail_args: str) -> list[str]:
        args = [self.cfg.kubectl_bin]
        if self.cfg.kube_context:
            args += ["--context", self.cfg.kube_context]
        args += ["exec", "-n", self.cfg.namespace, self.cfg.pod, "--"]
        args += list(tail_args)
        return args

    async def poll(self) -> bytes:
        # tail -c +N is 1-indexed ("start at byte N"); offset 0 -> +1.
        shell_cmd = f"tail -c +{self._offset + 1} {self.cfg.file_path} 2>/dev/null || true"
        args = self._kubectl_args("sh", "-c", shell_cmd)

        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.warning("pod tail failed (rc=%s): %s", proc.returncode, stderr.decode(errors="replace"))
            return b""

        self._offset += len(stdout)
        return stdout


def create_source(cfg: TupleSourceConfig) -> TupleSource:
    if cfg.kind == "local":
        return LocalFileSource(cfg.local)
    if cfg.kind == "s3":
        return S3Source(cfg.s3)
    if cfg.kind == "pod":
        return PodSource(cfg.pod)
    raise ValueError(f"Unknown tuple source kind: {cfg.kind!r}")
