# AWS OpenSearch Service: Expert Reference

Comprehensive guide to provisioning, securing, and operating AWS-managed OpenSearch for production deployments. This is not a general OpenSearch guide—it focuses on AWS-specific operational choices and their trade-offs.

---

## Provisioned vs Serverless: Decision Framework

### Provisioned Clusters (Traditional, Still Dominant)

**You explicitly provision node counts and types; you pay for capacity whether or not fully utilized.**

#### When to Use Provisioned

- **Throughput > 50K docs/sec** or **> 1K queries/sec** sustained
- **Predictable workload** with known baseline capacity
- **Cost-sensitive at high scale** (> 5 TB data): fixed costs amortize better
- **Multi-region failover** required (3-AZ deployments)
- **Full feature support** needed (all plugins, advanced config)

#### Sizing Considerations

**Data nodes** (where indices live):
- `r6g.xlarge` (4 vCPU, 32 GB RAM): Most common; holds ~500 GB-2 TB per node
- `r6g.2xlarge` (8 vCPU, 64 GB RAM): For larger shards or higher throughput
- `m6g.xlarge`: Compute-heavy analytics (avoid for mixed workloads)

**Dedicated masters** (cluster coordination):
- Separate from data nodes when node count > 10 or workload is high-write
- `m6g.large` (2 vCPU, 8 GB RAM): Sufficient for clusters up to 50 nodes
- Minimum 3 masters for quorum (HA requirement)

**Example configuration:**
- 3 nodes (r6g.xlarge), 2-AZ: ~$680/month + $160 storage = $840/month
- 5 nodes (r6g.xlarge) + 3 masters (m6g.large), 3-AZ: ~$1200 + $330 masters + $200 storage = $1730/month

#### Cost Trap: Over-Provisioning

Common mistake: provision 10 nodes "for future growth". Cost: $2300/month (26% of annual budget waste). Better: start with 3, add nodes as data grows.

### OpenSearch Serverless (New, Rapidly Adopted)

**Auto-scaling; you pay per OpenSearch Compute Unit (OCU) consumed; no node management.**

#### When to Use Serverless

- **Indexing throughput < 10K docs/sec**
- **Search throughput < 1K queries/sec**
- **Data volume < 100 GB** (or growth unpredictable)
- **Variable workload** (2x-10x spike during peak hours)
- **Operational simplicity > cost optimization**

#### Pricing Model

- 1 OCU ≈ 2 vCPU + 12 GB RAM, auto-scaled
- ~$0.30 per OCU-hour (~$219/OCU-month)
- Minimum: 4 OCUs ($876/month)
- Auto-scales up to 100+ OCUs; you set limits

#### Cost Scenarios

**Small unpredictable workload (peak 10x baseline):**
- Provisioned: 10 nodes ($2000/month) to handle peaks
- Serverless: 4-40 OCUs, average 8 OCUs ($1750/month average, scales down at night)
- **Winner: Serverless saves $250/month**

**Stable large workload (5 TB, 50K docs/sec):**
- Provisioned: 5 nodes ($1200/month) + reserved discounts
- Serverless: ~50 OCUs ($10,950/month)
- **Winner: Provisioned saves $9750/month**

#### Serverless Limitations

- **No VPC endpoint**: Public endpoint only (more restrictive security)
- **Limited plugins**: Anomaly Detection, ILM not available
- **Indexing backpressure**: Aggressive rate-limiting if you exceed provisioned OCUs
- **Higher p99 latency**: ~10-20% higher due to multi-tenant infrastructure

---

## Instance Type Selection

### Current Generation (2024)

#### Memory-Optimized (Graviton2, Preferred)

| Type | vCPU | RAM | Best For | Hourly Cost |
|------|------|-----|----------|-----------|
| **r6g.large** | 2 | 16 GB | Dev, small production | $0.077 |
| **r6g.xlarge** | 4 | 32 GB | **Most production deployments** | $0.154 |
| **r6g.2xlarge** | 8 | 64 GB | Large clusters, analytics | $0.309 |
| **r6g.4xlarge** | 16 | 128 GB | Rare; massive shards | $0.618 |

**Why Graviton2 (r6g)?**
- 20% cheaper than x86 equivalents
- Comparable performance; sometimes faster (cache efficiency)
- AWS strategic direction; best long-term support

#### Compute-Optimized (For Query-Heavy Workloads)

| Type | vCPU | RAM | Use Case | Hourly Cost |
|------|------|-----|----------|-----------|
| **c6g.xlarge** | 4 | 8 GB | Aggregation-heavy queries, few indices | $0.136 |
| **c6g.2xlarge** | 8 | 16 GB | Complex analytics | $0.272 |

**When to use:** Heavy aggregations, complex bool queries on large datasets. Not for general-purpose search.

#### Avoid Legacy Types

- x86 (r7i, i3): 20% more expensive; no performance benefit
- Local NVMe (i3, i3en): Faster but single-node-only; not worth operational complexity

### Storage Architecture

#### EBS gp3 (Default, Recommended)

- **Baseline**: 3,000 IOPS, 125 MB/s throughput (included in instance pricing)
- **Burstable**: Scale to 16,000 IOPS, 1,000 MB/s if needed (per-GB pricing)
- **Cost**: ~$0.08/GB-month (or $0.05/GB-month with 1-year commitment)
- **Best for**: General-purpose, mixed read/write

**When to upgrade to io1:**
- Consistent > 10K IOPS needed (rare for OpenSearch)
- Massive single-shard queries (> 50 GB scans)
- Database-like workload (not typical for search)

#### Storage Capacity Planning

**Formula:**
```
Total Storage = (Index Size × (1 + Replication Factor)) × 1.3

The 1.3 factor accounts for:
- Segment merging overhead (temporary growth during indexing)
- Operational headroom (snapshots, rebalancing)
```

**Example:**
- 50 GB index, 1 replica (replication factor = 2), 20% headroom needed
- Required: 50 × 2 × 1.2 = 120 GB per node
- Choose r6g.xlarge with 120 GB gp3 volume

---

## Dedicated Master Nodes: When Required, How to Size

### When Required (AWS Policy)

| Node Count | Multi-AZ? | Master Requirement |
|-------------|-----------|---|
| 1-2 nodes | 1-AZ | Optional (risky, not recommended) |
| 3-10 nodes | 1-AZ | Optional but recommended |
| 10+ nodes | Any | **Required** |
| Any count | 3-AZ | **Required** |

### How to Size Masters

**CPU requirement:** Light (cluster state updates are not CPU-intensive)
**Memory requirement:** 0.5-1 GB heap per 100-200 data nodes
**Network requirement:** Critical (must tolerate latency)

| Data Node Count | Master Instance | Quantity |
|---|---|---|
| 3-10 | m6g.large | 1 or 3 (3 for HA) |
| 10-30 | m6g.large | 3 |
| 30-100 | m6g.xlarge | 3-5 |
| 100+ | m6g.xlarge or 2xlarge | 5+ |

**Cost of 3-node master cluster:**
- 3 × m6g.large = ~$110/month (for up to 30 data nodes)
- Adds 15-20% to total cluster cost but ensures stability

### Master Node Placement (AWS Multi-AZ)

**For 3-AZ deployments with dedicated masters:**
```
AZ-1: 2 data nodes + 1 master
AZ-2: 2 data nodes + 1 master
AZ-3: 1 data node + 1 master
```

This ensures masters have quorum (2/3) if any AZ fails.

---

## Multi-AZ Strategy: 2-AZ vs 3-AZ

### 2-AZ Deployment (Cost-Optimized)

**Requirements:**
- Minimum 3 data nodes total
- Spread across 2 AZs (e.g., 2 in AZ-1, 1 in AZ-2)
- No dedicated masters required

**Topology:**
```
AZ-1: 2 data nodes
AZ-2: 1 data node
```

**Behavior on AZ-1 failure:**
- AZ-2 still has at least 1 replica of every shard
- Full search and indexing capability maintained
- Recovery: ~5-10 minutes as replicas become primaries

**Cost:** 3 nodes × $0.154 = $462/month (baseline)

**SLA impact:**
- Addresses single-AZ failures
- Tolerable 1-2 minute recovery window
- ~99.9% uptime (4.3 hours downtime/year)

**Gotcha:** If AZ-1 has 2 shards as primaries and AZ-2 has their replicas, losing AZ-1 temporarily can't rebuild shard replicas (cluster degrades temporarily).

### 3-AZ Deployment (High-Availability Premium)

**Requirements:**
- Minimum 3 data nodes total (1 per AZ)
- Dedicated master nodes required (minimum 3)
- Cross-AZ replication enabled

**Topology (Recommended):**
```
AZ-1: 2 data nodes + 1 master
AZ-2: 2 data nodes + 1 master
AZ-3: 1 data node + 1 master
```

**Behavior on AZ-1 failure:**
- AZ-2 + AZ-3 together have all replicas
- Quorum: 2/3 masters still have consensus
- Zero shard migration needed (replicas already in-place)
- Recovery: Immediate (seconds)

**Cost:** 5 data nodes × $0.154 + 3 masters × $0.077 = $1001/month (~120% overhead vs 2-AZ)

**SLA impact:**
- Can tolerate loss of entire AZ
- Zero shard migration overhead
- ~99.99% uptime (52 minutes downtime/year)

### Decision Criteria

| Factor | 2-AZ | 3-AZ |
|--------|------|------|
| **SLA requirement** | 99.9% ok | 99.99% required |
| **Data criticality** | Standard | High (financial, auth) |
| **Recovery time tolerance** | 5-10 min | < 1 min |
| **Cost sensitivity** | High | Low |
| **Compliance** | SOC 2, HIPAA baseline | PCI-DSS, strict HIPAA |

**For most migrations: Start with 2-AZ; upgrade to 3-AZ if availability SLA tightens.**

---

## VPC vs Public Endpoint: Security Trade-offs

### VPC Endpoint (Strongly Recommended)

**Architecture:**
```
Your VPC
├─ Private subnets (2-3, in different AZs)
│  ├─ OpenSearch domain (private IP 10.x.x.x)
│  └─ ENI (Elastic Network Interface)
│
├─ Application tier
│  └─ EC2/ECS/Lambda (same VPC)
│     → Can reach OpenSearch via private DNS
```

**Security benefits:**
- Zero internet-facing endpoints
- All traffic internal to AWS network
- No DDoS exposure
- VPC Flow Logs can audit all access

**Networking requirements:**
- Create 2+ private subnets (different AZs)
- Assign security group (port 9200 inbound from app tier)
- Enable private DNS resolution (`domain-vpc.us-east-1.es.amazonaws.com`)

**Cross-VPC or cross-account access:**
- **Same VPC:** Direct private DNS lookup
- **Different VPC, same account:** VPC peering + private hosted zone
- **Different account:** Transit Gateway + cross-account role
- **On-premises:** VPN or AWS Direct Connect (adds 5-50ms latency)

**Cost:** No additional cost; just use your VPC

### Public Endpoint (Legacy, Discouraged)

**When used:** Early deployments, multi-tenant SaaS (intentionally public)

**Why discouraged:**
- Internet exposure; subject to scanning and bot attacks
- Misconfiguration leaks sensitive data (common incident)
- No VPC segmentation

**If forced to use:**
1. Restrict via security group (IP whitelist only)
2. Enable WAF (Web Application Firewall) on domain
3. Use IAM auth (SigV4 signing) exclusively; no basic auth
4. Rotate credentials frequently
5. Monitor CloudWatch for suspicious activity

---

## Auth Options: When Each Is Appropriate

### 1. IAM Resource Policy + SigV4 (Preferred for AWS-Native Apps)

**Flow:**
```
EC2 / ECS / Lambda (with IAM role)
    ↓
Assumes role with es:ESHttpGet permission
    ↓
Requests signed with AWS SigV4
    ↓
OpenSearch validates signature
    ↓
Request granted if role in domain resource policy
```

**When to use:**
- Application runs in AWS (EC2, ECS, Lambda)
- No external/legacy access needed
- Zero secrets management overhead (temporary STS tokens)

**Setup:**
```json
// Domain resource policy (AWS console or API)
{
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::123456789012:role/my-app-role"
  },
  "Action": "es:*",
  "Resource": "arn:aws:es:us-east-1:123456789012:domain/my-domain/*"
}
```

**Pros:**
- No password management
- Automatic credential rotation (STS tokens expire in 1 hour)
- Audit via CloudTrail
- Principle of least privilege (fine-grained IAM policies)

### 2. Internal User Database (For Legacy/External Apps)

**Flow:**
```
External app / Old system
    ↓
HTTP basic auth (username/password)
    ↓
OpenSearch validates against internal user database
    ↓
Request granted if user has index permissions
```

**When to use:**
- Cannot refactor to use IAM (legacy system)
- External third-party needs access
- Simple password-based auth acceptable

**Creating users (via API):**
```bash
curl -X PUT "https://domain-vpc:9200/_plugins/_security/api/users/data_scientist" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "MySecurePassword123!",
    "backend_roles": ["analyst"]
  }'
```

**Cons:**
- Password management overhead
- No automatic rotation
- Harder to audit (need Dashboards UI)

### 3. SAML Federation (Corporate SSO)

**Flow:**
```
User opens OpenSearch Dashboards
    ↓
Redirect to corporate IdP (Okta, Azure AD)
    ↓
User authenticates once
    ↓
IdP returns SAML assertion
    ↓
Dashboards creates session
```

**When to use:**
- Corporate environment with centralized SSO
- Reduce password sprawl
- Compliance requirement (centralized auth audit)

**Important caveat:** SAML federation only works for **Dashboards UI access**. API access still requires:
- API keys (created via UI after SSO login), or
- Internal users with passwords

**Setup (via OpenSearch API):**
```bash
curl -X PUT "https://domain-vpc:9200/_plugins/_security/api/saml/config" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "idp": {
      "metadata_url": "https://dev-123456.okta.com/app/exk12345/sso/saml/metadata"
    },
    "sp": {
      "entity_id": "https://my-domain.us-east-1.kibana.amazonaws.com"
    }
  }'
```

**Cons:**
- SAML only for Dashboards, not API
- Adds IdP configuration complexity

### 4. Fine-Grained Access Control (FGAC)

**Always enable in addition to auth method above. Controls what authenticated users can see/do.**

**Hierarchy:**
```
User (authenticated via IAM, internal DB, or SAML)
  └─ Backend Role (e.g., "analyst", "admin", "read-only")
    └─ Index Permission (e.g., "logs-*", "metrics-*")
```

**Example role:**
```json
{
  "cluster_permissions": ["cluster:monitor/*"],  // Can view cluster health
  "index_permissions": [
    {
      "index_patterns": ["logs-*"],
      "allowed_actions": ["indices:data/read/*", "indices:data/write/*"]
    },
    {
      "index_patterns": ["metrics-*"],
      "allowed_actions": ["indices:data/read/*"]  // Read-only
    }
  ]
}
```

**Assign users to roles (backend roles):**
```bash
curl -X PUT "https://domain-vpc:9200/_plugins/_security/api/users/john" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "SecurePassword123!",
    "backend_roles": ["analyst", "logs-reader"]  // Assign multiple roles
  }'
```

---

## SigV4 Signing: What It Is, When Required

### What SigV4 Is

AWS Signature Version 4 is a request signing protocol. Your application signs HTTP requests using AWS credentials (access key, secret key), and OpenSearch validates the signature.

**Flow:**
1. Application has AWS credentials (from IAM role)
2. Application constructs OpenSearch API request
3. Application signs the request with SigV4 (includes auth header)
4. OpenSearch receives request
5. OpenSearch validates signature (using AWS public key)
6. OpenSearch checks domain resource policy (is this principal allowed?)
7. OpenSearch grants/denies based on FGAC rules

### When Required

- **AWS-managed OpenSearch Service with IAM auth**: Always
- **Self-managed OpenSearch with IAM signers**: When you implement SigV4 layer
- **Public OpenSearch endpoint**: Not required (can use basic auth)

### Spring Boot Configuration (Kotlin)

**Dependencies:**
```gradle
implementation 'org.opensearch.client:opensearch-java:2.5.0'
implementation 'software.amazon.awssdk:sdk-for-java:2.20.0'
implementation 'software.amazon.awssdk:auth-crt:2.20.0'
```

**Configuration class:**
```kotlin
@Configuration
@ConditionalOnProperty(name = "opensearch.aws.enabled", havingValue = "true")
class OpenSearchAwsConfig(
    @Value("\${opensearch.host}") val host: String,
    @Value("\${opensearch.port}") val port: Int = 9200,
    @Value("\${opensearch.aws.region}") val region: String = "us-west-2"
) {

    @Bean
    fun restClient(): RestClient {
        val credentialsProvider = DefaultCredentialsProvider.create()  // Uses IAM role

        return RestClient.builder(HttpHost(host, port, "https"))
            .setHttpClientConfigCallback { httpClientBuilder ->
                // Add SigV4 signing interceptor
                httpClientBuilder.addInterceptorLast { httpRequest, httpContext ->
                    val signer = Aws4Signer.create()
                    val signingConfig = Aws4SignerConfigProvider(
                        service = "es",
                        region = Region.of(region),
                        credentials = credentialsProvider
                    )
                    signer.sign(httpRequest, signingConfig)
                }
            }
            .build()
    }

    @Bean
    fun openSearchClient(restClient: RestClient): OpenSearchClient {
        val transport = RestClientTransport(restClient, ObjectMapper())
        return OpenSearchClient(transport)
    }
}
```

**application.yml:**
```yaml
opensearch:
  host: my-domain.us-west-2.es.amazonaws.com
  port: 443
  aws:
    enabled: true
    region: us-west-2
    # Credentials auto-loaded from IAM role (EC2, ECS, Lambda)
```

---

## Snapshot Strategy for Migration

### Automated Daily Snapshots (AWS-Managed)

**Default behavior:**
- AWS creates daily snapshot automatically
- Stored in AWS-managed S3 bucket (included in cost)
- Retained for 14 days (configurable up to 35 days)
- Zero additional cost

**Use case:** Disaster recovery, point-in-time restore

### Manual Snapshots (For Migration)

**Create before and after migration:**

```bash
# Snapshot old Solr cluster before migration starts
curl -X PUT "https://old-domain:9200/_snapshot/aws/pre-migration-$(date +%Y%m%d)"

# Snapshot new OpenSearch cluster after cutover
curl -X PUT "https://new-domain:9200/_snapshot/aws/post-migration-$(date +%Y%m%d)"
```

### Restore Snapshot to New Cluster

**Workflow:**
1. Source cluster (Solr): Export via API or snapshot
2. Intermediate: S3 bucket with snapshot
3. Target cluster (OpenSearch): Restore from snapshot

**Snapshot creation:**
```bash
# On source domain
POST /_snapshot/my-backup/snapshot-name
{
  "indices": "my-index",
  "include_global_state": false
}
```

**Restore to target:**
```bash
# On target domain
POST /_snapshot/my-backup/snapshot-name/_restore
{
  "indices": "my-index"
}
```

### Cross-Region Snapshots (DR)

**Setup:**
1. Enable S3 replication on snapshot bucket
2. Snapshot automatically replicated to secondary region
3. Restore in secondary region if primary fails

**Cost:**
- S3 cross-region replication: ~$0.02/GB
- For 1 TB, ~$20/month

---

## Version Considerations: AWS Lag, Upgrade Path

### AWS Release Schedule

- **OpenSearch open-source**: 2-3 releases per year (2.11, 2.12, 2.13, etc.)
- **AWS OpenSearch Service**: 4-8 weeks lag behind open-source
- **Current supported versions**: Last 3-4 versions; older versions EOL with notice
- **Major version upgrades** (1.x → 2.x, 2.x → 3.x): Explicit opt-in required

### Upgrade Path Strategy

**Version lag implications:**
- Security fixes take 2-4 weeks to arrive
- Feature adoption is delayed
- Plan for SLA windows (upgrades happen during business hours)

**Recommended approach:**
1. **Stay 1 version behind latest** (e.g., on 2.11 when 2.13 is out)
2. **Quarterly upgrade cycle** (apply upgrades every 3 months)
3. **Test in staging first** (especially major version upgrades)
4. **Plan for 30-60 min blue-green deployment window**

**Blue-green upgrade process (AWS-managed):**
1. You initiate upgrade request
2. AWS spins up new cluster with target version
3. AWS migrates data (~10-30 min)
4. AWS switches DNS (transparent, <5s client reconnection)
5. Old cluster retained for 24 hours (rollback if needed)

---

## Cost Model: What Drives Costs

### Instance Hours (Dominant Cost Driver)

```
Monthly cost = Node count × Node type hourly rate × 730 hours
```

**Example:**
- 3 × r6g.xlarge = 3 × $0.154 × 730 = $337/month
- 3 × m6g.large (masters) = 3 × $0.077 × 730 = $169/month
- Total: $506/month (instance cost, no storage)

### Storage

```
Storage cost = EBS size (GB) × $0.08/GB-month
```

**Example:**
- 500 GB gp3 = 500 × $0.08 = $40/month

### Data Transfer

```
Cross-AZ transfer: $0.02/GB
Internet egress: $0.09/GB (avoid if possible)
Intra-AZ transfer: $0.00
```

**Migration data transfer example:**
- Reindex 1 TB from Solr (on-prem) to OpenSearch (AWS): ~$20 (cross-region)
- During migration, dual-write adds 0% network cost (same region)

### Reserved Instances (Cost Optimization)

- **1-year commitment**: ~30% discount
- **3-year commitment**: ~40% discount
- Break-even: ~8 months for 1-year

**Strategy:**
- Reserve 80% of baseline capacity
- Use on-demand for peaks/growth
- Typical savings: $100-200/month for medium cluster

### Cost Calculation Checklist

| Component | Formula | Example |
|---|---|---|
| Instance hours | Nodes × Hourly rate × 730 | 3 × $0.154 × 730 = $337 |
| Storage | GB × $0.08 | 500 × $0.08 = $40 |
| Transfer | GB × $0.02 (cross-AZ) | 100 × $0.02 = $2 |
| **Monthly total** | | **~$380/month** |

---

## Slow Logs: Essential for Production

### Why Slow Logs Matter

Slow logs identify:
- Expensive queries (need optimization)
- Query design flaws (must-not clauses, deep pagination)
- Cluster capacity issues (GC pauses, memory pressure)

**Without slow logs:** Operating blind; performance regressions go undetected.

### Configuration

**Enable at domain level (AWS console or API):**

```bash
aws opensearch update-domain-config \
  --domain-name my-domain \
  --log-publishing-options '{
    "ES_INDEX_SLOW_LOGS": {
      "CloudWatchLogsLogGroupArn": "arn:aws:logs:us-west-1:123456789012:log-group:/aws/opensearch/my-domain/slow-logs",
      "Enabled": true
    }
  }'
```

**Slow log thresholds (via OpenSearch API):**

```bash
PUT _settings
{
  "index.search.slowlog.threshold.query.warn": "10s",
  "index.search.slowlog.threshold.query.info": "5s",
  "index.search.slowlog.threshold.query.debug": "2s",
  "index.indexing.slowlog.threshold.index.warn": "10s",
  "index.indexing.slowlog.threshold.index.info": "5s"
}
```

**CloudWatch Logs integration:**
- Slow queries automatically shipped to CloudWatch Logs
- Create alarms: IF queries > 10s THEN notify ops
- Cost: ~$0.50/GB ingested (small for typical clusters)

### Monitoring Slow Logs

**CloudWatch Insights query:**
```sql
fields @timestamp, @message, query_time_ms
| filter query_time_ms > 5000
| stats count() as slow_query_count by query
| sort slow_query_count desc
```

**Alerts to set up:**
- "More than 5 queries > 10s in last hour" → Warn
- "p99 query latency > 2x baseline" → Critical
- "GC pause > 5 seconds" → Investigate

---

## Troubleshooting & Operational Realities

### Cluster & Index Creation Blocks (The "90% Trap")

Even with hundreds of gigabytes of absolute free space, OpenSearch can block index creation if **percentage-based** disk watermarks are tripped. This is a common "day zero" failure during migrations to existing clusters or local dev environments.

**The Symptom:**
- API Error: `403 Forbidden`
- Root Cause Message: `index_create_block_exception`
- Reason: `blocked by: [FORBIDDEN/10/cluster create-index blocked (api)];`

**The Heuristic:**
1. Check `_cat/nodes?h=disk.used_percent`. If > 90%, you are likely in the "High Watermark" zone.
2. Check `_cluster/settings`. Look for `cluster.blocks.create_index`.

**The Remediation (Transient Fix):**
If absolute disk space is sufficient but percentage is high, relax the watermarks and explicitly unblock index creation:

```bash
curl -X PUT "http://localhost:9200/_cluster/settings" -H "Content-Type: application/json" -d'
{
  "transient": {
    "cluster.routing.allocation.disk.watermark.low": "95%",
    "cluster.routing.allocation.disk.watermark.high": "98%",
    "cluster.routing.allocation.disk.watermark.flood_stage": "99%",
    "cluster.blocks.create_index": "false"
  }
}'
```
*Note: This is a safety override. Long-term fix is to increase disk capacity or delete old indices.*

---

## Summary: Decision Framework for AWS OpenSearch

| Question | Answer → Decision |
|---|---|
| **Data size** | < 100 GB → Serverless; > 500 GB → Provisioned |
| **Throughput** | < 1K req/sec → Provisioned small; > 10K docs/sec → Provisioned large |
| **SLA** | 99.9% ok → 2-AZ; 99.99% required → 3-AZ |
| **Network** | In AWS → VPC endpoint; external access needed → Negotiate carefully |
| **Auth** | AWS-native → IAM + SigV4; Legacy → Internal users |
| **Instance type** | Default → r6g.xlarge (memory-optimized) |
| **Masters** | > 10 nodes or 3-AZ → Dedicated; < 10 nodes 2-AZ → Co-located |
| **Storage** | Most workloads → gp3; Very high IOPS (rare) → io1 |
| **Cost optimization** | High data volume → Reserved instances; Variable → Serverless |

**For most Solr migrations: Start with 3-node r6g.xlarge (2-AZ), VPC endpoint, IAM auth, gp3 storage. Cost: ~$840/month. Add dedicated masters if scaling past 10 nodes.**
