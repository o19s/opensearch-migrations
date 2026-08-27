"""Renders and submits the Migration Assistant workflow config."""

from __future__ import annotations

import json
import re
import asyncio

from migration_tui.config import K8sConfig, WorkflowConfig
from migration_tui.pipeline.k8s import exec_pod


async def create_basic_auth_secret(
        k8s: K8sConfig,
        secret_name: str,
        username: str = "admin",
        password: str = "admin",
) -> str:
    secret_yaml = await exec_pod(
        k8s,
        k8s.migration_console_pod,
        "kubectl",
        "create",
        "secret",
        "generic",
        secret_name,
        f"--from-literal=username={username}",
        f"--from-literal=password={password}",
        "--dry-run=client",
        "-o",
        "yaml",
    )

    return await exec_pod(
        k8s,
        k8s.migration_console_pod,
        "kubectl",
        "apply",
        "-f",
        "-",
        input_text=secret_yaml,
    )


async def create_s3_bucket(k8s: K8sConfig, bucket_name: str) -> str:
    return await exec_pod(
        k8s,
        k8s.localstack_pod,
        "awslocal",
        "s3api",
        "create-bucket",
        "--bucket",
        bucket_name,
    )


def render(cfg: WorkflowConfig) -> dict:
    return {
        "skipApprovals": cfg.skip_approvals,
        "sourceClusters": {
            "es-source": {
                "endpoint": cfg.source_endpoint,
                "allowInsecure": True,
                "version": cfg.source_version,
                "authConfig": {"basic": {"secretName": cfg.source_creds_secret}},
                "snapshotInfo": {
                    "repos": {
                        cfg.s3_repo_name: {
                            "awsRegion": cfg.s3_aws_region,
                            "endpoint": cfg.s3_endpoint,
                            "repoPathUri": cfg.s3_repo_path_uri,
                        }
                    },
                    "snapshots": {
                        cfg.snapshot_name: {
                            "config": {"createSnapshotConfig": {}},
                            "repoName": cfg.s3_repo_name,
                        }
                    },
                },
            }
        },
        "targetClusters": {
            "target": {
                "endpoint": cfg.target_endpoint,
                "allowInsecure": True,
                "authConfig": {"basic": {"secretName": cfg.target_creds_secret}},
            }
        },
        "snapshotMigrationConfigs": [
            {
                "fromSource": "es-source",
                "toTarget": "target",
                "perSnapshotConfig": {
                    cfg.snapshot_name: [
                        {
                            "metadataMigrationConfig": {
                                "skipEvaluateApproval": cfg.skip_approvals,
                                "skipMigrateApproval": cfg.skip_approvals,
                            },
                            "documentBackfillConfig": {"podReplicas": cfg.doc_backfill_pod_replicas},
                        }
                    ]
                },
            }
        ],
        "kafkaClusterConfiguration": {cfg.kafka_cluster_name: {"autoCreate": {}}},
        "traffic": {
            "proxies": {
                cfg.proxy_name: {
                    "source": "es-source",
                    "kafka": cfg.kafka_cluster_name,
                    "kafkaTopic": cfg.kafka_topic,
                    "skipApproval": cfg.skip_approvals,
                    "proxyConfig": {"serviceType": "ClusterIP", "listenPort": 9200},
                }
            },
            "replayers": {
                cfg.replayer_name: {
                    "fromCapturedTraffic": cfg.proxy_name,
                    "toTarget": "target",
                    "dependsOnSnapshotMigrations": [
                        {"source": "es-source", "snapshot": cfg.snapshot_name}
                    ],
                    "replayerConfig": {"useLocalStack": True},
                }
            },
        },
    }


async def configure_workflow(k8s: K8sConfig, workflow: WorkflowConfig) -> str:
    payload = json.dumps(render(workflow), indent=2)
    return await exec_pod(
        k8s, k8s.migration_console_pod, "workflow", "configure", "edit", "--stdin", input_text=payload
    )


async def submit_workflow(k8s: K8sConfig) -> str:
    return await exec_pod(k8s, k8s.migration_console_pod, "workflow", "submit")


async def workflow_status(k8s: K8sConfig) -> str:
    return await exec_pod(k8s, k8s.migration_console_pod, "workflow", "status")


async def wait_for_workflow(
        k8s: K8sConfig,
        *,
        poll_interval: float = 10.0,
        timeout: float = None,
) -> str:
    elapsed = 0.0

    while True:
        status = await workflow_status(k8s)

        match = re.search(r"^\s*Phase:\s*(\S+)", status, re.MULTILINE)

        if not match:
            raise RuntimeError(
                f"Could not determine workflow phase from status:\n{status}"
            )

        phase = match.group(1)

        if phase == "Succeeded":
            return status

        if phase in {"Failed", "Error"}:
            raise RuntimeError(
                f"Migration workflow failed (phase={phase}):\n{status}"
            )

        if timeout is not None and elapsed >= timeout:
            raise TimeoutError(
                f"Migration workflow did not complete within "
                f"{timeout} seconds.\nLast status:\n{status}"
            )

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval


def workflow_has_failed_step(status: str) -> bool:
    return "(Failed)" in status
