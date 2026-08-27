1. Run `deployment/k8s/kindTesting.sh` and wait for its completion
2. Port-forward ElasticSearch cluster with `kubectl port-forward -n ma elasticsearch-master-0 9200:9200`
3. Run `./populate_data.sh` to create index and add data
4. Stop port-forwarding
5. Enter the migration-console with `kubectl exec --stdin --tty -n ma migration-console-0 -- /bin/bash`
6. Create workflow with following configuration (`workflow configure edit`):
    ```json
    {
      "sourceClusters": {
        "es-source": {
          "endpoint": "https://elasticsearch-master-headless:9200",
          "allowInsecure": true,
          "version": "ES 7.10",
          "authConfig": {
            "basic": { "secretName": "source-creds" }
          },
          "snapshotInfo": {
            "repos": {
              "localstack-s3": {
                "awsRegion": "us-east-2",
                "endpoint": "localstack://localstack.ma.svc.cluster.local:4566",
                "repoPathUri": "s3://es-snapshots"
              }
            },
            "snapshots": {
              "es-migration-snapshot": {
                "config": {
                  "createSnapshotConfig": {}
                },
                "repoName": "localstack-s3"
              }
            }
          }
        }
      },
      "targetClusters": {
        "target": {
          "endpoint": "https://opensearch-cluster-master:9200",
          "allowInsecure": true,
          "authConfig": {
            "basic": { "secretName": "target-creds" }
          }
        }
      },
      "snapshotMigrationConfigs": [
        {
          "fromSource": "es-source",
          "toTarget": "target",
          "perSnapshotConfig": {
            "es-migration-snapshot": [
              {
                "metadataMigrationConfig": {
                  "skipEvaluateApproval": true,
                  "skipMigrateApproval": true
                },
                "documentBackfillConfig": {
                  "podReplicas": 4
                }
              }
            ]
          }
        }
      ],
      "kafkaClusterConfiguration": {
        "main-kafka": {
          "autoCreate": {}
        }
      },
      "traffic": {
        "proxies": {
          "main-proxy": {
            "source": "es-source",
            "kafka": "main-kafka",
            "kafkaTopic": "replaytraffic",
            "skipApproval": true,
            "proxyConfig": {
              "serviceType": "ClusterIP",
              "listenPort": 9200
            }
          }
        },
        "replayers": {
          "main-replayer": {
            "fromCapturedTraffic": "main-proxy",
            "toTarget": "target",
            "dependsOnSnapshotMigrations": [
              {
                "source": "es-source",
                "snapshot": "es-migration-snapshot"
              }
            ],
            "replayerConfig": {
              "useLocalStack": true
            }
          }
        }
      }
    }
    ```
7. Submit workflow with `workflow submit` and wait for completion (may require approval)
8. Port-forward the proxy via `kubectl port-forward -n ma svc/main-proxy 9200:9200`
9. Run the queries with `query_data.sh`
10. Copy the logs from the replayer and run the scripts
    - comparison_matrix.py [output.log]
    - comparison_matrix_alt.py [output.log]
    - query_diff_visualization.py [output.log]
