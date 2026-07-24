# Multi-Tenants Support Scripts

## Environment setup

The provided scripts in this directory are tested against the test cluster charts using Solr 9.7.0.

When you want to test multi-tenancy for Solr, you may create and deploy a cluster as usual. It is recommended to change
the replicas count and configure the authentication to use basic auth, so that the scripts can also create configsets
(alternatively, comment out the part that creates a configset in the script and create one manually). If auth is not
enabled, you may run into errors because the scripts try to create a configset from a trusted baseConfigSet.

To enable auth, first create a secret with credentials of your choice:

```bash
kubectl create secret generic solr-auth-creds -n ma --from-literal=username=admin --from-literal=password=admin
```

Then, for more reliable results, consider reinstalling the helm chart via:

```bash
# Uninstall first
helm uninstall -n ma tc

# Then, from inside deployments/k8s/
helm install -n ma tc . -f valuesSolrSource.yaml --set solrSource.replicas=3 \
  --set solrSource.solrOptions.security.authenticationType=Basic \
  --set solrSource.solrOptions.security.basicAuthSecret=solr-auth-creds
```

And enabling auth from within a SolrCloud pod:

```bash
kubectl exec -it -n ma solr-source-solrcloud-0 --container=solrcloud-node --stdin=true --tty=true -- /bin/sh

bin/solr auth enable --type basicAuth --prompt true -z solr-source-solrcloud-zookeeper-0.solr-source-solrcloud-zookeeper-headless.ma.svc.cluster.local:2181/
```

## Create configsets and collections

To create a single configset and multiple collections from that configset, simply:

```bash
# port-forward a solr pod
kubectl -n ma port-forward svc/solr-source-solrcloud-headless 8983:8983

# then run the script
SORL_BASIC_AUTH=admin:admin ./populate_solrcloud.sh
```

Once the data is populated, you can use a workflow like this:

```json
{
  "sourceClusters": {
    "solr-source": {
      "endpoint": "http://solr-source-solrcloud-headless:8983",
      "allowInsecure": true,
      "version": "SOLR 9.7.0",
      "snapshotInfo": {
        "repos": {
          "localstack-s3": {
            "awsRegion": "us-east-2",
            "endpoint": "localstack://localstack.ma.svc.cluster.local:4566",
            "repoPathUri": "s3://solr-backups"
          }
        },
        "backups": {
          "solr-migration-snapshot": {
            "createSnapshotConfig": {},
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
      "fromSource": "solr-source",
      "toTarget": "target",
      "perSnapshotConfig": {
        "solr-migration-snapshot": [
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
  ]
}
```

Make sure that you have created a bucket before you submit the workflow with the name `solr-backups` in case you use the
test cluster with `valuesSolrSource.yaml`.

Once submitted, the workflow will create backups in that bucket under:

```
s3://[bucket]/[workflow-snapshot-identifier]/[collection-backup-name]/[collection]/
```

An example backup of a collection would look like this:

```
s3://solr-backups/solr-source_solr-migration-snapshot_1784817550/techproducts_tenant0/techproducts_tenant0/
```

## Scenario with SolrBackup CRD

When using a SolrBackup CRD, like `backup-simple.yaml` or `backup-recurring.yaml`, backups are generated
automatically by the solr-operator. You then have to point to the right backup directory by using in your workflow an
externally managed snapshot name:

```json lines
// instead of
"sourceClusters": {
  "solr-source": {
    //...
    "snapshotInfo": {
      //...
      "backups": {
        "solr-migration-snapshot": {
          "createSnapshotConfig": {},
          "repoName": "localstack-s3"
        }
      }
    }
  },
  //...
}
// this
"sourceClusters": {
  "solr-source": {
    //...
    "snapshotInfo": {
      //...
      "backups": {
        "solr-migration-snapshot": {
          "externallyManagedSnapshotName": "backup-simple",
          "repoName": "localstack-s3"
        }
      }
    }
  },
  //...
}
```
