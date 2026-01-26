# Sentinel Performance & Scale Bounds

> **v1 states its limits honestly.**

---

## Purpose

Enterprise users trust tools that admit limits. This document defines Sentinel's performance characteristics and scale boundaries.

---

## Trace Limits

### Per Execution

| Metric | Recommended | Hard Limit |
|--------|-------------|------------|
| Traces per execution | ≤ 100 | 1,000 |
| Execution graph nodes | ≤ 100 | 1,000 |
| Execution graph edges | ≤ 200 | 5,000 |

**Above hard limit**: Performance degrades, UI may lag.

### Per Day

| Metric | Recommended | Notes |
|--------|-------------|-------|
| Total traces | ≤ 10,000 | Per day directory |
| Total size | ≤ 1 GB | JSON files |

---

## Graph Limits

### Visualization

| Metric | Recommended | Hard Limit |
|--------|-------------|------------|
| Visible nodes | ≤ 50 | 200 |
| Stages | ≤ 10 | 50 |

**Above limit**: Use hierarchical stages to collapse.

### Computation

| Operation | Time Complexity | Recommended Limit |
|-----------|-----------------|-------------------|
| `from_traces()` | O(n) | 100 traces |
| `compute_verdict()` | O(n) | 100 nodes |
| `compute_hash()` | O(n) | 100 nodes |
| `critical_path()` | O(n + e) | 100 nodes, 200 edges |
| `investigation_path()` | O(n) | 100 nodes |

---

## Storage

### File System

| Metric | Expected |
|--------|----------|
| Per trace JSON | 2-10 KB |
| Per day (100 traces) | 200 KB - 1 MB |
| Per month (3000 traces) | 6-30 MB |

### SQLite Index

| Metric | Expected |
|--------|----------|
| Index size | ~10 KB per 1000 traces |
| Query time (by ID) | < 1 ms |
| Query time (list) | < 10 ms |

### Cleanup Recommendation

```bash
# Traces older than 90 days can be archived
find ~/.sentinel/traces -mtime +90 -delete
```

---

## API Response Times

### Typical Latencies

| Endpoint | Expected | Notes |
|----------|----------|-------|
| `GET /v1/traces` | < 50 ms | First 50 traces |
| `GET /v1/traces/{id}` | < 10 ms | By ID |
| `GET /v1/executions` | < 50 ms | List |
| `GET /v1/executions/{id}/graph` | < 100 ms | Small graphs |
| `POST /v1/replay/{id}` | Variable | Depends on LLM |

### Degradation Thresholds

| Condition | Expected Impact |
|-----------|-----------------|
| > 10,000 traces | List queries slow |
| > 100 nodes/graph | Graph render slow |
| > 1 GB storage | Startup slower |

---

## Memory Usage

### Server

| Component | Expected |
|-----------|----------|
| Base FastAPI | 50-100 MB |
| Per trace loaded | ~10 KB |
| Graph computation | ~1 MB per 100 nodes |

### Recommendations

- Keep server memory < 500 MB
- Restart server weekly if running long
- Use pagination for large trace lists

---

## Client Limits

### CLI

| Command | Expected Time |
|---------|---------------|
| `sentinel list` | < 1 s |
| `sentinel show <id>` | < 1 s |
| `sentinel check` | < 5 s per golden |
| `sentinel replay` | Variable (LLM) |

### UI

| Operation | Expected |
|-----------|----------|
| Initial load | < 2 s |
| Trace list | < 500 ms |
| Graph render | < 1 s (small) |
| Forensics mode toggle | < 200 ms |

---

## Scaling Guidance

### When to Optimize

| Symptom | Solution |
|---------|----------|
| UI feels slow | Reduce visible nodes |
| Queries slow | Index older traces |
| Storage growing | Archive old traces |
| Memory high | Restart server |

### When to Split

Consider multiple Sentinel instances when:
- > 100,000 traces total
- > 10 concurrent users
- > 10 executions/minute

---

## Benchmarks

Measured on: Intel i7, 16GB RAM, SSD

| Scenario | Result |
|----------|--------|
| 100 traces, build graph | 50 ms |
| 100 nodes, compute_verdict | 10 ms |
| 100 nodes, investigation_path | 5 ms |
| 1000 traces, list query | 200 ms |
| 10 MB storage, full load | 2 s |

---

*Last updated: 2026-01-26*
*Measured on: Sentinel v1.0.0*
