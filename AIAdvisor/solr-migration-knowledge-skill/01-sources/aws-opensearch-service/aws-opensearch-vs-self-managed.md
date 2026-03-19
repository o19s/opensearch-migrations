# AWS OpenSearch Service vs Self-Managed OpenSearch

## Executive Summary

AWS OpenSearch Service provides a fully managed search-as-a-service offering, handling operational burden in exchange for constraints on configuration and lower-level control. For most migration scenarios from self-managed Solr or Elasticsearch, AWS OpenSearch Service is the appropriate target—the operational overhead of self-managed OpenSearch in a hybrid cloud environment rarely justifies the additional flexibility.

---

## What AWS Manages for You

### Patching and Upgrades
- **Automated security patching**: AWS applies JVM and OS-level security patches without downtime (via blue-green deployment)
- **Version upgrades**: OpenSearch releases are deployed to AWS typically 1-2 releases behind the open-source schedule; upgrades are offered as managed operations
- **Blue-green deployments**: AWS automatically creates a parallel cluster, migrates data, and cuts traffic over (happens behind your domain endpoint)
- **Zero-downtime patching**: Even critical patches do not require manual intervention or application downtime
- **Automatic rollback**: If an upgrade fails, AWS automatically restores your domain to the previous version

### Operational Infrastructure
- **Multi-AZ deployment**: Automatic replica placement across availability zones (configurable as 2-AZ or 3-AZ)
- **Node failure recovery**: Failed nodes are automatically replaced; no manual remediation required
- **Disk space management**: Storage is elastically provisioned; monitoring and alerts warn before exhaustion
- **Cluster state recovery**: ZooKeeper-equivalent state management (cluster metadata) is handled by AWS
- **Shard allocation and rebalancing**: AWS manages the shard allocation policy and handles node joins/leaves
- **Snapshot infrastructure**: Automated backups can be sent to S3 (with configurable retention and frequency)

### Backup and Disaster Recovery
- **Automated snapshots**: Daily snapshots (configurable) stored in AWS-managed S3 buckets
- **Cross-region snapshots**: Automated replication of snapshots to a secondary region
- **Restore-to-point-in-time**: Ability to restore to any snapshot without downtime (via cluster creation)
- **Cross-account snapshot restore**: Snapshots can be shared and restored to different AWS accounts

### Monitoring and Observability
- **CloudWatch integration**: Metrics for cluster health, node count, indexing rate, search latency, JVM heap
- **Application logs delivery**: Slow query logs, application logs shipped to CloudWatch Logs or Kinesis
- **AWS X-Ray integration**: Request tracing for application calls to OpenSearch

---

## What You Lose: Self-Managed Trade-offs

### Direct Host Access
- **No SSH to nodes**: You cannot SSH into cluster nodes to inspect files, debug, or run custom commands
- **No custom kernel tuning**: kernel parameters, ulimits, swap settings cannot be modified
- **No external file mounting**: Dependency on plugins must be installed via OpenSearch configuration (not manual file placement)

### Plugin Installation and Restrictions
- **Pre-approved plugins only**: AWS maintains a list of verified plugins; custom plugins are not supported
- **No plugin compilation or patching**: You cannot modify plugin source code or apply local patches
- **Limited plugin selection**: Some specialized Solr features (e.g., custom update processors, UIMA plugin) have no equivalent in the approved OpenSearch plugin list
- **Plugin lag**: Plugin versions are often behind open-source releases

### Advanced Configuration Constraints
- **Limited elasticsearch.yml parameters**: Many low-level JVM, network, and memory parameters are not exposed
- **No custom analyzers via config files**: Custom analyzers must be created via Index API at index creation time (acceptable but less flexible than Solr)
- **No fine-tuning of replica placement**: Shard allocation is constrained to AWS-managed strategies
- **Query cache, filter cache sizing**: Cache parameters are opaque and tied to node size (not independently tunable)

### Cost and Metering
- **Pay for reserved capacity**: You provision minimum node counts and types; you pay whether or not capacity is fully utilized
- **No overcommit or burst capacity**: Unlike EC2, there is no "spare capacity" available at reduced rates
- **Data transfer egress**: Large scan-and-export operations incur cross-region or cross-AZ egress charges

---

## Cost Model Deep Dive

### Instance Pricing
**AWS charges per node-hour for each data node, master node, and warm/cold tier node.**

Current generation (2024) pricing examples (US East 1):
- **r6g.xlarge.elasticsearch** (8 vCPU, 32 GB RAM): ~$0.31/hour (~$226/month)
- **r6g.2xlarge.elasticsearch** (8 vCPU, 64 GB RAM): ~$0.62/hour (~$453/month)
- **m6g.xlarge.elasticsearch** (4 vCPU, 16 GB RAM): ~$0.15/hour (~$110/month)
- **Dedicated master node (m6g.xlarge)**: ~$0.15/hour (required when >30 nodes or for multi-AZ 3-AZ)

### Storage Pricing
- **EBS gp3 storage**: ~$0.08 per GB-month (or reserved at ~$0.05/GB-month for 1-year commitment)
- **Warm tier storage**: Same as primary storage (EBS)
- **UltraWarm/cold tier**: S3-backed storage at ~$0.023 per GB-month (for data older than configurable period, e.g., 90+ days)

### Typical Cost Patterns

**Small deployment (single-node, development)**
- 1x r6g.xlarge node: $226/month
- 500 GB storage: $40/month
- **Total: ~$266/month**

**Medium deployment (3-node multi-AZ, production)**
- 3x r6g.xlarge data nodes: $678/month
- 1x m6g.large master node: ~$110/month (not always required until >10 nodes)
- 2 TB storage (1 TB primary + 1 TB replica): $160/month
- **Total: ~$948/month**

**Large deployment with warm tier (time-series)**
- 5x r6g.xlarge primary (hot) nodes: $1,155/month
- 2x r6g.xlarge warm nodes: $465/month (UltraWarm S3-backed at $0.023/GB-month is cheaper, see below)
- 1x m6g.xlarge dedicated master: $110/month
- 10 TB hot storage: $800/month
- 50 TB warm storage (S3): $1,150/month
- **Total: ~$3,680/month**

### Cost Optimization Strategies
1. **Use warm/cold tiers for time-series data**: Transition data older than 30-90 days to warm tier (cheaper storage, slower queries)
2. **Right-size instance types**: Graviton2 (r6g, m6g) are 20% cheaper than x86 equivalents; c6g suitable for compute-intensive queries
3. **Reserve capacity**: AWS offers 1-year and 3-year reserved capacity (discount ~25-40% vs on-demand)
4. **Use OpenSearch Serverless for unpredictable workloads**: No pre-provisioned nodes; pay per OCU (OpenSearch Compute Unit)
5. **Consolidate indices**: Fewer indices = fewer shards = lower memory overhead
6. **Shared tenancy across teams**: Namespace isolation via FGAC rather than separate domains

---

## Version Lag and Release Cycle

### AWS Release Schedule
- **OpenSearch open-source versions**: 2-3 releases per year (2.11, 2.12, 2.13, etc.)
- **AWS OpenSearch Service deployments**: Typically 4-8 weeks lag; AWS validates, tests, and blue-green prepares before offering upgrades
- **Current supported versions**: AWS typically supports the last 3-4 versions; EOL versions are force-upgraded with notice
- **Version compatibility**: AWS maintains API compatibility across minor versions; major version upgrades (1.x → 2.x) require explicit opt-in

### Implications for Migration
- Plan to be on AWS versions, not the absolute latest open-source
- Security fixes may lag by 2-4 weeks; critical CVEs are patched faster
- Feature adoption is delayed; bleeding-edge features are not immediately available
- Cluster upgrades are mandatory on a schedule; plan for SLA windows

---

## OpenSearch Serverless vs Provisioned Clusters

### OpenSearch Serverless (Preferred for New Workloads)

**Pricing Model**: Pay per OpenSearch Compute Unit (OCU) per hour
- 1 OCU ≈ 2 vCPU, 12 GB RAM, scaled transparently
- **Cost**: ~$0.30 per OCU-hour (~$219/OCU-month)
- **Minimum**: 4 OCUs (2 for indexing, 2 for search if separate collections)

**Strengths**
- **No capacity planning**: Auto-scales as workload increases; pay for actual usage
- **Simpler operations**: No node management, no master node decisions
- **Cost efficiency for variable workloads**: If workload ranges 2x-10x, serverless typically wins
- **Faster provisioning**: Seconds to create a collection, vs minutes/hours for provisioned clusters
- **Built-in isolation**: Collections are isolated; noisy neighbors are impossible

**Weaknesses**
- **Limited plugin support**: Only core OpenSearch plugins supported (no Anomaly Detection, ILM, etc.)
- **No advanced config**: Analyzers and settings are more restricted
- **Indexing throughput caps**: Aggressive rate-limiting if you exceed provisioned capacity; backoff required
- **VPC endpoint only**: No public endpoint option
- **Query latency slightly higher**: ~10-20% higher p99 due to multi-tenant infrastructure

**When to Use Serverless**
- Indexing throughput < 10K docs/sec
- Search throughput < 1K queries/sec
- Data volume < 100 GB
- Workload is bursty or unpredictable
- Cost predictability is lower priority than operational simplicity
- Migration from Solr with unknown scale

### Provisioned Clusters (Legacy, Still Appropriate for High Throughput)

**Strengths**
- **Predictable performance**: No rate-limiting; full control over shard count and placement
- **High throughput**: Can sustain 100K+ docs/sec with proper configuration
- **Full feature support**: All plugins, all configuration options
- **Lower per-unit cost at scale**: Fixed costs amortize better at 20+ TB and high QPS
- **Multi-AZ and 3-AZ**: Better HA, cross-region failover

**Weaknesses**
- **Capacity planning required**: Over-provisioning wastes money; under-provisioning causes outages
- **Minimum node count**: Even a tiny deployment costs 3 nodes (multi-AZ)
- **Idle cost**: You pay for capacity even during off-peak hours
- **Slower to scale**: Adding nodes takes 10-30 minutes, depending on data volume

**When to Use Provisioned**
- Indexing throughput > 50K docs/sec
- Data volume > 500 GB
- Stable, predictable workload (logs, metrics, analytics)
- Require multi-region failover
- Cost per GB is lower at high scale

---

## Blue-Green Deployments for Version Upgrades

### How AWS Manages Upgrades Transparently

1. **Trigger**: AWS initiates an upgrade (user-initiated or auto-upgrade by deadline)
2. **Blue cluster**: Your current production cluster (the "blue" environment)
3. **Green cluster**: AWS spins up a new cluster with the target version, seeds it with your current indices
4. **Validation**: AWS waits for shard allocation and replica sync (typically 10-30 minutes)
5. **DNS switchover**: Your domain endpoint DNS record switches from blue to green (transparent to clients)
6. **Cleanup**: Old blue cluster is retained for ~24 hours in case rollback is needed
7. **Automatic rollback**: If health checks fail, AWS automatically reverts to blue

**Key advantages**
- Zero client downtime (DNS TTL is 60 seconds; connection pooling in clients allows graceful failover)
- Zero index downtime; all indices remain searchable throughout
- Network interruptions are brief (~1-5 seconds) for connection handoff
- Rollback is automatic if issues detected within the validation window

**Caveats**
- Temporary disk space consumption doubles during upgrade (briefly)
- JVM GC patterns may change (new JVM versions sometimes behave differently)
- Application connection pools should have short timeout, allow reconnection (Spring Boot default is usually fine)

---

## Ultra-Warm and Cold Tiers: Time-Series Cost Optimization

### Problem: Time-Series Data Growth
- **Log and metrics workloads**: Data grows linearly; 1 year of daily logs ≈ 365+ indices
- **Hot-to-cold pattern**: Recent data (1-7 days) queried heavily; older data queried rarely
- **Storage dominates cost**: 1 PB of EBS storage at $0.08/GB-month = $80K/month

### Ultra-Warm Tier Solution
- **Tiered storage**: Data transitioned to warm tier lives on S3 (cheaper) but remains searchable
- **S3 cost**: ~$0.023/GB-month (vs $0.08/GB-month for EBS)
- **Query performance**: Slightly slower (100-500ms overhead per warm shard) but acceptable for historical queries
- **Transition**: Automatic via Index State Management (ISM) policies or manual rollover

**ISM Policy Example** (transition indices > 30 days to warm)
```json
{
  "policy": "log_lifecycle",
  "states": [
    {
      "name": "hot",
      "transitions": [
        {
          "transition": {
            "days": 30,
            "state": "warm"
          }
        }
      ]
    },
    {
      "name": "warm",
      "actions": [
        {
          "warm_transition": {}
        }
      ]
    }
  ]
}
```

### Cold Tier Solution
- **Snapshot-based**: Indices are snapshotted and stored in S3 (searchable snapshots)
- **Cost**: Pay only for S3 storage (~$0.023/GB-month)
- **Query performance**: Slower still (seconds) but acceptable for compliance/legal hold queries
- **Use case**: Data older than 90-180 days

### Typical Time-Series Architecture
```
Hot (0-7 days):       5x r6g.xlarge, EBS storage, ~$1,200/month
Warm (8-90 days):     2x r6g.xlarge, S3-backed, ~$400/month
Cold (>90 days):      Snapshots in S3, ~$50/month per 1 TB
```

For a daily-indices workload (1 GB/day), 1 year of data:
- **Hot tier**: 7 GB = $0.56/month
- **Warm tier**: 83 GB = $1.91/month
- **Cold tier**: 275 GB = $6.33/month
- **Total**: ~$9/month (vs $22/month if all on EBS)

---

## Instance Types: Current Generation Recommendations

### Graviton2-Based (Preferred)

| Type | vCPU | RAM | Use Case | Hourly Cost |
|------|------|-----|----------|-------------|
| **r6g.large** | 2 | 16 GB | Small/dev, <50 GB data | $0.077 |
| **r6g.xlarge** | 4 | 32 GB | Medium, 50-500 GB data | $0.154 |
| **r6g.2xlarge** | 8 | 64 GB | Large, 500 GB-2 TB data | $0.309 |
| **m6g.large** | 2 | 8 GB | Master node (cheap) | $0.077 |
| **m6g.xlarge** | 4 | 16 GB | Master node (standard) | $0.154 |
| **c6g.xlarge** | 4 | 8 GB | Compute-heavy queries | $0.136 |

**Why Graviton2?**
- 20% cheaper than Intel equivalents (x2ieE)
- Comparable performance for indexing; sometimes faster for search (cache efficiency)
- AWS strategic direction; best support and optimization

### x86-Based (Still Supported)

| Type | vCPU | RAM | Hourly Cost |
|------|------|-----|-------------|
| **r7g.xlarge** (Intel, latest) | 4 | 32 GB | $0.198 |
| **r5.xlarge** (Intel, older) | 4 | 32 GB | $0.252 |

**Use x86 only if**
- Existing workload is x86-optimized (rare for OpenSearch)
- Graviton instance is not available in your region

### Ultra-Warm Tier Nodes
- **Fixed: ultrawarm.xlplus.opensearch**: S3-backed storage tier, no choice required
- **Sizing**: Start with 2 nodes; scale by monitoring search latency to warm indices

---

## Multi-AZ and HA Design

### 2-AZ Deployment (Recommended for Most)

**Requirements**
- Minimum 3 data nodes (1 shard + 2 replicas, distributed across 2 AZs)
- No dedicated master required (unless 10+ data nodes)

**Topology**
```
AZ-1: 2 data nodes
AZ-2: 1 data node
(Or 2-2 if even distribution desired, but 2-1 is cost-optimized)
```

**Behavior**
- Surviving AZ has at least 1 replica of every shard
- Full search and indexing capability if one AZ goes down
- Cross-AZ replication latency: <10 ms in AWS regions

**Cost**: 3x node cost (no discount for HA)

### 3-AZ Deployment (High-Availability Premium)

**Requirements**
- Minimum 3 data nodes (can be 1 per AZ or 2-1-0 distribution)
- Dedicated master node required (1 m6g.xlarge minimum; typically 3 for HA)
- 5+ data nodes recommended for true HA (2 per AZ + 1 "tie-breaker")

**Topology** (Ideal for 5+ nodes)
```
AZ-1: 2 data nodes
AZ-2: 2 data nodes
AZ-3: 1 data node
3x m6g.xlarge master nodes (distributed across AZs)
```

**Behavior**
- Can survive failure of 1 entire AZ with zero data loss
- Master quorum ensures consistent cluster state (3 masters = majority if 1 fails)
- Cross-AZ replication latency: <10-50 ms (depends on region)

**Cost**: 3x data node + 3x master node (cluster cost increased ~30%)

**When to Use 3-AZ**
- Production critical system (e.g., real-time alerting on logs)
- SLA requires 99.99% uptime
- Disaster recovery RTO < 1 minute
- Data loss is intolerable (financial records, compliance logs)

**When 2-AZ is Sufficient**
- SLA is 99.9% uptime (4.3 hours downtime/year)
- Recovery time of 10-30 minutes acceptable
- Development, staging, or secondary clusters

### Dedicated Master Nodes

**When Required**
- Data nodes count > 10 (cluster metadata management becomes bottleneck)
- 3-AZ deployment (ensures quorum with odd count)

**When Recommended (But Not Required)**
- Data node scale > 30 nodes (separates operational burden)
- High write throughput (>100K docs/sec) combined with high query load

**Sizing**
- **m6g.large**: 2-8 data nodes, light workload
- **m6g.xlarge**: 8-30 data nodes, moderate workload
- **m6g.2xlarge**: 30+ data nodes, heavy workload
- **Quantity**: 1 (risky), 3 (recommended), 5 (for very large clusters)

**Cost**
- 3x m6g.xlarge masters: ~$330/month
- Not always necessary; avoidable for < 20 node clusters if acceptable to include master on data nodes

---

## VPC Deployment: Security and Connectivity

### VPC Endpoint (Recommended)

**What it is**
- Private DNS endpoint within your VPC (e.g., `my-domain-vpc.us-east-1.es.amazonaws.com`)
- OpenSearch Service nodes are attached to your VPC subnets; no public internet IP
- Access only from EC2/ECS/Lambda in the VPC or via VPN/direct connect

**Security Benefits**
- No internet-facing endpoint; eliminates 95% of attack surface
- All traffic stays within AWS network
- VPC flow logs capture all traffic (valuable for security audit)
- CloudFlare DDoS protection not needed (AWS network-level protection)

**Setup**
1. Choose VPC and subnets (minimum 2 subnets if multi-AZ; 1 per AZ)
2. Assign security group (controls inbound from app tier)
3. Enable IAM access policy or internal user database

**Connectivity**
- Same VPC: Application can reach OpenSearch via DNS
- Different VPC: VPC peering or PrivateLink (NAT gateway adds ~$32/month)
- On-premises: VPN or Direct Connect required (adds latency, ~5-50 ms)
- Multi-account: Resource-based policy + STS or cross-account role assumption

### Public Endpoint (Legacy, Discouraged)

**When used**: Simplicity, developers accessing from unsecured networks
**Drawback**: Exposed to internet scanning, brute-force attacks, accidental misconfiguration
**Recommendation**: Use only for development/learning; never production

---

## Fine-Grained Access Control (FGAC): Users, Roles, Policies

### Identity Sources

#### 1. IAM Roles (Preferred for AWS-Native Apps)
- **Who**: EC2, ECS, Lambda, RDS, any AWS service with an IAM role
- **How**: Service assumes role → role has permission to access OpenSearch → request signed with SigV4
- **Setup**: Minimal; just attach policy to role
- **Pros**: Works seamlessly; no secrets management
- **Cons**: Only works for AWS services; not for external users or legacy apps

**Example IAM Policy**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "es:ESHttpGet",
        "es:ESHttpPost",
        "es:ESHttpPut"
      ],
      "Resource": "arn:aws:es:us-east-1:123456789012:domain/my-domain/*"
    }
  ]
}
```

#### 2. Internal User Database (Okta/Active Directory-like)
- **Who**: End users, developers, external partners
- **How**: Create users in OpenSearch; manage passwords and RBAC internally
- **Setup**: Create users via API or Dashboards UI
- **Pros**: Fine-grained per-index and per-API access; works for external users
- **Cons**: Password management overhead; no SSO integration (except via proxy)

**Example User Creation**
```bash
curl -X PUT "https://domain-vpc:9200/_plugins/_security/api/users/john" \
  -H "Content-Type: application/json" \
  -d '{"password": "SecurePassword123", "backend_roles": ["analyst"]}'
```

#### 3. SAML Federation (SSO, Okta/Azure AD)
- **Who**: Corporate users with existing SSO directory
- **How**: OpenSearch redirects to SAML IdP (Okta, Azure AD); users login once, get federated session
- **Setup**: Configure SAML entity ID, SSO URL, X.509 certificate in OpenSearch
- **Pros**: No password management; centralized identity; compliance-friendly
- **Cons**: Only works for Dashboards UI access; API access still requires API key

**Typical Flow**
1. User opens OpenSearch Dashboards
2. Redirect to Okta login page
3. User authenticates
4. Okta POST SAML assertion back to OpenSearch
5. OpenSearch creates session; user logged in

#### 4. OIDC Federation (Modern Alternative to SAML)
- **Who**: Modern apps using OAuth 2.0 / OIDC
- **How**: Similar to SAML but uses modern JWT tokens instead of XML
- **Pros**: Easier integration with cloud-native apps; better developer experience
- **Cons**: Still limited to Dashboards in AWS OpenSearch (raw API requires API key)

---

### Role and Policy Model

**Hierarchy**
```
User (internal user, IAM role, or federated identity)
  └─ Backend Role (e.g., "analyst", "admin", "read-only")
    └─ Permission (Action + Resource)
      ├─ Action: (indices:read, indices:create, admin:*)
      ├─ Resource: ("my-index*", "my-other-index", "*")
```

**Example Backend Role**
```json
{
  "cluster_permissions": [
    "cluster:monitor/*"
  ],
  "index_permissions": [
    {
      "index_patterns": ["logs-*"],
      "allowed_actions": ["indices:data/read/*", "indices:data/write/*"]
    },
    {
      "index_patterns": ["metrics-*"],
      "allowed_actions": ["indices:data/read/*"]
    }
  ]
}
```

**Common Roles**
- **admin**: Full cluster and index access (`cluster:*`, `indices:*`)
- **analyst**: Read-only to all indices (`indices:data/read/*`)
- **ingest**: Write to time-series indices only (`indices:create`, `indices:data/write/*` on `logs-*`)
- **dashboards-user**: Access to Dashboards UI and saved searches (limited API)

---

## Service-Linked Role Quirks

### What It Is
AWS OpenSearch requires a **service-linked role** (automatically created on first domain) that allows AWS to manage cluster infrastructure:
```
arn:aws:iam::123456789012:role/aws-service-role/opensearchservice.amazonaws.com/AWSServiceRoleForAmazonOpenSearchService
```

### Permissions It Grants to AWS
- Create/delete VPC endpoints
- Attach/detach ENIs to subnets
- Modify security groups (in rare cases)
- Write CloudWatch metrics and logs

### IAM vs Internal Auth Complexity
**Gotcha**: Resource-based policy and internal user database are orthogonal:
- **IAM policy** (resource-based on the domain) controls whether a principal can call the OpenSearch API
- **Internal user database** (separate from IAM) controls what data that principal can access once authenticated

**Example Confusion**
```
Scenario: AWS account Alice has IAM role with es:ESHttpGet permission to Bob's domain
          But Bob's domain does not list Alice's IAM role in the resource policy
Result: Alice cannot authenticate (fails at IAM check)

Scenario: AWS account Alice has no IAM role; Bob adds Alice's role to domain policy
          But Alice tries to query indices without specifying a backend role
Result: Alice can authenticate but gets "403 Forbidden" on every index (FGAC denies)
```

### Best Practice
1. **IAM policy**: Allows or denies the call reaching OpenSearch at all
2. **Resource policy** (on domain): Lists which IAM principals/roles are allowed
3. **Internal users/roles**: Define what indices each authenticated principal can access
4. **Order**: IAM → Resource Policy → FGAC checks

---

## Snapshot Policies: Automated Backups and Restore

### Automated Snapshots

**Default Behavior**
- AWS creates daily snapshots automatically
- Stored in AWS-managed S3 bucket (you don't pay for this bucket; it's included)
- Retained for 14 days (configurable up to 35 days)
- Zero cost; automated

**Configuration** (via AWS Console or API)
```json
{
  "AutomatedSnapshotStartHour": 3,  // UTC 3 AM
  "SnapshotRetentionDays": 14
}
```

### Manual Snapshots
- Useful before major changes (version upgrade, configuration change)
- Stored in the same AWS-managed S3 bucket
- Persistent (not auto-deleted like automated snapshots)

**Create Manual Snapshot** (via OpenSearch API)
```bash
curl -X PUT "https://domain-vpc:9200/_snapshot/aws/my-backup-$(date +%Y%m%d)" \
  -H "Content-Type: application/json" \
  -d '{"indices": "*", "include_global_state": true}'
```

### Cross-Region Snapshots
- **Setup**: Enable snapshot to S3 and enable cross-region replication on S3 bucket
- **Cost**: S3 cross-region transfer (~$0.02/GB)
- **Recovery**: Snapshot replicated to secondary region; can restore new cluster there in minutes
- **Use case**: Disaster recovery, compliance (data residency)

### Cross-Account Snapshot Restore
- Account A creates snapshot in S3 bucket
- Bucket policy allows Account B to assume role and restore
- Account B creates new cluster and restores from snapshot
- **Use case**: Staging/prod isolation, multi-tenant SaaS

**S3 Bucket Policy (Account A, allows Account B to restore)**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT-B:root"
      },
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-snapshots-bucket",
        "arn:aws:s3:::my-snapshots-bucket/*"
      ]
    }
  ]
}
```

---

## Slow Log and Application Log Delivery

### Slow Query Logs
- **Purpose**: Identify queries taking > threshold (default 500 ms)
- **Destination**: CloudWatch Logs group (automatically created)
- **Retention**: Configurable (default 7 days)
- **Cost**: CloudWatch Logs ingestion (~$0.50/GB ingested)

**Enable in OpenSearch**
```bash
curl -X PUT "https://domain-vpc:9200/_plugins/_logstash/config/index_slow_logs" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_ms": 500,
    "log_to_cloudwatch": true
  }'
```

**Example Slow Log Entry** (in CloudWatch Logs)
```
[2024-12-01 10:23:45,123] INDEX [my-index] took [1,523ms], query: {...}
```

### Application Logs
- **What they are**: OpenSearch node logs (cluster state changes, exceptions, GC events)
- **Destination**: CloudWatch Logs group
- **Log types**: ES_APPLICATION_LOGS, ES_INDEX_SLOW_LOGS, ES_CLUSTER_LOGS
- **Retention**: Configurable

**Enable Application Logs**
```bash
aws opensearch update-domain-config \
  --domain-name my-domain \
  --log-publishing-options '{
    "ES_APPLICATION_LOGS": {
      "CloudWatchLogsLogGroupArn": "arn:aws:logs:us-east-1:123456789012:log-group:/aws/opensearch/domains/my-domain/application-logs",
      "Enabled": true
    }
  }'
```

---

## Summary: Decision Framework

| Decision | AWS OpenSearch | Self-Managed |
|----------|---|---|
| **Operational overhead** | Very low | Very high |
| **Cost for <50 GB** | Competitive | Higher (fixed nodes) |
| **Cost for >1 TB** | Higher per GB | Competitive |
| **Customization** | Limited | Full |
| **Time to production** | Days | Weeks |
| **Disaster recovery** | Built-in, multi-region | Manual, complex |
| **Scaling elasticity** | Good (vertical), limited (horizontal) | Full, but manual planning |
| **Recommended for** | Most workloads, startups | Large-scale, custom needs |

For a **Solr-to-OpenSearch migration project**, AWS OpenSearch Service is the right choice unless:
- Your Solr instance has highly customized plugins or analyzers
- Your indexing throughput consistently exceeds 100K docs/sec
- Your cost is already optimized (self-hosted in-house)
- You have deep Solr expertise and wish to replicate that environment exactly

AWS OpenSearch Serverless is recommended for initial migration (unknown scale, variable workload); migrate to provisioned clusters once steady-state scale is understood.
