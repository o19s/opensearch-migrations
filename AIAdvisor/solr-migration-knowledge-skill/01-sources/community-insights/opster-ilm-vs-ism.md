# Elasticsearch ILM vs OpenSearch ISM: Index Lifecycle Management Comparison

## Overview
Both Elasticsearch (ILM - Index Lifecycle Management) and OpenSearch (ISM - Index State Management) provide automated policy-driven index management for time-series data, logs, and other data with lifecycle patterns. This guide explains their architecture, capabilities, and migration considerations.

## Conceptual Differences

### Elasticsearch ILM (Index Lifecycle Management)
- **Introduced**: Elasticsearch 6.6
- **Purpose**: Automate index management through defined phases
- **Model**: Phase-based (hot → warm → cold → delete)
- **Trigger**: Time-based primarily (can be size or doc count)
- **Philosophy**: Reduce manual index management; optimize storage costs

### OpenSearch ISM (Index State Management)
- **Introduced**: Early OpenSearch (forked from Elasticsearch 7.10)
- **Purpose**: Policy-driven state machine for indices
- **Model**: State-based (arbitrary states, transitions on conditions)
- **Trigger**: Time, doc count, index size, or custom conditions
- **Philosophy**: More flexible state machine allowing arbitrary state definitions

## Architecture Comparison

### ILM Phase Model (Elasticsearch)
```
HOT → WARM → COLD → DELETE
 ↓     ↓      ↓       ↓
Hot Phase  Warm Phase  Cold Phase  Delete
(Index)    (Replicas)  (Archive)   (Remove)
```

**Phases:**
- **Hot**: Actively written to, full replicas, optimized for write performance
- **Warm**: No longer written to, higher replica count, searchable
- **Cold**: Rarely accessed, minimal replicas, searchable (with cost)
- **Delete**: Index deleted entirely

**Transitions:** Time-based or size-based conditions trigger phase advancement

### ISM State Machine Model (OpenSearch)
```
CREATION → <STATE A> → <STATE B> → <STATE C> → DELETE
            ↓          ↓          ↓
        Custom actions based on conditions
        Arbitrary state names and transitions
```

**States:**
- **User-defined**: Arbitrary number of states with custom names
- **Conditions**: Time, doc count, size, or custom Groovy scripts
- **Transitions**: Can move between any states (not linear)
- **Actions**: Per-state actions (rollover, shrink, force merge, etc.)

## Feature Comparison

### ILM Features
| Feature | Support | Notes |
|---------|---------|-------|
| **Automatic rollover** | ✅ Yes | Hot phase exclusive |
| **Force merge** | ✅ Yes | Warm/cold phase |
| **Shrinking** | ✅ Yes | Warm/cold phase |
| **Tiered storage** | ✅ Yes | Map phases to node tiers |
| **Lifecycle reset** | ✅ Yes | Return to hot phase |
| **Delete policy** | ✅ Yes | Time or age-based |
| **Custom conditions** | ❌ No | Predefined phase logic only |
| **Arbitrary states** | ❌ No | Fixed 4-phase model |
| **State machines** | ❌ No | Linear progression only |

### ISM Features
| Feature | Support | Notes |
|---------|---------|-------|
| **Automatic rollover** | ✅ Yes | State-based |
| **Force merge** | ✅ Yes | Any state |
| **Shrinking** | ✅ Yes | Any state |
| **Tiered storage** | ✅ Yes | Via state transitions |
| **Lifecycle reset** | ✅ Yes | State machine supports loops |
| **Delete policy** | ✅ Yes | Time or age-based |
| **Custom conditions** | ✅ Yes | Groovy script support |
| **Arbitrary states** | ✅ Yes | Define custom state names |
| **State machines** | ✅ Yes | Complex transitions |

## Configuration Examples

### ILM: Simple Log Index Policy
```json
{
  "policy": "logs-policy",
  "phases": {
    "hot": {
      "min_age": "0d",
      "actions": {
        "rollover": {
          "max_primary_shard_size": "50GB",
          "max_age": "1d"
        },
        "set_priority": {
          "priority": 100
        }
      }
    },
    "warm": {
      "min_age": "30d",
      "actions": {
        "force_merge": {
          "max_num_segments": 1
        },
        "set_priority": {
          "priority": 50
        }
      }
    },
    "cold": {
      "min_age": "90d",
      "actions": {
        "set_priority": {
          "priority": 0
        }
      }
    },
    "delete": {
      "min_age": "365d",
      "actions": {
        "delete": {}
      }
    }
  }
}
```

### ISM: Equivalent Log Index Policy
```json
{
  "policy": {
    "policy_type": "index",
    "description": "Logs lifecycle policy",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [
          {
            "rollover": {
              "min_size": "50gb",
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
            "force_merge": {
              "max_num_segments": 1
            }
          }
        ],
        "transitions": [
          {
            "state_name": "cold",
            "conditions": {
              "min_index_age": "90d"
            }
          }
        ]
      },
      {
        "name": "cold",
        "actions": [],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {
              "min_index_age": "365d"
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
        ],
        "transitions": []
      }
    ]
  }
}
```

## Migration from ILM to ISM

### Direct Translation Strategy
1. **Map ILM phases to ISM states** (hot → warm → cold → delete)
2. **Convert min_age to min_index_age** in transition conditions
3. **Convert max_age, max_size to ISM equivalents** in rollover conditions
4. **Review custom actions**: ISM supports more flexibility

### Common Pitfalls
- **Condition evaluation**: ILM checks conditions periodically; ISM does same (typically every 5 minutes)
- **Priority semantics**: ILM set_priority is action; ISM doesn't have direct equivalent
- **Allocation rules**: ILM uses tier allocation; ISM uses require tag routing
- **Naming changes**: Condition field names differ slightly (min_age vs min_index_age)

### Example Translation

**ILM condition:**
```json
"min_age": "30d"
```

**ISM equivalent:**
```json
"min_index_age": "30d"
```

## Operational Differences

### ILM Management (Elasticsearch)
```bash
# Get ILM status
GET _ilm/status

# Get policy
GET _ilm/policy/my-policy

# Remove policy
DELETE _ilm/policy/my-policy

# Explain index status
GET my-index-000001/_ilm/explain
```

### ISM Management (OpenSearch)
```bash
# Get ISM status
GET _plugins/_ism/status

# Get policy
GET _plugins/_ism/policies/my-policy

# Remove policy
DELETE _plugins/_ism/policies/my-policy

# Explain index status
GET my-index-000001/_plugins/_ism/explain
```

## Performance & Scalability Considerations

### ILM Performance
- **Overhead**: Minimal; built into core Elasticsearch
- **Scale**: Handles thousands of indices efficiently
- **Evaluation frequency**: Default 10-minute checks
- **Bottleneck**: Large number of rollover operations (single coordinator)

### ISM Performance
- **Overhead**: Slightly higher (plugin-based), but minimal
- **Scale**: Same as ILM, can handle thousands of indices
- **Evaluation frequency**: Configurable, default 5 minutes
- **Bottleneck**: Custom Groovy scripts in conditions can slow evaluation

## When to Use Each

### Use ILM (Elasticsearch)
- Standard hot-warm-cold-delete lifecycle
- Cluster running Elasticsearch
- Prefer battle-tested, widely-adopted approach
- No need for custom state machines

### Use ISM (OpenSearch)
- Complex lifecycle with multiple states
- Custom conditions or conditional logic needed
- Running OpenSearch (required)
- Need more flexibility in state transitions
- Want Groovy script customization

## Migration Recommendations

### For Elasticsearch users considering OpenSearch
1. **Evaluate lifecycle complexity**: Simple cases translate easily
2. **Plan migration timeline**: Convert ILM to ISM simultaneously with cluster migration
3. **Test state transitions**: Verify condition logic works identically
4. **Monitor evaluation**: Watch ISM evaluation logs post-migration
5. **Performance testing**: Verify no slowdown in large index counts

### Best Practices Post-Migration
- Start with simple policies (hot → warm → cold → delete)
- Add complexity only when needed
- Use metrics and monitoring to track policy execution
- Document custom state names and transitions
- Version control policy definitions

## Conclusion
Both ILM and ISM accomplish similar goals but with different models:
- **ILM**: Simpler, phase-based, Elasticsearch standard
- **ISM**: More flexible, state-machine based, OpenSearch standard

Migration is straightforward for standard use cases; complexity arises with custom lifecycle logic requiring ISM's flexibility.
