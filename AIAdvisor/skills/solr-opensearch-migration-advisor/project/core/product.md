# Solr to OpenSearch Migration: Product Steering Document

**Project**: Replace Apache Solr SolrCloud with AWS OpenSearch Service as the primary search engine
**Date**: 2024-Q1
**Stakeholders**: Platform Team, Search Team, DevOps, Security, Finance

---

## Vision and Goals

### Why We're Doing This

Our current Solr SolrCloud infrastructure has reached operational maturity limits:
- **Operational overhead**: Manual ZooKeeper management, cluster rebalancing, node replacement consumes 15-20% of platform team capacity
- **Scaling friction**: Adding capacity requires infrastructure provisioning, manual shard reallocation, and coordination across teams
- **Maintenance burden**: JVM tuning, garbage collection tuning, and custom plugin management are constant pain points
- **Inconsistent search quality**: Solr index configuration is siloed in each app team's code; no shared standards or best practices
- **Cost opacity**: Self-managed infrastructure costs are buried in cloud bills; hard to allocate per application

### Success Looks Like

1. **Operational simplicity**: Platform team spends <5 hours/month on search infrastructure (down from 15-20)
2. **Search quality maintained or improved**: Relevance metrics (click-through rate, dwell time) remain stable or improve; latency reduced by 10-20%
3. **Faster deployments**: App teams can deploy new search features without coordinating with platform team (same-day turnaround, not weeks)
4. **Cost predictability**: Fixed monthly cost for search infrastructure; allocated per application via tagging
5. **Operational observability**: Real-time dashboards show search latency, indexing throughput, query patterns; alerting on anomalies
6. **Zero-downtime during migration**: Users experience no search outages or degradation during cutover

### Non-Goals

- **Not a search algorithm overhaul**: This is not an opportunity to rewrite ranking/relevance functions (that's a separate initiative)
- **Not a query language migration**: Applications continue using their existing Solr query syntax (mapped to OpenSearch during transition)
- **Not a multi-cloud strategy**: We're committing to AWS; no ongoing self-managed fallback
- **Not a feature parity requirement**: Some Solr features (e.g., custom update processors) may not have 1:1 equivalents; we prioritize core search (query, indexing)

---

## Stakeholder Concerns and How We Address Them

### Search Team (Data Science, Relevance)
**Concern**: Will migration affect search quality? How do we validate changes?

**Response**:
- Run parallel Solr/OpenSearch for 1 week post-cutover; compare metrics side-by-side
- Establish relevance benchmarks (click-through rate, query latency percentiles) as acceptance criteria
- Post-migration, implement A/B testing framework (5% of traffic to OpenSearch, 95% to Solr) before 100% cutover
- Pre-migration: Migrate and re-index 3 months of production data; run offline comparison of top 1000 queries

### Platform Team (Operations)
**Concern**: Will this reduce our on-call burden? What's the learning curve?

**Response**:
- AWS OpenSearch is managed service; we don't patch, scale nodes, or manage ZooKeeper
- New operational skills: VPC networking, IAM, CloudWatch Logs (AWS fundamentals team already knows these)
- We retain Logstash expertise for indexing pipeline (no change)
- Monitoring: Migrate to CloudWatch + OpenSearch slow logs (vs. current Ganglia + custom logging)

### Finance (Cost Management)
**Concern**: Will this cost more or less than self-managed?

**Response**:
- **Estimated monthly cost**: $3000-5000 (3-5 TB data, 1000 docs/sec indexing)
- **Breakdown**: Compute ($2000-3000), Storage ($800-1500), Data transfer ($200-500)
- **Comparison to self-managed**: Saves ~$1000/month in EC2 costs; eliminates ZooKeeper cluster overhead
- **Cost tracking**: Use AWS tags (team, app, environment) for cost allocation and showback

### Security Team
**Concern**: Is AWS OpenSearch secure? How do we meet compliance requirements?

**Response**:
- **Encryption**: At-rest (KMS), in-transit (TLS 1.2+); both enabled by default
- **Authentication**: IAM roles for AWS services; internal user database for external tools
- **Authorization**: Fine-grained access control (FGAC) per index, per user
- **Audit**: CloudTrail logs all API calls; VPC Flow Logs capture network access
- **Compliance**: Supports HIPAA, PCI-DSS, SOC 2 (with proper configuration)

### Application Teams (Developers)
**Concern**: Will my app break? Do I need to rewrite search code?

**Response**:
- **API compatibility**: OpenSearch Query DSL is 99% compatible with Solr JSON Query syntax
- **Client library**: Migrate from SolrJ to the appropriate OpenSearch client for your platform
- **Effort per app**: 1-2 days per app (client library swap, index schema mapping)
- **Migration window**: 2 weeks; we provide runbooks and support
- **Fallback**: During cutover week, apps can instantly revert to Solr if needed

---

## Key Constraints and Risk Mitigations

### Backward Compatibility Window
- **Constraint**: Cannot deprecate Solr APIs immediately; existing apps need transition time
- **Mitigation**: Parallel operation for 2 weeks (both Solr and OpenSearch live); graceful shutdown of Solr after 1 month
- **Timeline**: Announce deprecation 3 months before; migration window 2 weeks; support window 1 month

### Zero-Downtime Requirement
- **Constraint**: Search is critical path for users; any downtime impacts revenue
- **Mitigation**:
  - Canary deployment (1% of traffic to OpenSearch for 24 hours)
  - Gradual rollout (10% → 50% → 100%) over 1 week
  - Automatic fallback to Solr if OpenSearch latency > 2x baseline or error rate > 1%
  - Maintain Solr read-only for 24 hours post-cutover (emergency rollback)

### Data Completeness During Migration
- **Constraint**: Solr cluster may receive writes during migration; we must not lose those writes
- **Mitigation**:
  - Phase 1: Bulk migrate all historical data (Solr → S3 → OpenSearch, ~10 TB)
  - Phase 2: Enable dual-write in application code (new docs go to both systems)
  - Phase 3: Kinesis stream captures deltas from Solr; Lambda writes to OpenSearch
  - Phase 4: Validate OpenSearch index completeness (document count matches Solr exactly)
  - Phase 5: Cutover application reads to OpenSearch

---

## Quality Metrics and Acceptance Criteria

### Search Latency SLO
- **p50 latency**: < 100 ms (vs. current Solr p50 ≈ 120 ms)
- **p95 latency**: < 500 ms (vs. current Solr p95 ≈ 600 ms)
- **p99 latency**: < 2000 ms (vs. current Solr p99 ≈ 3000 ms)
- **Measurement**: Sampled via Application Performance Monitoring (APM); tracked in CloudWatch

### Indexing Throughput
- **Target**: 1000 docs/sec sustained (matches current Solr baseline)
- **Peak**: 5000 docs/sec for 5 minutes without backlog
- **Measurement**: Via pipeline metrics; alert if queue depth > 10K

### Relevance Quality
- **Click-through rate**: Must not degrade > 2% post-migration
- **Query latency distribution**: p50, p95, p99 must not exceed Solr by more than 10%
- **Index freshness**: Documents indexed < 5 seconds from submission (vs. current 10 seconds)

### Availability
- **Uptime**: 99.95% (4.4 hours downtime/month acceptable)
- **Recovery time (RTO)**: < 10 minutes to restore service
- **Recovery point (RPO)**: < 1 hour (most recent snapshot)

### Operational Metrics
- **Platform team effort**: < 5 hours/month (down from 15-20)
- **MTTR (Mean Time To Recovery)**: < 30 minutes for common issues (vs. current 2+ hours with Solr)
- **Automated incident response**: Alerting for 90%+ of common failure modes

---

## Project Phases and Milestones

### Phase 1: Foundation (Weeks 1-4)
- **Goal**: Set up infrastructure, validate tooling
- **Work**:
  - Provision AWS OpenSearch domain (dev, staging, prod)
  - Set up VPC, security groups, IAM roles
  - Implement monitoring (CloudWatch dashboards, alerting)
  - Run load tests (1000 docs/sec, 1000 queries/sec)
  - Validate data migration tooling (Logstash, Glue, Lambda)
- **Milestone**: OpenSearch domain stable under baseline load; zero operational issues for 1 week

### Phase 2: Bulk Migration (Weeks 5-8)
- **Goal**: Migrate all historical data
- **Work**:
  - Export Solr collections to S3 (10-15 TB)
  - Run Logstash pipeline (3-5 Fargate tasks, parallel)
  - Validate index completeness (doc count, checksum)
  - Migrate search configurations (custom analyzers, boost rules)
  - Dry-run application deployment on OpenSearch (no production traffic yet)
- **Milestone**: 100% of historical data in OpenSearch; 10 sample apps tested against OpenSearch

### Phase 3: Dual-Write and Validation (Weeks 9-11)
- **Goal**: Enable production writes to both systems; validate consistency
- **Work**:
  - Deploy dual-write code to production (1 app, canary)
  - Run consistency checker (query both systems, compare results)
  - Monitor for discrepancies (alert if > 0.01% mismatch)
  - Fix bugs in field mapping, analysis, ranking
  - Gradual rollout to all 10 apps (1 app/day)
- **Milestone**: All apps dual-writing; zero consistency issues for 3 days

### Phase 4: Cutover (Week 12)
- **Goal**: Switch application reads to OpenSearch; validate in production
- **Work**:
  - Canary cutover (1% of traffic to OpenSearch, 99% to Solr)
  - Monitor latency, error rate, search quality metrics for 24 hours
  - Gradual rollout (10% → 25% → 50% → 100% over 3 days)
  - Automatic fallback if any SLO violated
  - Solr remains read-only for emergency rollback (1 week)
- **Milestone**: 100% of production traffic on OpenSearch for 24 hours with zero SLO violations

### Phase 5: Cleanup and Optimization (Week 13+)
- **Goal**: Retire Solr infrastructure; optimize OpenSearch for cost/performance
- **Work**:
  - Remove dual-write code from application
  - Disable Solr cluster (keep backups for 3 months)
  - Implement ISM policies (warm tier, auto-delete old data)
  - Fine-tune OpenSearch configuration (shard count, replica count, refresh interval)
  - Measure and report on success metrics
- **Milestone**: Solr retired; OpenSearch stable and cost-optimized

---

## Success Criteria (Go/No-Go Decision Points)

### End of Phase 1: Foundation
- ✅ OpenSearch domain passes load tests (1000 docs/sec, 1000 QPS, < 200 ms p95 latency)
- ✅ Monitoring dashboards created and operational
- ✅ No blocking security or VPC issues

### End of Phase 2: Bulk Migration
- ✅ All historical data migrated (doc count matches Solr exactly)
- ✅ Index size < 20% larger than Solr (acceptable overhead for replicas)
- ✅ 3+ production apps successfully queried against test OpenSearch instance

### End of Phase 3: Dual-Write and Validation
- ✅ All apps dual-writing; consistency rate > 99.99%
- ✅ No regressions in search relevance (click-through rate stable)
- ✅ Latency p50/p95/p99 match or exceed Solr baseline

### End of Phase 4: Cutover
- ✅ 100% of traffic on OpenSearch for >= 24 hours
- ✅ Zero SLO violations during cutover week
- ✅ Automatic fallback not triggered
- ✅ User-facing metrics (latency, relevance, availability) stable

### End of Phase 5: Cleanup
- ✅ Solr infrastructure retired
- ✅ OpenSearch cost optimized (ISM policies active, unnecessary shards removed)
- ✅ All operational runbooks documented
- ✅ Platform team trained and confident operating OpenSearch

---

## Budget and Resource Allocation

### Personnel (4-month project)
- **Search/Platform Team Lead**: 50% allocation (4 months)
- **Infrastructure Engineer**: 100% allocation (8 weeks, then 25% ongoing)
- **Application Engineers** (3-4): 20% allocation (2 weeks) for client library migration
- **DBA/Data Engineer**: 25% allocation (4 weeks) for bulk migration tooling

**Estimated effort**: 1.5 FTE-months

### Infrastructure Costs
- **OpenSearch Service**: $3,000-5,000/month (ongoing)
- **Logstash/Fargate** (migration only): $500 (3-week migration window)
- **S3 intermediate storage**: $200 (temporary)
- **Total Year 1**: ~$45,000 (including 12 months operation)

### Savings vs. Current State
- **Solr EC2 cluster**: ~$4,000/month (eliminated)
- **ZooKeeper EC2 cluster**: ~$2,000/month (eliminated)
- **Engineering overhead**: ~$5,000/month (15 hours × $100/hour) (reduced to ~$1,000/month)
- **Total Year 1 savings**: ~$95,000

**Net benefit Year 1**: $95,000 savings - $45,000 costs = **$50,000 ROI**

---

## Communication Plan

### Internal Stakeholders
- **Kickoff**: All-hands presentation; explain why, timeline, impact on each team
- **Bi-weekly updates**: Steering committee (platform, search, eng leadership)
- **Weekly syncs**: Technical working group (eng, infrastructure, security)
- **Pilot communication**: Email to app teams 1 week before their migration window

### External (if applicable)
- **Customer-facing**: No communication (internal infrastructure change)
- **Status page**: Note "planned maintenance window" during cutover week (if monitoring)

### Documentation
- **Runbooks**: How to migrate an app, how to troubleshoot latency, how to add a new index
- **Architecture decision records (ADRs)**: Why OpenSearch over Elasticsearch/others
- **Post-mortem**: After project completion; lessons learned
- **Training**: 2-hour workshop for platform team on OpenSearch operations

---

## Open Questions and Decisions Pending

1. **OpenSearch version**: Stick with latest AWS-supported (2.11+) or conservative (2.9)?
   - *Decision window*: Week 2
   - *Impact*: Affects plugin availability, feature set

2. **Provisioned vs. Serverless**: Cost/performance tradeoff for known workload
   - *Decision window*: Week 2
   - *Recommendation*: Start with provisioned (predictable performance); migrate to serverless later if workload becomes bursty

3. **Multi-region failover**: Do we need OpenSearch in secondary region immediately?
   - *Decision window*: Week 4 (Phase 1)
   - *Recommendation*: No; start with single region; add DR after Year 1 if ROI justifies

4. **Auth model**: IAM roles only, or internal user database + SAML?
   - *Decision window*: Week 3
   - *Recommendation*: IAM for apps; internal users for third-party tools; plan SAML later

5. **Kibana vs. alternative**: Use OpenSearch Dashboards or invest in Grafana?
   - *Decision window*: Week 4
   - *Recommendation*: OpenSearch Dashboards for initial rollout; evaluate alternatives post-migration

---

## Success Metrics Review Cadence

- **Weekly** (Weeks 1-4): Load test results, infrastructure readiness
- **Daily** (Weeks 5-12): Migration progress (%, docs/sec), data consistency
- **Hourly** (Week 12 cutover): Latency, error rate, search quality metrics
- **Post-cutover**: Bi-weekly until Month 3, then monthly

**Owner**: Platform Lead (with Search Team for relevance metrics)

---

## Rollback and Contingency Plan

### If Phase 1 Fails (Load Testing)
- **Action**: Escalate to AWS support; investigate infrastructure tuning
- **Fallback**: Delay project by 2 weeks; use AWS professional services for configuration review
- **Cost**: ~$5000 (AWS consulting)

### If Phase 2 Fails (Data Loss)
- **Action**: Re-run bulk migration from Solr backups; investigate root cause
- **Fallback**: Not applicable (data is backed up; migration is idempotent)
- **Timeline impact**: +1 week

### If Phase 3 Fails (High Mismatch Rate)
- **Action**: Debug field mapping; iterate on configuration
- **Fallback**: Delay Phase 4 (cutover) by 1 week; skip this app batch
- **Cost**: +1 week engineering time

### If Phase 4 Fails (Latency SLO Violated)
- **Action**: Automatic fallback to Solr (< 5 minutes); investigate scaling issues
- **Fallback**: Add more OpenSearch nodes; re-tune shard allocation
- **Timeline impact**: +1 week (re-attempt cutover with more resources)

### If Post-Cutover Issues Arise
- **Within 24 hours**: Automatic failover to Solr; detailed incident review
- **Within 1 week**: Keep Solr read-only; investigate and fix OpenSearch
- **After 1 week**: Solr shutdown; full OpenSearch support

---

## Appendix: Related Initiatives

- **Search relevance overhaul** (separate project, Q2 2024): Implement learning-to-rank, A/B testing framework
- **Observability initiative** (in progress): CloudWatch dashboards, alerting for all services
- **Cost optimization** (ongoing): AWS commitment discounts, reserved instance purchases
- **Security hardening** (in progress): Encryption, VPC Flow Logs, alerting for auth failures

---

**Document owner**: Platform Lead
**Last updated**: 2024-01-15
**Review cycle**: Quarterly (or as needed based on phase progress)
