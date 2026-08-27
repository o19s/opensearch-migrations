"""Central configuration for the migration-tui pipeline and dashboard.

Everything is overridable via CLI flags or environment variables (see __main__.py)
so the tool isn't hard-wired to one cluster's naming.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import subprocess

def _default_kind_script() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip()) / "deployment" / "k8s" / "kindTesting.sh"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path("deployment/k8s/kindTesting.sh")  # fallback outside a git checkout

@dataclass(slots=True)
class K8sConfig:
    namespace: str = "ma"
    kind_script: Path = field(default_factory=_default_kind_script)

    elasticsearch_service: str = "elasticsearch-master-0"
    elasticsearch_local_port: int = 9200
    elasticsearch_remote_port: int = 9200

    migration_console_pod: str = "migration-console-0"

    proxy_service: str = "svc/main-proxy"
    proxy_local_port: int = 9200
    proxy_remote_port: int = 9200

    # kubectl binary/context overrides, useful for multi-cluster setups.
    kubectl_bin: str = "kubectl"
    kube_context: str = None


@dataclass(slots=True)
class OpenSearchConfig:
    index_name: str = "products"
    index_file: Path = Path("sample-data/products_index.json")
    bulk_file: Path = Path("sample-data/products.ndjson")
    username: str = "admin"
    password: str = "admin"
    verify_tls: bool = False


@dataclass(slots=True)
class WorkflowConfig:
    """Fields used to render the migration-assistant workflow JSON."""

    source_endpoint: str = "https://elasticsearch-master-headless:9200"
    source_version: str = "ES 7.10"
    source_creds_secret: str = "source-creds"

    target_endpoint: str = "https://opensearch-cluster-master:9200"
    target_creds_secret: str = "target-creds"

    s3_repo_name: str = "localstack-s3"
    s3_aws_region: str = "us-east-2"
    s3_endpoint: str = "localstack://localstack.ma.svc.cluster.local:4566"
    s3_bucket: str = "es-snapshots"
    s3_repo_path_uri: str = f"s3://{s3_bucket}"

    snapshot_name: str = "es-migration-snapshot"
    doc_backfill_pod_replicas: int = 4

    kafka_cluster_name: str = "main-kafka"
    kafka_topic: str = "replaytraffic"

    proxy_name: str = "main-proxy"
    replayer_name: str = "main-replayer"

    skip_approvals: bool = True


@dataclass(slots=True)
class S3SourceConfig:
    bucket: str = ""
    key: str = ""
    region: str = None
    poll_interval_seconds: float = 3.0


@dataclass(slots=True)
class PodSourceConfig:
    pod: str = "main-replayer-0"
    namespace: str = "ma"
    file_path: str = "/data/tuples.log"
    poll_interval_seconds: float = 3.0
    kubectl_bin: str = "kubectl"
    kube_context: str = None


@dataclass(slots=True)
class LocalSourceConfig:
    path: Path = Path("output.log")
    poll_interval_seconds: float = 1.0


@dataclass(slots=True)
class TupleSourceConfig:
    """Exactly one of these should be populated; `kind` selects which."""

    kind: str = "local"  # "local" | "s3" | "pod"
    local: LocalSourceConfig = field(default_factory=LocalSourceConfig)
    s3: S3SourceConfig = field(default_factory=S3SourceConfig)
    pod: PodSourceConfig = field(default_factory=PodSourceConfig)


@dataclass(slots=True)
class AppConfig:
    k8s: K8sConfig = field(default_factory=K8sConfig)
    opensearch: OpenSearchConfig = field(default_factory=OpenSearchConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    source: TupleSourceConfig = field(default_factory=TupleSourceConfig)

    # RBO persistence parameter (higher = more weight on top ranks).
    rbo_p: float = 0.9

    # Classification thresholds, consolidated from the original scripts.
    jaccard_acceptable: float = 0.90
    rbo_acceptable: float = 0.90
    max_avg_rank_shift: float = 1.0
    index_count_threshold_percent: float = 0.01
    index_count_threshold_absolute: int = 100
    agg_threshold_percent: float = 0.01
    agg_threshold_absolute: float = 0.0
