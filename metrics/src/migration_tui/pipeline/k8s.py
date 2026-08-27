"""kubectl wrappers used by the pipeline steps.

Kept deliberately thin -- these just build argv lists and delegate to
shell.py. No cluster-specific assumptions beyond what's in config.py.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from migration_tui.config import K8sConfig
from migration_tui.pipeline.shell import BackgroundProcess, run_capture, run_streamed


def _base_args(cfg: K8sConfig) -> list[str]:
    args = [cfg.kubectl_bin]
    if cfg.kube_context:
        args += ["--context", cfg.kube_context]
    return args


async def run_kind_script(script_path: str) -> AsyncIterator[str]:
    async for line in run_streamed(["bash", script_path]):
        yield line


def port_forward(cfg: K8sConfig, target: str, local_port: int, remote_port: int) -> BackgroundProcess:
    """Returns a not-yet-started BackgroundProcess for `kubectl port-forward`."""

    args = _base_args(cfg) + [
        "port-forward",
        "-n",
        cfg.namespace,
        target,
        f"{local_port}:{remote_port}",
    ]
    return BackgroundProcess(command=args)


async def exec_pod(cfg: K8sConfig, pod: str, *command: str, input_text: str | None = None) -> str:
    """`kubectl exec <pod> -- <command...>`, optionally piping stdin (`-i`)."""

    args = _base_args(cfg) + ["exec", "-n", cfg.namespace]
    if input_text is not None:
        args.append("-i")
    args += [pod, "--", *command]
    return await run_capture(args, input_text=input_text)


async def cat_pod_file(cfg: K8sConfig, pod: str, path: str) -> str:
    """Read a whole file out of a pod without `kubectl cp` (image lacks it)."""

    return await exec_pod(cfg, pod, "cat", path)
