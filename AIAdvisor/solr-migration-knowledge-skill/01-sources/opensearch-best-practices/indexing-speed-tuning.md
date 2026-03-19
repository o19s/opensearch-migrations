# Indexing Performance Tuning for OpenSearch

**Source:** https://docs.opensearch.org/latest/tuning-your-cluster/performance/

## Overview

Indexing performance is critical for write-heavy workloads (logs, metrics, events, real-time analytics). Thoughtful tuning of buffer sizes, refresh rates, and hardware allocation can yield 5-10x throughput improvements.

## Bulk API Optimization

### Batch Size Selection

The Bulk API is mandatory for high-throughput indexing. Optimal batch sizes depend on document size:

**Batch Size Guidelines**:
- **Target range**: 5-15 MB per batch (number of documents varies)
- **Measurement**: Monitor actual network throughput and GC pauses
- **Too small** (<1 MB): Excessive network round-trips, lower throughput
- **Too large** (>20 MB): Risk of OutOfMemoryError, GC pauses, slower error recovery

**Practical approach**:
```
Start with 1,000 documents or 5MB per batch, measure throughput, adjust up or down
```

### Concurrent Bulk Requests

- **Concurrency**: 2-4 concurrent bulk requests per data node
  - Example: 8-node cluster = 16-32 concurrent requests optimal
  - More concurrency risks overwhelming JVM memory, triggering aggressive GC
  - Fewer concurrent requests underutilizes cluster capacity

- **Backpressure handling**:
  - Implement exponential backoff on 429 responses (too many requests)
  - Track in-flight requests; stop submitting when count reaches concurrency limit
  - Monitor bulk request latency; if >5s, reduce concurrency

### Bulk Request Structure

Optimal format for performance:

```json
{"index": {"_index": "logs-2026-03", "_id": "doc-123"}}
{"timestamp": "2026-03-17T10:30:00Z", "level": "info", "message": "..."}
{"index": {"_index": "logs-2026-03"}}
{"timestamp": "2026-03-17T10:30:01Z", "level": "warn", "message": "..."}
```

- Omit `_id` when possible (cluster generates UUIDs faster than you parse them)
- Omit `_type` (deprecated; single type per index)
- Use consistent field ordering in documents (improves CPU cache locality)

## Refresh Interval Tuning

The `refresh_interval` determines how often new documents become searchable.

### Default Behavior

- **Default**: `1s` (new documents searchable within 1 second)
- **Cost**: Frequent refresh triggers segment creation, merge overhead
- **Trade-off**: Near real-time searchability vs. indexing throughput

### Tuning for Bulk Indexing

**During initial load or high-throughput periods**:

```json
PUT logs-2026-03/_settings
{
  "index.refresh_interval": "30s"
}
```

- Reduces refresh overhead by 30x
- Documents visible within 30 seconds (acceptable for logs)
- Increases throughput 2-3x

**During bulk ingestion of historical data**:

```json
PUT historical-logs/_settings
{
  "index.refresh_interval": "-1"
}
```

- Disables refresh entirely
- Highest throughput possible
- Restore after bulk load: `"index.refresh_interval": "1s"`

**Monitoring refresh impact**:
- Track `refresh` metric in slow logs
- If refresh >100ms, increase interval
- Segment count grows during disabled refresh; restore interval to trigger merges

## Replica Count Strategy

### Initial Load Phase

**During bulk ingestion**: Set `number_of_replicas: 0`

```json
PUT logs-2026-03/_settings
{
  "number_of_replicas": 0
}
```

- Eliminates replica shard replication overhead
- Speeds up indexing 2x (single copy per document)
- Safe for time-series data (can recreate from source)

**After bulk load completes**: Restore replicas for HA

```json
PUT logs-2026-03/_settings
{
  "number_of_replicas": 1
}
```

- Shard copying happens in background (monitored in cluster state)
- Cluster automatically allocates replicas across nodes
- Monitor `relocating_shards` in cluster health

### Replica Allocation Awareness

Ensure replicas don't land on same node as primaries:

```json
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.awareness.attributes": "rack_id"
  }
}
```

## Translog Configuration

The translog is the write-ahead log ensuring durability; tuning affects throughput vs. safety.

### Flush Strategy

**Async flush** (recommended for throughput):

```json
PUT _cluster/settings
{
  "persistent": {
    "index.translog.durability": "async",
    "index.translog.flush_threshold_size": "512mb",
    "index.translog.sync_interval": "5s"
  }
}
```

- `durability: async`: Writes don't wait for disk sync
- Increases throughput 10-20% over synchronous mode
- Risk: Up to 5 seconds of documents lost on abrupt node shutdown
- Acceptable for logs/metrics (data is often replicated elsewhere)

**Synchronous flush** (for critical data):

```json
{
  "index.translog.durability": "sync",
  "index.translog.sync_interval": "1s"
}
```

- Every bulk request waits for translog fsync
- Safer (no data loss on shutdown)
- 10-20% slower throughput

## Thread Pool Sizing

Thread pools handle bulk requests and indexing. Defaults are usually adequate, but tuning may help:

### Bulk Pool

The pool handling bulk requests:

```yaml
thread_pool.bulk.queue_size: 2000
thread_pool.bulk.size: number_of_cpu_cores
```

- Size = CPU cores (default, good for balanced systems)
- Queue size = max queued requests before rejecting (429 Too Many Requests)
- Increase queue only if you see legitimate request dropping; better to add concurrency limit on client side

### Index Pool

The pool handling indexing operations:

```yaml
thread_pool.index.size: number_of_cpu_cores
thread_pool.index.queue_size: 2000
```

- Usually no tuning needed (default works well)
- Monitor queue depth; if consistently full, CPU may be bottleneck

## Index Buffer Size

The in-memory buffer accumulating documents before flushing to disk:

```json
PUT _cluster/settings
{
  "persistent": {
    "indices.memory.index_buffer_size": "30%"
  }
}
```

- **Default**: 10% of JVM heap
- **For indexing-heavy clusters**: Increase to 20-30%
- **Formula**: `index_buffer_size * node_heap_size * number_of_nodes / number_of_shards` should be 100-500 MB per shard
- Larger buffers reduce merge frequency but risk OOM if misconfigured

## Merge Policy Tuning

Merges consolidate small segments into larger ones; tuning affects search performance vs. indexing speed.

### Log-Based Merge Policy (Default)

```json
PUT _cluster/settings
{
  "persistent": {
    "index.merge.policy.segments_per_tier": 10,
    "index.merge.policy.max_merge_at_once": 10,
    "index.merge.policy.floor_segment_size": "2mb"
  }
}
```

- `segments_per_tier`: Segments per tier before triggering merge (10-15 typical)
  - Lower = more frequent merges, better search performance, slower indexing
  - Higher = fewer merges, faster indexing, larger segment count
- `max_merge_at_once`: Max segments merged in single operation (10-30 typical)
  - Lower = smaller merges, lower memory cost
  - Higher = more aggressive consolidation
- `floor_segment_size`: Segments smaller than this are always merged (ignore tier settings)

### Merge Scheduling

```json
{
  "index.merge.scheduler.max_thread_count": 1
}
```

- For indexing-heavy workloads, limit concurrent merges to 1 (merges compete with indexing for CPU/IO)
- For search-heavy workloads, allow 2-4 merges in parallel

## Mapping Optimizations

### Disable _source Field

If original JSON not needed (only indexed fields queried):

```json
PUT logs-2026/_mappings
{
  "properties": {...},
  "_source": {
    "enabled": false
  }
}
```

- Reduces index size by 10-20%
- Documents cannot be retrieved with `_source` (must reconstruct from indexed fields)
- Use for logs where you only query, never retrieve raw event

### Use doc_values for Aggregations

Ensure aggregation-heavy fields have doc_values enabled:

```json
{
  "properties": {
    "status_code": {
      "type": "keyword",
      "doc_values": true
    },
    "response_time_ms": {
      "type": "integer",
      "doc_values": true
    }
  }
}
```

- Enables efficient aggregations on large datasets
- Defaults to true for most field types
- Adds disk overhead (~10% per field) but enables fast analytics

### Disable Analysis for Non-Searchable Fields

```json
{
  "properties": {
    "raw_payload": {
      "type": "keyword",
      "index": false,
      "doc_values": false
    }
  }
}
```

- `index: false`: Field not searchable
- `doc_values: false`: No aggregation support
- Reduces memory/storage for large unqueried fields

### Use Appropriate Field Types

- `keyword` for exact matches (faster than text for filtering)
- `integer/long` for numbers (faster aggregations than text)
- `date` for timestamps (enables date math queries)
- Avoid `text` for fields never full-text searched

## Hardware Recommendations

### CPU

- **Minimum**: 4 cores per data node
- **Recommended**: 8+ cores for indexing-heavy workloads
- Merges and compression are CPU-intensive

### Memory

- **JVM heap**: 50% of available RAM (rest for OS cache)
- **Maximum heap**: 32 GB (preserves compressed object pointers)
- **Per node**: Minimum 16 GB, recommended 32-64 GB for indexing
- Higher memory means larger index buffer, better OS caching of indices

### Storage

- **SSDs mandatory** (NVMe preferred for high throughput)
- **IOPS**: Minimum 3,000 IOPS (gp3), prefer 5,000+ for sustained indexing
- **Bandwidth**: Ensure storage can sustain 100+ MB/s writes
- **Capacity**: Leave 20-30% free space for merging overhead

### Network

- **Bandwidth**: 1 Gbps minimum between nodes; 10 Gbps for multi-node bulk ingestion
- **Latency**: <5 ms inter-node latency preferred (same datacenter/AZ)

## Monitoring Indexing Performance

### Key Metrics

- **Indexing rate** (docs/sec): Track with `GET _stats`
- **Bulk request latency**: p50, p99 should improve as settings optimize
- **Segment count**: `GET _cat/indices?v` shows segment count; should stabilize
- **GC pause time**: Monitor JVM; >100ms pauses indicate memory pressure
- **Merge time**: Sum of all merge operations; should stay <500ms/sec

### Diagnostic Queries

```json
GET _stats/indexing?pretty

GET _cat/indices?h=index,docs.count,store.size,segments.count
```

## Tuning Checklist for Maximum Throughput

1. Set `refresh_interval` to 30s or -1 during bulk load
2. Set `number_of_replicas` to 0 during bulk load
3. Use bulk API with 5-15 MB batches, 2-4 concurrent requests
4. Increase `index_buffer_size` to 20-30%
5. Set `translog.durability: async` for throughput-critical loads
6. Disable merges during load: `index.merge.scheduler.max_thread_count: 0` (restore after)
7. Scale hardware: 8+ CPU cores, 32+ GB heap, fast SSD storage
8. Monitor and adjust batch size; target 50-100 MB/sec per data node
