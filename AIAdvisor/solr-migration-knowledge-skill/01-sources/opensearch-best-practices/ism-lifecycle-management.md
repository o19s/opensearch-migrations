# Index State Management (ISM) and Lifecycle Policies

**Source:** https://docs.opensearch.org/latest/im-plugin/ism/policies/

## Overview

Index State Management (ISM) is a plugin that automates index lifecycle transitions: automatic rollover, tier transitions (hot→warm→cold), force merging, snapshots, and deletion. ISM policies eliminate manual intervention for time-series and log data.

## Policy Structure

### Core Concepts

**States**: Defined conditions and actions (hot, warm, cold, delete)
**Transitions**: Rules determining when to move between states
**Actions**: Operations executed when entering a state (rollover, forcemerge, snapshot, etc.)

### Basic Policy Schema

```json
PUT _ilm/policy/time-series-policy
{
  "policy": {
    "description": "Automated lifecycle for logs",
    "default_state": "hot",
    "states": {
      "hot": {
        "meta": {
          "description": "Actively indexed data"
        },
        "actions": [
          {
            "rollover": {
              "min_doc_count": 1000000,
              "min_index_age": "1d"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "warm",
            "conditions": {
              "min_index_age": "7d"
            }
          }
        ]
      },
      "warm": {
        "actions": [
          {
            "forcemerge": {
              "max_num_segments": 1
            }
          }
        ],
        "transitions": [
          {
            "state_name": "cold",
            "conditions": {
              "min_index_age": "30d"
            }
          }
        ]
      },
      "cold": {
        "actions": [],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {
              "min_index_age": "90d"
            }
          }
        ]
      },
      "delete": {
        "actions": [
          {
            "delete": {}
          }
        ]
      }
    }
  }
}
```

### State Components

**actions**: Operations performed upon entering state
- Executed sequentially
- Can depend on previous action completion (e.g., forcemerge then snapshot)
- Failures can trigger retries or state transitions

**transitions**: Conditions determining state exit
- Multiple transitions possible (first matching condition wins)
- Condition evaluation every `index_state_management_cycle_duration` (default 5 minutes)
- Supports time-based (`min_index_age`) and size-based (`min_doc_count`, `min_primary_shard_size`) conditions

## Common Lifecycle Pattern: Hot→Warm→Cold→Delete

### Hot Phase (Active Indexing)

```json
"hot": {
  "actions": [
    {
      "rollover": {
        "min_primary_shard_size": "50GB",
        "min_age": "1d",
        "min_doc_count": 1000000
      }
    },
    {
      "set_priority": {
        "priority": 100
      }
    }
  ],
  "transitions": [
    {
      "state_name": "warm",
      "conditions": {
        "min_index_age": "7d"
      }
    }
  ]
}
```

**Rollover triggers**:
- `min_primary_shard_size: 50GB`: New index if any primary shard exceeds 50 GB
- `min_age: 1d`: New index if current is >1 day old (even if small)
- `min_doc_count`: New index after N documents
- Rollover creates next-generation index: `logs-0001`, `logs-0002`, etc.

**Priority**:
- `priority: 100` ensures hot indices allocated to best nodes first
- Coordinating nodes and expensive operations avoid hot indices

### Warm Phase (Optimized for Search)

```json
"warm": {
  "actions": [
    {
      "set_priority": {
        "priority": 50
      }
    },
    {
      "forcemerge": {
        "max_num_segments": 1
      }
    },
    {
      "shrink": {
        "number_of_shards": 1
      }
    }
  ],
  "transitions": [
    {
      "state_name": "cold",
      "conditions": {
        "min_index_age": "30d"
      }
    }
  ]
}
```

**Actions**:

- **set_priority**: Deprioritize to cheaper nodes (might have slower disk)
- **forcemerge**: Consolidate all segments into 1 (improves search speed, reduces CPU overhead)
  - No new documents written (index is read-only now)
  - Reduces memory usage (fewer segment metadata objects)
  - One segment = one large file (better compression)
- **shrink**: Reduce shard count (consolidates data, simplifies operations)
  - Prerequisite: Index must be read-only
  - Example: Hot phase had 5 shards; warm shrinks to 1

### Cold Phase (Archive/Infrequent Search)

```json
"cold": {
  "actions": [
    {
      "searchable_snapshot": {
        "snapshot_repository": "s3-repo"
      }
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
}
```

**searchable_snapshot action**:
- Snapshot index to S3 (or other repository)
- Index data lives in S3, not on cluster
- Queries fetch data on-demand from S3
- Massive storage savings (S3 costs ~$0.023/GB/month vs. $0.10+/GB/month for hot storage)
- Latency increases slightly (S3 access time ~10-100ms vs. local disk <1ms)
- Best for cold data (infrequent ad-hoc analytics, compliance audits)

### Delete Phase (Retention Enforcement)

```json
"delete": {
  "actions": [
    {
      "delete": {}
    }
  ]
}
```

- Deletes index entirely (frees all storage)
- Clean deletion (vs. individual document deletes)
- Essential for compliance (GDPR, CCPA retention windows)

## Rollover Action: Advanced Tuning

### Rollover Conditions

**Size-based rollover** (most common):

```json
"rollover": {
  "min_primary_shard_size": "50GB",
  "min_doc_count": 100000000
}
```

- Rolls over when any primary shard exceeds 50 GB
- Best for search workloads (keeps shard size reasonable)
- Example: logs-000001 (1 shard 50GB) rolls to logs-000002 (1 shard, <1GB)

**Time-based rollover**:

```json
"rollover": {
  "min_age": "1d"
}
```

- Rolls over every 1 day regardless of size
- Best for logs (consistent 1 day of data per index)
- Simpler operations (know exactly 1 day per index)
- Risk: Small indices (wasted shard metadata)

**Hybrid approach** (recommended):

```json
"rollover": {
  "min_age": "1d",
  "min_primary_shard_size": "50GB",
  "min_doc_count": 100000
}
```

- Rolls over if ANY condition met
- Prevents undersized indices (need 100K docs minimum)
- Prevents oversized indices (50 GB max)
- Cleans up on daily boundary (operational simplicity)

### Rollover Alias Pattern

Rollover works through aliases:

```json
PUT logs-000001
{
  "settings": {
    "index.lifecycle.name": "logs-policy",
    "index.lifecycle.rollover_alias": "logs"
  },
  "aliases": {
    "logs": {"is_write_index": true}
  }
}
```

- `is_write_index: true`: Bulk API targets `logs` alias (maps to active index)
- Rollover creates `logs-000002`, updates alias
- Application queries `logs` alias (transparently gets current index)

## Force Merge in Warm State

### Segment Consolidation

**Background**:
- Indexing creates segment files (one per bulk request)
- Segments are immutable (deleted docs marked, but take space)
- Multiple segments = overhead (CPU scanning segment metadata)

**forcemerge action**:

```json
"forcemerge": {
  "max_num_segments": 1
}
```

- Consolidates all segments into single file
- Removes deleted documents (actual disk space recovery)
- Expensive operation (CPU/disk intensive)
- Reduces query latency 10-20% (single segment = linear search, better CPU cache)

### When to Forcemerge

- **Always in warm**: Index is read-only; no new data; safe to consolidate
- **Not in hot**: Active indexing; merging competes for resources
- **Optional in cold**: If querying cold data frequently, may help
- **Never force merge during peak hours**: Can slow queries significantly

### Performance Impact

```
Before forcemerge:
  - 500 segments per index
  - Query touches all 500
  - CPU scanning segment metadata
  
After forcemerge:
  - 1 segment
  - Single linear scan
  - 10-20% faster queries
  - Cluster can handle 2-3x more concurrent queries
```

## Read-Only Transitions

### Marking Indices as Read-Only

Some patterns prevent writes after hot phase:

```json
"warm": {
  "actions": [
    {
      "index_priority": {
        "priority": 50
      }
    },
    {
      "index_priority": {
        "priority": 0
      }
    }
  ]
}
```

But better approach: Use explicit read-only block:

```json
PUT logs-2026-03/_settings
{
  "index.blocks.write": true
}
```

- Prevents accidental writes to old data
- Reduces confusion (writes clearly fail)
- Recommended for compliance workloads (audit trail)

## Shrink Action for Shard Reduction

### Shrinking Shards in Warm Phase

```json
"warm": {
  "actions": [
    {
      "shrink": {
        "number_of_shards": 1
      }
    }
  ]
}
```

**Prerequisites**:
- Index must be read-only
- All shards must be on same node (ISM handles reallocation automatically)

**Example workflow**:
1. Hot phase: logs-000123 with 5 primary shards
2. Rollover to logs-000124 (new index, new shards)
3. logs-000123 transitions to warm
4. Shrink action: Consolidate 5 shards → 1 shard
5. Result: logs-000123 now has 1 shard (80% shard metadata reduction)

**Benefits**:
- Reduces cluster state size (100 indices × 5 shards = 500 shards; shrink to 1 = 100 shards)
- Simplifies operations (fewer shards to manage)
- Saves memory (shard metadata no longer needed)

**Drawback**: Requires reallocation (slight latency increase during shrink, then faster queries)

## Snapshot Before Delete Pattern

### Backup Compliance

```json
"cold": {
  "actions": [
    {
      "snapshot": {
        "repository": "s3-repo",
        "snapshot": "snapshot-{{index | urlencode}}-{{now/d}}"
      }
    }
  ]
}

"delete": {
  "actions": [
    {
      "delete": {}
    }
  ]
}
```

**Pattern**:
1. Index enters cold phase (older than 30 days)
2. Snapshot action creates backup in S3 (incremental, typically 5-10% of index size)
3. Index aged beyond retention (90 days)
4. Delete action removes index from cluster
5. Backup in S3 retained for compliance/audit (indefinite or per policy)

**Cost**: Snapshot storage << hot storage (S3 is cheap; hot nodes are expensive)

## ISM Job Interval and Tuning

### Default Cycle Duration

```yaml
index_state_management_cycle_duration: 300000  # 5 minutes (default)
```

- ISM checks transitions every 5 minutes
- If index age is "1d", check happens every 5 min (max 5 min delay in state transition)
- Trade-off: More frequent checks = more CPU; less frequent = operational latency

### Adjusting Cycle Duration

**For fast-moving data**:

```json
PUT _cluster/settings
{
  "persistent": {
    "index_state_management_cycle_duration": "60000"  # 1 minute
  }
}
```

- Reduces delay from hot→warm transition
- Useful for critical SLAs (must transition exactly at threshold)
- Increases cluster CPU load slightly

**For stable data**:

```json
{
  "index_state_management_cycle_duration": "600000"  # 10 minutes
}
```

- Reduces overhead (fewer state checks)
- Acceptable latency (OK if warm transition is 5-10 min late)
- Better for very large clusters (reduced coordination overhead)

## Error Handling and Retry Policies

### Action Failures

If an action fails (e.g., forcemerge fails due to disk full):

```json
{
  "action": {
    "retry": {
      "count": 3,
      "backoff": "exponential",
      "delay": "1m"
    }
  }
}
```

**Retry behavior**:
- `count: 3`: Retry up to 3 times
- `backoff: exponential`: Wait 1m, 2m, 4m between retries
- If retries exhausted: State stalls (manual intervention needed)

### Manual Intervention

If index stuck in state:

```json
POST /logs-2026-03/_ilm/move
{
  "state": "warm"
}
```

- Forces transition to specific state
- Useful for unblocking stuck indices
- Use cautiously (bypasses normal state logic)

### Monitoring Policy Failures

```json
GET _ilm/status
```

Returns policy execution status, failed indices, retry counts.

## Practical Policy Examples

### Search Workload (Short Retention, High Performance)

```json
{
  "policy": {
    "default_state": "hot",
    "states": {
      "hot": {
        "actions": [
          {
            "rollover": {
              "min_primary_shard_size": "30GB",
              "min_age": "3d"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {"min_index_age": "7d"}
          }
        ]
      },
      "delete": {
        "actions": [{"delete": {}}]
      }
    }
  }
}
```

**Characteristics**:
- Shorter shard size (30 GB for better parallelism)
- Quick deletion (7-day retention)
- Single hot phase (no cold storage)
- Best for: Real-time dashboards, short-term analytics

### Logging Workload (Long Retention, Cost-Optimized)

```json
{
  "policy": {
    "default_state": "hot",
    "states": {
      "hot": {
        "actions": [
          {
            "rollover": {
              "min_primary_shard_size": "50GB",
              "min_age": "1d"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "warm",
            "conditions": {"min_index_age": "7d"}
          }
        ]
      },
      "warm": {
        "actions": [
          {
            "set_priority": {"priority": 50}
          },
          {
            "forcemerge": {"max_num_segments": 1}
          },
          {
            "shrink": {"number_of_shards": 1}
          }
        ],
        "transitions": [
          {
            "state_name": "cold",
            "conditions": {"min_index_age": "30d"}
          }
        ]
      },
      "cold": {
        "actions": [
          {
            "searchable_snapshot": {
              "snapshot_repository": "s3-repo"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {"min_index_age": "90d"}
          }
        ]
      },
      "delete": {
        "actions": [{"delete": {}}]
      }
    }
  }
}
```

**Characteristics**:
- Hot: 1 day (current logs only)
- Warm: 7-30 days (searchable, optimized for analytics)
- Cold: 30-90 days (S3-backed, minimal cost)
- 90+ days: Deleted (compliance window)
- Best for: Long-term log retention, audit trails

### Multi-Tenant SaaS (Per-Customer Retention)

```json
{
  "policy": {
    "default_state": "hot",
    "states": {
      "hot": {
        "actions": [
          {
            "rollover": {
              "min_primary_shard_size": "25GB",
              "min_age": "1d"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {"min_index_age": "${retention_days}"}
          }
        ]
      },
      "delete": {
        "actions": [{"delete": {}}]
      }
    }
  }
}
```

**Characteristics**:
- Simple policy (hot → delete)
- Retention tunable per customer (policies can reference dynamic variables)
- No cold tier (cost-optimized for many small customers)
- Best for: SaaS multi-tenant logs
