# Cutover Checklist

**Artifact ID:** `northwind-cutover-checklist-draft-v1`
**Status:** Draft only
**Warning:** This checklist is not active authority to cut over production traffic. It exists to show the operator-facing artifact that should be ready before a cutover approval gate.

## Preconditions

- judged relevance report approved
- shadow traffic report completed
- current risk register reviewed
- rollback owner on call
- product owner on call
- platform lead on call
- communication channel opened for command updates

## Live Checks Before Traffic Shift

- target cluster health green
- no active bulk rejections or sustained write throttling
- replay lag below agreed threshold
- document freshness within agreed tolerance
- error rate within baseline guardrail
- p95 and p99 latency within guardrail

## Controlled Shift Steps

1. Shift 5% production read traffic to OpenSearch path.
2. Hold for 15 minutes and review latency, errors, freshness, and sampled results.
3. Shift to 25% only if all guardrails remain healthy.
4. Hold for 30 minutes and repeat review.
5. Shift to 50% only with named approver confirmation in the command channel.
6. Hold for 30 minutes and repeat review.
7. Shift to 100% only after final human confirmation.

## Rollback Triggers

- critical functional failure in search or autocomplete
- sustained error-rate breach
- sustained p99 latency breach
- replay lag or freshness breach beyond threshold
- unexplained critical result regression reported during live sampling

## Rollback Actions

1. Return read traffic to Solr path.
2. Pause further migration-stage actions.
3. Capture telemetry snapshots and incident notes.
4. Record exact time, trigger, and observed impact.
5. Open human-led incident review before reattempting cutover.
