# AWS OpenSearch Networking and Security

## Executive Summary

AWS OpenSearch domains exist within your VPC (for modern deployments) or on the public internet (legacy). Networking and security configuration determines whether your search service is accessible, how it authenticates requests, and whether data in transit is encrypted. This document covers production-ready configurations, architectural decisions, and operational considerations for securing OpenSearch in AWS.

---

## VPC Endpoint vs Public Endpoint: Deployment Topology

### VPC Endpoint Deployment (Recommended for All Production)

**What it means**
- OpenSearch domain is deployed inside your VPC
- Nodes receive private IP addresses (10.x.x.x, 172.x.x.x)
- Domain endpoint resolves to private IPs (e.g., `my-domain-vpc.us-east-1.es.amazonaws.com`)
- No internet-facing IP; not reachable from the public internet

**Architecture**
```
Your VPC
├─ Public subnets (application tier, if needed)
│  └─ Application (EC2, ECS, Lambda)
│     ├─ VPC endpoint (resolved DNS)
│     └─ Private link to OpenSearch
│
└─ Private subnets (OpenSearch tier, required for multi-AZ)
   ├─ OpenSearch node (AZ-1)
   ├─ OpenSearch node (AZ-2)
   └─ OpenSearch node (AZ-3) [optional]
```

**Requirements**
- Minimum 2 subnets (for multi-AZ; required for any production deployment)
- Subnets in different AZs (AWS requirement)
- Security group attached to OpenSearch
- IAM policy on domain (resource-based policy) controlling access

**Security benefits**
- Zero internet exposure
- All traffic internal to AWS network
- VPC Flow Logs can audit all access
- DDoS protection is network-level (AWS infrastructure)
- No need for WAF or external load balancer

**Networking access**
- **Same VPC**: Application resolves domain DNS directly
- **Different VPC in same account**: VPC peering + private hosted zone
- **Different account**: Transit Gateway + cross-account IAM role
- **On-premises**: VPN or AWS Direct Connect (adds 5-50 ms latency)

**Costs**
- No additional cost for VPC endpoint itself
- Data transfer: Cross-AZ is $0.02/GB (but usually acceptable)

**Setup Example** (via AWS CLI)
```bash
# Create OpenSearch domain in VPC
aws opensearch create-domain \
  --domain-name my-domain \
  --elasticsearch-version 7.10 \
  --vpc-options '{
    "SubnetIds": ["subnet-12345", "subnet-67890"],
    "SecurityGroupIds": ["sg-abcdef"]
  }' \
  --node-type-and-instance-count '{
    "m5.large.elasticsearch": 3
  }' \
  --access-policies '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::123456789012:role/my-app-role"
        },
        "Action": "es:*",
        "Resource": "arn:aws:es:us-east-1:123456789012:domain/my-domain/*"
      }
    ]
  }'
```

---

### Public Endpoint Deployment (Legacy, Not Recommended)

**What it means**
- OpenSearch domain has public IP address
- Domain endpoint is internet-facing (e.g., `my-domain.us-east-1.es.amazonaws.com`)
- Reachable from anywhere on the internet

**When it was used**
- Early AWS OpenSearch deployments (pre-2018)
- Development/testing environments
- Multi-tenant SaaS (accepting external search requests)

**Why it's discouraged now**
- Exposed to internet scanning and bot attacks
- Requires hardening via IP whitelisting, WAF, or other controls
- Misconfiguration leaks indices (common security incident)
- No VPC segmentation
- High operational risk

**If forced to use public endpoint**
- Restrict via IP whitelist in security group (outbound from known IPs only)
- Enable WAF rules to block common attacks
- Use IAM authentication (SigV4 signing) exclusively; no basic auth
- Monitor CloudWatch for suspicious activity
- Rotate credentials frequently

---

## Security Group Configuration: Inbound Rules

**Security group purpose**: Acts as stateful firewall; controls which traffic can reach OpenSearch nodes.

### Typical Security Group Configuration

**Allow from Application Tier**
```
Type:       Custom TCP
Protocol:   TCP
Port:       9200
Source:     sg-app-tier (security group ID)
Reason:     Application servers query/write to OpenSearch
```

**Allow from Admin/Monitoring**
```
Type:       Custom TCP
Protocol:   TCP
Port:       9200
Source:     sg-admin (or specific IP, e.g., 203.0.113.0/32)
Reason:     Developers, operations, monitoring tools (e.g., Kibana, Grafana)
```

**Allow Internal Cluster Communication**
```
Type:       Custom TCP
Protocol:   TCP
Port:       9300
Source:     Same security group (sg-opensearch)
Reason:     Node-to-node communication (required for multi-node clusters)
```

**Common Mistake**: Allowing inbound from 0.0.0.0/0 (anywhere)
- This is equivalent to a public endpoint
- Exposes OpenSearch to the internet
- Only acceptable for development with WAF rules

### Security Group Example (IaC - Terraform)

```hcl
resource "aws_security_group" "opensearch" {
  name        = "opensearch-sg"
  description = "OpenSearch cluster security group"
  vpc_id      = aws_vpc.main.id

  # Inbound: From application tier (port 9200)
  ingress {
    from_port       = 9200
    to_port         = 9200
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "Application servers"
  }

  # Inbound: From monitoring/admin (port 9200)
  ingress {
    from_port   = 9200
    to_port     = 9200
    protocol    = "tcp"
    cidr_blocks = ["203.0.113.0/32"]  # Admin bastion host
    description = "Admin access"
  }

  # Inbound: Node-to-node communication (port 9300)
  ingress {
    from_port       = 9300
    to_port         = 9300
    protocol        = "tcp"
    security_groups = [aws_security_group.opensearch.id]  # Self-reference
    description     = "Node-to-node communication"
  }

  # Outbound: Allow all (default)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "opensearch-sg"
  }
}
```

---

## IAM Authentication: Resource-Based and Identity-Based Policies

### Resource-Based Policy (Whitelist on Domain)

**What it is**: Policy attached to the OpenSearch domain itself; specifies which IAM principals are allowed to make requests.

**How it works**
1. Client makes request to OpenSearch (signed with AWS SigV4)
2. AWS checks: Is this principal (user, role, account) in the resource policy?
3. If yes, proceed to next check (FGAC); if no, deny immediately

**Example: Allow specific IAM role**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/my-app-role"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:123456789012:domain/my-domain/*"
    }
  ]
}
```

**Example: Allow multiple roles**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::123456789012:role/app-role-1",
          "arn:aws:iam::123456789012:role/app-role-2",
          "arn:aws:iam::123456789012:role/admin-role"
        ]
      },
      "Action": [
        "es:ESHttpGet",
        "es:ESHttpPost",
        "es:ESHttpPut",
        "es:ESHttpDelete"
      ],
      "Resource": "arn:aws:es:us-east-1:123456789012:domain/my-domain/*"
    }
  ]
}
```

**Example: Allow cross-account access**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::999999999999:role/remote-app-role"  # Different account
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:123456789012:domain/my-domain/*"
    }
  ]
}
```

**When to use**: Always for AWS-native apps (EC2, Lambda, ECS, RDS). Zero overhead; credentials are temporary (STS tokens).

---

### Identity-Based Policy (IAM Role Permissions)

**What it is**: Permissions attached to the IAM role itself; specifies what OpenSearch actions that role can perform.

**Example: Allow read-only search**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "es:ESHttpGet"
      ],
      "Resource": "arn:aws:es:us-east-1:123456789012:domain/my-domain/*"
    }
  ]
}
```

**Example: Allow full access**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "es:*"
      ],
      "Resource": "arn:aws:es:us-east-1:123456789012:domain/my-domain/*"
    }
  ]
}
```

**Order of operations**
1. IAM evaluates identity-based policy: Is the action allowed?
2. If denied here, request is rejected immediately
3. If allowed, domain resource-based policy is evaluated
4. If principal not in resource policy, request is rejected
5. If allowed through resource policy, FGAC checks apply

---

## Internal Users Database: Local User Management

**What it is**: OpenSearch maintains its own user/password database, separate from IAM. Users are created via API and have fine-grained permissions tied to backend roles.

### When to Use Internal Users

**Scenario 1: External Users**
```
Third-party applications need to query your OpenSearch cluster.
You cannot create IAM roles in your AWS account for external parties.
Solution: Create internal user in OpenSearch; share username/password.
```

**Scenario 2: Legacy Applications**
```
Application uses basic authentication (username/password).
Cannot be refactored to use IAM roles and SigV4 signing.
Solution: Internal users database provides basic auth endpoint.
```

**Scenario 3: Fine-Grained Index-Level Access**
```
Requirement: Different users have different permissions per index.
Example: Analyst can read logs-* but not metrics-*.
IAM policies are coarse (domain-level or action-level).
Solution: Internal users + backend roles + index permissions provide granularity.
```

### Internal User Management API

**Create user**
```bash
curl -X PUT "https://my-domain-vpc:9200/_plugins/_security/api/users/john" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "MySecurePassword123!",
    "backend_roles": ["analyst"],
    "attributes": {
      "email": "john@example.com"
    }
  }'
```

**Assign user to backend role**
```bash
# Backend roles are defined separately (next section)
# Just assign the role name in the user creation above
# Or update an existing user:

curl -X PATCH "https://my-domain-vpc:9200/_plugins/_security/api/users/john" \
  -H "Content-Type: application/json" \
  -d '{
    "backend_roles": ["analyst", "reviewer"]  # Add multiple roles
  }'
```

**List users**
```bash
curl "https://my-domain-vpc:9200/_plugins/_security/api/users"
```

**Delete user**
```bash
curl -X DELETE "https://my-domain-vpc:9200/_plugins/_security/api/users/john"
```

### Backend Roles and Permissions

**Define a backend role**
```bash
curl -X PUT "https://my-domain-vpc:9200/_plugins/_security/api/roles/analyst" \
  -H "Content-Type: application/json" \
  -d '{
    "cluster_permissions": [
      "cluster:monitor/*"  # Can monitor cluster (health, stats)
    ],
    "index_permissions": [
      {
        "index_patterns": ["logs-*"],
        "allowed_actions": [
          "indices:data/read/*"  # Can read logs indices
        ]
      }
    ]
  }'
```

**Common backend roles**

| Role | Permissions | Use Case |
|------|---|---|
| admin | `cluster:*`, `indices:*` | Full cluster access |
| analyst | `cluster:monitor/*`, `indices:data/read/*` on `logs-*` | Read-only to logs |
| ingest | `cluster:*`, `indices:data/write/*` on `logs-*` | Write logs only |
| dashboards-user | Limited API (saved objects, dashboards) | Kibana/Dashboards UI users |

---

## SAML Federation for Dashboards UI

**What it is**: Integration between OpenSearch Dashboards and external identity providers (Okta, Azure AD, Ping Identity) via SAML 2.0.

**How it works**
```
User opens OpenSearch Dashboards
  ↓
Dashboards redirects to IdP login (Okta, Azure AD)
  ↓
User authenticates with IdP
  ↓
IdP returns SAML assertion (XML token with identity claims)
  ↓
Dashboards validates assertion signature
  ↓
Dashboards creates session; user logged in
  ↓
User can now access Dashboards UI
```

**Important caveat**: SAML federation only works for **Dashboards UI access**, not API access. For API access, users still need API keys or other authentication.

### SAML Configuration

**Prerequisite: Get SAML metadata from IdP**
- Okta: IdP metadata URL is provided in Okta admin console
- Azure AD: Download SAML metadata XML from Azure portal
- Ping Identity: Export metadata from Ping console

**Configure SAML in OpenSearch**
```bash
curl -X PUT "https://my-domain-vpc:9200/_plugins/_security/api/saml/config" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "order": 5,
    "http_enabled": false,
    "transport_enabled": true,
    "idp": {
      "metadata_url": "https://dev-123456.okta.com/app/exk12345abc/sso/saml/metadata",
      "entity_id": "https://dev-123456.okta.com",
      "binding": {
        "saml_single_signon_binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
      }
    },
    "sp": {
      "entity_id": "https://my-domain.us-east-1.kibana.amazonaws.com"
    },
    "role_key": "groups",  # SAML attribute mapping to backend roles
    "roles_key": "groups"
  }'
```

**Map SAML groups to OpenSearch backend roles**
```bash
# SAML assertion contains: <saml:Attribute Name="groups"><saml:AttributeValue>analysts</saml:AttributeValue></saml:Attribute>
# Map this to OpenSearch backend role "analyst"

curl -X PUT "https://my-domain-vpc:9200/_plugins/_security/api/rolesmapping/analyst" \
  -H "Content-Type: application/json" \
  -d '{
    "backend_roles": [],
    "users": [],
    "and_backend_roles": ["analysts"],  # Maps SAML "analysts" group to this role
    "description": "Map Okta analysts group to OpenSearch analyst role"
  }'
```

**Test SAML flow**
1. Open `https://my-domain.us-east-1.kibana.amazonaws.com`
2. Should redirect to Okta/Azure AD login
3. Enter credentials
4. Should redirect back to Dashboards (logged in)

---

## OIDC Federation (Modern Alternative to SAML)

**What it is**: OAuth 2.0 / OpenID Connect integration; newer standard than SAML, easier for cloud-native apps.

**Advantage over SAML**: OIDC is simpler, uses JSON tokens (JWT) instead of XML, better for APIs.

**Limitation in AWS OpenSearch**: OIDC is supported for Dashboards UI only (same as SAML); API access still requires API keys.

**OIDC Configuration**
```bash
curl -X PUT "https://my-domain-vpc:9200/_plugins/_security/api/oidc/config" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "client_id": "my-opensearch-client-id",
    "client_secret": "my-secret",
    "connect_url": "https://dev-123456.okta.com/.well-known/openid-configuration",
    "scope": ["openid", "profile", "email"],
    "roles_key": "groups"
  }'
```

---

## Encryption: At-Rest and In-Transit

### Encryption at Rest (EBS/Storage)

**What it protects**: Data written to disk on OpenSearch nodes.

**Configuration**
- **Default**: AWS-managed KMS key (aws/opensearch managed service key)
- **Custom**: Customer-managed KMS key (you manage key rotation and access)

**Benefits of customer-managed key**
- Auditing: CloudTrail shows every key usage
- Compliance: Some standards require customer-managed keys
- Key rotation: Control how often keys are rotated
- Access control: Add conditions on who can use the key

**Example: Enable customer-managed KMS key**
```bash
# First, create or use existing KMS key
KMS_KEY_ID="arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"

# Create OpenSearch domain with custom KMS key
aws opensearch create-domain \
  --domain-name my-domain \
  --encryption-at-rest-options '{
    "Enabled": true,
    "KmsKeyId": "'$KMS_KEY_ID'"
  }'
```

**KMS Key Policy** (grant OpenSearch permission to use key)
```json
{
  "Sid": "Allow OpenSearch to use the key",
  "Effect": "Allow",
  "Principal": {
    "Service": "opensearchservice.amazonaws.com"
  },
  "Action": [
    "kms:Decrypt",
    "kms:GenerateDataKey"
  ],
  "Resource": "*"
}
```

**Cost**: No additional charge for encryption (KMS key usage billed separately; ~$1/month per key)

---

### Encryption in Transit (TLS/HTTPS)

**What it protects**: Data sent over the network to/from OpenSearch.

**Configuration**
- **Default**: TLS 1.2 (minimum version)
- **Policy**: AWS enforces TLS 1.2+; TLS 1.0/1.1 are deprecated

**Enforcing client certificate validation**
```bash
# OpenSearch validates server certificate by default.
# Optionally require client certificate (mutual TLS):

aws opensearch update-domain-config \
  --domain-name my-domain \
  --node-to-node-encryption-options '{
    "Enabled": true
  }'
```

**Application code: Trusting OpenSearch certificate**
```python
from opensearchpy import OpenSearch

# Minimal verification (not recommended)
es = OpenSearch(
    hosts=['https://my-domain.us-east-1.es.amazonaws.com'],
    use_ssl=True,
    verify_certs=False  # UNSAFE; only for development
)

# Proper verification (production)
import certifi
es = OpenSearch(
    hosts=['https://my-domain.us-east-1.es.amazonaws.com'],
    use_ssl=True,
    verify_certs=True,
    ca_certs=certifi.where()  # Use system CA bundle
)
```

**Node-to-Node Encryption**
- **What it is**: Encryption between OpenSearch nodes (internal cluster communication)
- **Required**: 2-node or larger clusters; single-node clusters don't need it
- **Performance impact**: Minimal (< 2% CPU overhead)

```bash
# Enable node-to-node encryption
aws opensearch update-domain-config \
  --domain-name my-domain \
  --node-to-node-encryption-options '{
    "Enabled": true
  }'
```

---

## Cross-Cluster Search (CCS): Multi-Domain Queries

**What it is**: Ability to query OpenSearch indices across multiple clusters (domains) as if they were local.

**Use cases**
- Multi-region deployments (query US and EU clusters simultaneously)
- Multi-tenant isolation (each customer has own domain; query all at once)
- Aggregation (federated search across many small domains)

### CCS Setup

**Source cluster**: Cluster being queried (read access needed)
**Local cluster**: Cluster initiating the query (makes the remote call)

**Example: Query indices in both clusters**
```json
POST _search
{
  "index": "local-index,remote:other-domain-index"
}
```

**Setup: Trust between clusters**

1. **Configure remote cluster connection** (on local cluster)
```bash
curl -X PUT "https://local-domain:9200/_cluster/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "persistent": {
      "cluster": {
        "remote": {
          "remote-cluster-name": {
            "seeds": ["remote-domain.us-west-1.es.amazonaws.com:9300"],
            "transport": {
              "compress": true
            }
          }
        }
      }
    }
  }'
```

2. **Configure security groups** (both clusters)
   - Remote cluster security group: Allow port 9300 from local cluster

3. **Configure IAM** (if cross-account)
   - Remote cluster resource policy: Allow local cluster IAM role

**Limitations**
- Only works for domains in the same region (or same account)
- Cross-region CCS requires manual VPN/Direct Connect setup
- Index names must be globally unique (avoid naming collisions)

---

## Alerting and Anomaly Detection: Built-In Security Plugins

### Alerting Plugin

**What it does**: Monitors indices for specific conditions; sends notifications when thresholds are breached.

**Use cases**
- Alert on unusual search latency (potential DDoS)
- Alert on failed authentication attempts
- Alert on slow queries
- Alert on disk usage > 80%

**Example: Alert on failed authentication**
```json
PUT _plugins/_alerting/monitors/auth-failures
{
  "name": "Failed Authentication Alert",
  "type": "monitor",
  "enabled": true,
  "schedule": {
    "period": {
      "interval": 5,
      "unit": "MINUTES"
    }
  },
  "inputs": [
    {
      "search": {
        "indices": [".opensearch-logs-*"],
        "query": {
          "bool": {
            "must": [
              {
                "match": {
                  "message": "authentication failure"
                }
              },
              {
                "range": {
                  "@timestamp": {
                    "gte": "now-5m"
                  }
                }
              }
            ]
          }
        }
      }
    }
  ],
  "triggers": [
    {
      "name": "Failed Auth Trigger",
      "severity": "2",
      "condition": {
        "script": {
          "source": "params.trigger_value > 10"
        }
      },
      "actions": [
        {
          "name": "Email Admin",
          "destination_id": "email-destination",
          "message_template": {
            "source": "{{ctx.monitor.name}} triggered. {{ctx.results[0].total.value}} failed authentication attempts detected."
          }
        }
      ]
    }
  ]
}
```

**Alert notifications**
- Email (requires SES configuration)
- Slack (webhook)
- Chime (AWS messaging)
- Custom webhooks

---

### Anomaly Detection Plugin

**What it does**: Uses machine learning to detect unusual patterns in data; alerts when anomalies detected.

**Use cases**
- Detect sudden spikes in error rates
- Detect unusual query latencies
- Detect unusual user access patterns
- Detect unusual data insertion rates

**Example: Detect anomaly in indexing rate**
```json
POST _plugins/_anomaly_detection/detectors/_search
{
  "detector": {
    "name": "Indexing Rate Anomaly",
    "description": "Detect unusual changes in document indexing rate",
    "time_field": "@timestamp",
    "indices": [".opensearch-stats-*"],
    "feature_attributes": [
      {
        "feature_name": "docs_indexed",
        "feature_enabled": true,
        "aggregation_query": {
          "docs_indexed": {
            "value_count": {
              "field": "doc_id"
            }
          }
        }
      }
    ],
    "detection_interval": {
      "period": {
        "interval": 10,
        "unit": "MINUTES"
      }
    },
    "window_delay": {
      "period": {
        "interval": 0,
        "unit": "MINUTES"
      }
    }
  }
}
```

---

## Index State Management (ISM) for Automation

**What it is**: Policy-driven automation for index lifecycle (create → warm → delete).

**Use cases**
- Auto-rollover indices daily/weekly (time-series data)
- Auto-transition to warm tier after 30 days
- Auto-delete indices older than 90 days
- Auto-close indices to save disk space

**Example: Time-Series Lifecycle Policy**
```json
PUT _plugins/_ism/policies/logs-lifecycle
{
  "policy": {
    "description": "Lifecycle policy for time-series logs",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [
          {
            "rollover": {
              "min_size": "10gb",
              "min_index_age": "1d"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "warm",
            "conditions": {
              "min_index_age": "30d"
            }
          }
        ]
      },
      {
        "name": "warm",
        "actions": [
          {
            "warm_migration": {}
          }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {
              "min_index_age": "90d"
            }
          }
        ]
      },
      {
        "name": "delete",
        "actions": [
          {
            "delete": {}
          }
        ]
      }
    ]
  }
}
```

**Apply policy to index**
```bash
PUT logs-2024-01-01/_plugins/_ism/explain
{
  "policy_id": "logs-lifecycle"
}
```

---

## VPC Flow Logs: Audit All Network Access

**What it captures**: All network traffic to/from OpenSearch nodes (source IP, destination IP, port, bytes transferred, accept/reject).

**Configuration**
```bash
# Enable VPC Flow Logs for OpenSearch ENI

# First, identify the ENI (network interface) of OpenSearch cluster
aws ec2 describe-network-interfaces \
  --filters "Name=tag:aws:cloudformation:stack-name,Values=*opensearch*" \
  --query "NetworkInterfaces[*].NetworkInterfaceId"

# Create CloudWatch Logs group
aws logs create-log-group --log-group-name /aws/vpc/opensearch-flow-logs

# Create Flow Logs
aws ec2 create-flow-logs \
  --resource-type NetworkInterface \
  --resource-ids eni-12345678 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/opensearch-flow-logs
```

**Analyzing Flow Logs**
```bash
# Query for rejected connections
aws logs start-query \
  --log-group-name /aws/vpc/opensearch-flow-logs \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string "fields srcaddr, dstaddr, dstport, action | filter action = 'REJECT'"
```

---

## Security Best Practices Summary

| Control | Why | How |
|---|---|---|
| VPC Endpoint | Isolate from internet | Deploy domain in VPC; use private subnets |
| Security Groups | Restrict access | Allow only from app tier + admin IPs; port 9200 |
| IAM Roles | Authenticate AWS services | Attach domain resource policy; use SigV4 signing |
| Internal Users | Support external/legacy apps | Create backend roles; map to indices |
| SAML/OIDC | Single sign-on | Configure IdP federation; map groups to roles |
| Encryption at Rest | Protect stored data | Use customer-managed KMS keys |
| Encryption in Transit | Protect network data | TLS 1.2+ enforced; node-to-node encryption |
| Alerting | Monitor for attacks | Alert on auth failures, unusual latency |
| ISM Policies | Automate lifecycle | Delete old indices; transition to cold storage |
| VPC Flow Logs | Audit access | Enable flow logs; analyze for anomalies |

---

## Troubleshooting Common Security Issues

### Issue: "403 Forbidden - User: anonymous is not permitted to access"

**Cause**: Domain resource policy doesn't allow the calling principal.

**Resolution**:
```bash
# Check domain resource policy
aws opensearch describe-domain-config --domain-name my-domain --query "DomainConfig.AccessPolicies"

# Add principal to policy
aws opensearch update-domain-config \
  --domain-name my-domain \
  --access-policies '{...updated policy...}'
```

### Issue: "Connection refused" from application

**Cause**: Security group doesn't allow traffic from application tier.

**Resolution**:
```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-opensearch

# Add inbound rule for application tier
aws ec2 authorize-security-group-ingress \
  --group-id sg-opensearch \
  --protocol tcp \
  --port 9200 \
  --source-group sg-app
```

### Issue: "Certificate verification failed" from application

**Cause**: Application doesn't trust OpenSearch certificate.

**Resolution**:
```python
# Add CA certificate to application
import certifi
import ssl

context = ssl.create_default_context(cafile=certifi.where())
es = OpenSearch(
    hosts=['https://my-domain:9200'],
    use_ssl=True,
    ssl_context=context
)
```

### Issue: SAML login redirects but fails with "Invalid assertion"

**Cause**: SAML entity ID or ACS URL mismatch between IdP and OpenSearch.

**Resolution**:
1. Verify `sp.entity_id` in OpenSearch SAML config matches IdP configuration
2. Verify Dashboards URL is correct (HTTPS, no trailing slash)
3. Check IdP assertion signature certificate is valid

---

## Compliance Considerations

### HIPAA Compliance
- **Requirement**: Encryption at rest (KMS) and in transit (TLS)
- **Configuration**: Customer-managed KMS key; TLS 1.2+
- **Additional**: Audit logging via CloudTrail; VPC Flow Logs

### PCI-DSS Compliance
- **Requirement**: Strong access control; encryption; audit trails
- **Configuration**: IAM roles; FGAC; encryption; CloudWatch logs
- **Additional**: Annual penetration testing; security scanning

### SOC 2 Compliance
- **Requirement**: Documented security controls; audit trails
- **Configuration**: VPC deployment; CloudWatch logs; CloudTrail
- **Additional**: Monitoring and alerting; incident response procedures

---

**Final Recommendation**: For production deployments, use VPC-endpoint deployment with:
1. Private subnets (multi-AZ)
2. Security groups (least privilege)
3. IAM roles (SigV4 signing) + FGAC
4. Encryption (KMS key + TLS)
5. Monitoring (CloudWatch, VPC Flow Logs, alerting)

This configuration provides defense-in-depth and aligns with AWS best practices.
