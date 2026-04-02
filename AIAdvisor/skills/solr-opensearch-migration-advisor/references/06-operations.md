# Operations: Migration Runbook and Steady-State Readiness
**Scope:** Operational posture for running OpenSearch safely during and after migration: preflight checks, monitoring, alerting, shard and storage health, indexing/search workload control, cutover watch, rollback readiness, and handoff to steady-state operations. Covers operator-facing migration workflows rather than cluster provisioning detail.
**Audience:** Platform engineers, SREs, search engineers, and migration leads
**Last reviewed:** 2026-03-20 | **Reviewer:** AI draft — expanded for operator-facing use

---

## Key Judgements

- **A migration is not production-ready because the cluster is green.** Green only means the allocation state is acceptable. It does not mean latency, ranking quality, replay lag, or rollback posture are healthy.
- **Operational readiness starts before cutover day.** If dashboards, alerts, slow logs, and rollback ownership are not established in advance, the cutover will be governed by guesswork.
- **The biggest operations mistake is treating throughput and relevance as separate worlds.** Many migration incidents are mixed failures: a cluster under write pressure starts showing stale results, odd ranking, or timeouts that users interpret as search-quality regression.
- **Managed service does not eliminate operational design.** AWS OpenSearch removes some infrastructure burden, but it does not remove the need for shard discipline, storage headroom, traffic shaping, or recovery planning.
- **Most migrations need boring operations more than clever operations.** Clear thresholds, explicit dashboards, and simple rollback criteria beat sophisticated but fragile observability every time.
- **A rollback path you have not rehearsed is just a comforting story.** If the team cannot say exactly who will roll back, how, and under what thresholds, it is not ready to cut over.
- **Slow logs are not just a tuning tool; they are a migration safety tool.** During shadowing and cutover, they often reveal the specific query families that are about to become user-visible failures.
- **Operational handoff is part of migration success.** If the post-migration team cannot explain alerts, shard posture, index versioning, and relevance asset ownership, the migration has not actually finished.

---

## Operating Goals

During migration, operations should answer these questions continuously:

1. Is the cluster healthy enough to keep serving and indexing?
2. Are queries behaving within expected latency and error tolerances?
3. Is the target staying current with source-side reality?
4. Are we approaching thresholds that should pause, slow, or roll back the migration?
5. Can the steady-state team run this without the migration team standing over them?

If operations cannot answer those questions quickly, observability is still immature.

---

## Migration Operations Lifecycle

### Phase 1: Preflight

Before meaningful migration activity:

- dashboards exist
- alert thresholds exist
- logging is enabled where needed
- rollback owner is named
- runbooks exist for the most likely failure classes

### Phase 2: Build and Backfill

Watch:

- indexing throughput
- bulk rejection
- storage growth
- merge pressure
- refresh/segment behavior

### Phase 3: Shadow / Limited Live Validation

Watch:

- latency delta vs source
- query errors/timeouts
- result-shape anomalies
- replay lag / freshness
- slow query patterns

### Phase 4: Cutover

Watch:

- user-facing query latency
- error spikes
- critical query behavior
- cluster stability under live load
- rollback trigger thresholds

### Phase 5: Stabilization and Handoff

Watch:

- alert quality
- capacity trend
- lingering operational debt
- ownership transfer

---

## Preflight Checklist

Do not proceed into live migration stages until these are in place.

### Monitoring and Logging

- [ ] cluster health visibility
- [ ] node CPU / memory / storage visibility
- [ ] indexing and search latency visibility
- [ ] slow logs enabled at reasonable thresholds
- [ ] application-side error visibility
- [ ] query timeout visibility

### Capacity and Safety

- [ ] storage headroom confirmed
- [ ] shard posture reviewed
- [ ] replica posture reviewed
- [ ] snapshot/restore plan verified
- [ ] rollback owner named
- [ ] rollback conditions written down

### Human Readiness

- [ ] on-call or watcher assignments during cutover window
- [ ] acceptance owner available
- [ ] escalation path defined
- [ ] runbook location known to the team

If several of these are missing, the migration is not yet in execution mode; it is still in preparation.

---

## Core Metrics To Watch

Use a compact set first. Add more only when they answer a real question.

### Cluster Health

- cluster status
- node count
- shard allocation state
- unassigned shards

This tells you whether the cluster is structurally stable. It does not tell you whether users are having a good experience.

### Storage and Shard Pressure

- free storage
- disk used percent
- shard count per node
- segment/merge pressure

These are early warnings for degraded performance and allocation problems.

### Search Performance

- p50 / p95 / p99 search latency
- query timeout rate
- search rejection/thread-pool pressure where relevant
- slow query log volume

This is the operator's main view of user-facing search health.

### Indexing Performance

- indexing throughput
- bulk failure/rejection rate
- refresh behavior
- replay lag or ingestion freshness indicators

This matters most during backfill, dual-write, and replay.

### Migration-Specific Indicators

- document-count parity trend
- critical-query smoke test results
- shadow diff sample results
- replay lag or catch-up distance

These are the signals that connect infrastructure health to migration correctness.

---

## Alerting Posture

Alerts should answer "what action should we consider now?" Avoid noisy alarms with no decision attached.

### Must-Have Alerts

- cluster health transitions to yellow/red unexpectedly
- storage headroom below agreed threshold
- sustained JVM / memory pressure
- search p99 above agreed limit
- indexing failures or bulk rejection spike
- replay lag exceeds agreed freshness budget
- high timeout or error-rate increase during shadow/cutover

### Good Alert Design

Each alert should name:

- what crossed threshold
- likely impact
- first operator action
- where to look next

If an alert cannot tell an operator what to do next, it is only half-designed.

---

## Slow Log and Query Triage Workflow

When query latency spikes:

1. Confirm it is not a broad cluster issue first
2. Check whether the spike is isolated to specific query families
3. Inspect slow logs for recurring patterns
4. Identify whether the problem is:
   - a mapping/model issue
   - an analyzer/query issue
   - an aggregation/sort issue
   - a shard/storage pressure issue
5. Decide whether to:
   - continue and monitor
   - tune and retry
   - pause the migration stage
   - roll back exposure

During migration, slow logs are especially useful for exposing underrepresented query patterns that slipped through offline validation.

---

## Workload Shaping Rules

### During Bulk Backfill

Prefer:

- larger refresh intervals or temporarily disabled refresh where appropriate
- controlled bulk sizing
- staged worker concurrency
- explicit monitoring of rejection and merge pressure

Do not maximize throughput blindly. The goal is sustainable indexing without destabilizing the cluster.

### During Shadow or Live Traffic

Prefer:

- conservative query concurrency increases
- staged rollout
- slow-query review
- explicit protection of critical business flows

If backfill and live traffic compete, the migration should favor user experience and data correctness over raw throughput.

---

## Document Count and Freshness Validation

Do not rely on a single count check at the end.

Use repeated validation:

- total document count comparison
- sampled key-segment counts
- freshness or lag checks over recent updates
- duplicate / missing record probes on known IDs

Count parity alone is not enough, but lack of parity is a strong warning sign.

If counts are drifting and the team cannot explain why, pause before increasing live exposure.

---

## Cutover Watch Window

Treat cutover as a watch window, not a single switch flip.

### First 15 Minutes

Watch:

- critical user journeys
- search latency and timeout changes
- error spikes
- cluster instability indicators

### First Hour

Watch:

- top business queries
- freshness behavior
- replay/catch-up state if relevant
- operator cognitive load: are alerts understandable or chaotic?

### First Day

Watch:

- tail latency under normal traffic variation
- slow query patterns not seen during shadowing
- support tickets and user complaints
- storage and segment growth under sustained load

The watch window should have named humans on point. "We’ll keep an eye on it" is not a staffing plan.

---

## Rollback Posture

### Rollback Should Be Prepared Before Cutover

Define:

- who can call rollback
- what thresholds trigger rollback discussion
- what exact steps return reads to the source path
- how long rollback is expected to take
- what happens to writes during or after rollback

### Common Rollback Triggers

- critical query path failure
- sustained p99 regression beyond tolerance
- unexplained timeout/error spike
- freshness or replay failure that affects user trust
- critical business stakeholder rejection with evidence

### Important Distinction

Not every issue requires full rollback. Some require:

- pause in rollout progression
- reduced traffic percentage
- temporary query-path fallback

Use the smallest safe corrective action first, but do not hesitate to roll back if user trust is at risk.

---

## Handoff to Steady-State Operations

Migration is not complete until steady-state operators inherit:

- dashboards they understand
- alerts they can act on
- index/versioning conventions
- snapshot/restore procedure
- shard/capacity posture
- relevance asset ownership
- runbooks for common incidents

### Handoff Checklist

- [ ] steady-state owner named
- [ ] dashboards reviewed with the owner
- [ ] alert thresholds reviewed
- [ ] index/alias strategy explained
- [ ] rollback and restore procedures explained
- [ ] relevance assets and owners documented
- [ ] known risks and operational debt logged

---

## Decision Heuristics

- **If you do not have dashboards for latency, storage, and failures, do not cut over.** You are flying blind.
- **If slow logs show recurring expensive query families, investigate before increasing traffic.** Do not wait for users to teach you what is slow.
- **If indexing pressure is harming live search, slow the migration workload before you optimize the cluster.** User-facing stability wins first.
- **If the rollback threshold is vague, rewrite it before cutover.** Operators need trigger conditions, not vibes.
- **If the post-migration team cannot explain the runbook, the handoff is not done.** Documentation alone is not transfer.

---

## Common Mistakes

- assuming cluster green means cutover-safe
- enabling migration stages without clear rollback authority
- chasing every metric instead of focusing on a compact control set
- pushing backfill too hard and degrading live search
- noticing slow-query patterns but treating them as a post-cutover problem
- treating operational handoff as documentation upload instead of operator readiness

---

## Open Questions / Evolving Guidance

- Which migration-specific dashboards should become standard artifacts in the repo’s worked examples?
- What default thresholds should be recommended for different migration sizes and risk classes?
- How should this runbook evolve for hybrid/vector search workloads where query latency profiles differ materially?
