# Networking and Access Patterns for AWS OpenSearch

This document covers VPC configuration, endpoint access, and connectivity patterns for both managed domains and Serverless collections.

## 1. Managed Domain Networking

### 1.1 VPC Access (Recommended for Production)

When a managed domain is placed in a VPC:

- The domain endpoint resolves to private IP addresses within the VPC subnets.
- Access is controlled by **security groups** attached to the domain.
- Clients must be within the VPC or connected via VPN, Direct Connect, or VPC peering.
- The domain is not accessible from the public internet.

**Configuration at creation time:**

| Parameter | Description |
| :--- | :--- |
| VPC | The VPC to place the domain in |
| Subnets | One subnet per AZ (2 or 3 subnets for multi-AZ) |
| Security groups | Control inbound access (typically allow port 443 from application security groups) |

**Self-managed equivalent**: A cluster behind a private load balancer in a VPC. The migration is straightforward — update the endpoint URL and security group rules.

### 1.2 Public Access

- The domain endpoint is a public DNS name resolving to public IPs.
- Access is controlled by **IAM resource-based policies** and/or **fine-grained access control**.
- IP-based access policies can restrict access to specific CIDR ranges.

**When to use**: Development/testing, or when clients are outside AWS (e.g., on-premises applications during a phased migration).

### 1.3 Custom Endpoints

Managed domains support custom endpoint names with ACM certificates:

- Map a custom domain (e.g., `search.example.com`) to the OpenSearch domain endpoint.
- Requires an ACM certificate for the custom domain.
- Useful for maintaining the same endpoint URL during migration from self-managed.

### 1.4 VPC Endpoint Access (PrivateLink)

For cross-VPC or cross-account access without VPC peering:

- Create an **interface VPC endpoint** for the OpenSearch domain.
- Clients in other VPCs or accounts connect via the VPC endpoint.
- Traffic stays on the AWS network.

## 2. Serverless Networking

### 2.1 Network Policies

Serverless uses **network policies** (not VPC placement) to control access:

```json
[
  {
    "Rules": [
      {
        "ResourceType": "collection",
        "Resource": ["collection/my-collection"]
      }
    ],
    "AllowFromPublic": false,
    "SourceVPCEs": ["vpce-0123456789abcdef0"]
  }
]
```

Options:
- **Public access**: The collection endpoint is accessible from the internet (IAM auth still required).
- **VPC endpoint access**: Restrict access to specific VPC endpoints (AWS PrivateLink).

### 2.2 VPC Endpoints for Serverless

To access a Serverless collection from within a VPC:

1. Create an **OpenSearch Serverless VPC endpoint** (different from standard interface endpoints).
2. Associate the VPC endpoint with the collection's network policy.
3. Clients in the VPC route to the collection through the VPC endpoint.

**Key difference from managed domains**: The collection itself is not "in" the VPC. The VPC endpoint provides a private path to the Serverless service.

### 2.3 Endpoint Format

| Deployment | Endpoint Format | Port |
| :--- | :--- | :--- |
| Self-managed | `https://my-cluster:9200` | 9200 (configurable) |
| Managed domain (VPC) | `https://vpc-my-domain-xxxx.<region>.es.amazonaws.com` | 443 |
| Managed domain (public) | `https://search-my-domain-xxxx.<region>.es.amazonaws.com` | 443 |
| Serverless | `https://<collection-id>.<region>.aoss.amazonaws.com` | 443 |

**Migration action**: Update all client configurations to use port 443 and the new endpoint format. Self-managed clusters typically use port 9200.

## 3. Cross-VPC and Cross-Account Access

### 3.1 Managed Domains

| Pattern | Mechanism |
| :--- | :--- |
| Same VPC | Security group rules |
| Cross-VPC (same account) | VPC peering or Transit Gateway + security groups |
| Cross-VPC (cross-account) | VPC peering, Transit Gateway, or PrivateLink |
| On-premises | AWS Direct Connect or Site-to-Site VPN |

### 3.2 Serverless Collections

| Pattern | Mechanism |
| :--- | :--- |
| Same VPC | VPC endpoint + network policy |
| Cross-VPC (same account) | VPC endpoint in each VPC + network policy |
| Cross-VPC (cross-account) | VPC endpoint + cross-account IAM + network policy |
| Public internet | Public network policy + IAM auth |

## 4. DNS and Service Discovery

### 4.1 Self-Managed Migration Considerations

Self-managed clusters often use:
- Internal DNS names (e.g., `opensearch.internal.example.com`)
- Service discovery (Consul, Kubernetes DNS)
- Load balancer endpoints

When migrating to AWS:
- **Managed domain**: Use a Route 53 CNAME or alias record pointing to the domain endpoint, or use a custom endpoint.
- **Serverless**: Use a Route 53 CNAME pointing to the collection endpoint.
- Update all client configurations, environment variables, and config files.

### 4.2 Phased Migration with DNS

For zero-downtime migration:

1. Set up the AWS deployment (managed or Serverless) alongside the self-managed cluster.
2. Migrate data using snapshot/restore (managed) or OSI pipeline (either).
3. Run both in parallel, validating query results.
4. Switch the DNS record from the self-managed endpoint to the AWS endpoint.
5. Monitor for issues; roll back DNS if needed.
6. Decommission the self-managed cluster after stabilization.

## 5. Firewall and Security Group Rules

### 5.1 Managed Domain Security Groups

Inbound rules needed:

| Source | Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- |
| Application security group | 443 | HTTPS | API and Dashboards access |
| Bastion / VPN security group | 443 | HTTPS | Admin access to Dashboards |
| OpenSearch Ingestion (if used) | 443 | HTTPS | Data pipeline access |

No outbound rules are needed on the domain security group (AWS manages outbound).

### 5.2 Self-Managed Firewall Translation

| Self-Managed Rule | AWS Equivalent |
| :--- | :--- |
| Allow port 9200 from app servers | Security group: allow 443 from app SG |
| Allow port 9300 (transport) from cluster nodes | Not needed — AWS manages inter-node communication |
| Allow port 9200 from monitoring | Security group: allow 443 from monitoring SG |
| Deny all other inbound | Default security group behavior (deny all not explicitly allowed) |
