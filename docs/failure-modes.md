# Phylax Failure Modes (v1.0)

> **v1 is trusted when failure behavior is predictable.**  
> This document defines what happens when things go wrong.

---

## Purpose

This document defines Phylax's behavior in error scenarios. Users must know exactly what Phylax will do when things fail — ambiguity destroys trust.

---

## Failure Taxonomy

### 1. Adapter Errors

When the LLM provider fails (network, auth, rate limit):

| Scenario | Behavior |
|----------|----------|
| Network timeout | Trace recorded with `response.error = "timeout"` |
| Auth failure (401) | Trace recorded with `response.error = "unauthorized"` |
| Rate limit (429) | Trace recorded with `response.error = "rate_limited"` |
| Server error (5xx) | Trace recorded with `response.error = "server_error"` |
| Invalid response | Trace recorded with `response.error = "parse_error"` |

**Key guarantee**: A trace is always created, even on error.

**Verdict**: Error traces get `verdict.status = "fail"` automatically.

---

### 2. Expectation Misconfigurations

When expectation rules are invalid:

| Scenario | Behavior |
|----------|----------|
| Invalid type (`must_include=123`) | **Fail fast** at decoration time |
| Empty list (`must_include=[]`) | Treated as no expectation (pass) |
| Negative latency (`max_latency_ms=-1`) | **Fail fast** at decoration time |
| Conflicting rules | All rules evaluated independently |

**Key guarantee**: Invalid expectations fail immediately, not at runtime.

---

### 3. Replay Errors

When replaying a trace fails:

| Scenario | Behavior |
|----------|----------|
| Original trace not found | HTTP 404, no replay created |
| Adapter unavailable | Replay trace with `verdict.status = "fail"` |
| Different output | Expected — replay compares with diff |
| Identical output | Replay trace with `verdict.status = "pass"` |

**Key guarantee**: Replay creates a new trace linked via `replay_of`.

---

### 4. Golden Trace Scenarios

When working with blessed traces:

| Scenario | Behavior |
|----------|----------|
| Missing golden (no blessed trace exists) | `Phylax check` warns, exits 0 |
| Golden exists, output matches | `Phylax check` exits 0 |
| Golden exists, output differs | `Phylax check` exits 1 |
| Multiple goldens (same model) | Uses most recent |

**Key guarantee**: Missing golden is NOT a failure. Only regressions fail.

---

### 5. Graph Construction Errors

When building graphs from traces:

| Scenario | Behavior |
|----------|----------|
| No traces for execution | HTTP 404 |
| Single trace (no edges) | Valid graph with 1 node |
| Orphan node (parent not found) | Node included, no edge |
| Circular reference (shouldn't happen) | Ignored, graph acyclic |

**Key guarantee**: Graphs are always valid DAGs.

---

### 6. Storage Errors

When file/database operations fail:

| Scenario | Behavior |
|----------|----------|
| Disk full | Trace creation fails, error logged |
| Permission denied | Trace creation fails, error logged |
| Corrupted trace file | File skipped, warning logged |
| SQLite lock | Retry 3 times, then fail |

**Key guarantee**: Bad files don't crash the system.

---

### 7. Server Errors

API error handling:

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 201 | Created (new trace) |
| 400 | Bad request (client error) |
| 404 | Resource not found |
| 422 | Validation error (schema mismatch) |
| 500 | Internal server error |

**Key guarantee**: Errors return JSON with `{"detail": "..."}`.

---

### 8. CLI Exit Codes

| Command | Exit 0 | Exit 1 | Exit 2 |
|---------|--------|--------|--------|
| `Phylax init` | Success | Already initialized | Error |
| `Phylax server` | Clean shutdown | - | Crash |
| `Phylax list` | Success | - | Error |
| `Phylax show <id>` | Found | Not found | Error |
| `Phylax replay <id>` | Success | Replay failed | Error |
| `Phylax bless <id>` | Success | Already blessed | Error |
| `Phylax check` | All pass | Any fail | Error |

**Key guarantee**: Exit codes are predictable for scripting.

---

## Determinism Guarantees

### What Is Deterministic

These produce the same result every time:

| Operation | Determinism |
|-----------|-------------|
| `evaluate()` with same inputs | ✅ Always same verdict |
| `Trace.model_dump()` | ✅ Always same JSON |
| `graph.compute_hash()` | ✅ Always same hash |
| `graph.compute_verdict()` | ✅ Always same verdict |
| `graph.investigation_path()` | ✅ Always same steps |

### What Is NOT Deterministic

These may vary between runs:

| Operation | Variability |
|-----------|-------------|
| LLM response content | Different every call |
| LLM latency | Varies by network/load |
| `uuid.uuid4()` | Different every call |
| `datetime.now()` | Different every call |
| File ordering in storage | May vary by filesystem |

### What Phylax Enforces vs Observes

| Aspect | Role |
|--------|------|
| Expectation rules | **Enforces** — fails if violated |
| LLM output | **Observes** — records, doesn't change |
| Latency | **Observes** — records, may alert |
| Trace creation | **Enforces** — always happens |
| Verdict mutation | **Enforces** — forbidden after creation |

---

## Error Messages

All errors follow this pattern:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "context": {}
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| `TRACE_NOT_FOUND` | Trace ID doesn't exist |
| `EXECUTION_NOT_FOUND` | Execution ID doesn't exist |
| `ADAPTER_ERROR` | LLM provider failed |
| `VALIDATION_ERROR` | Schema validation failed |
| `STORAGE_ERROR` | File/DB operation failed |
| `REPLAY_ERROR` | Replay operation failed |

---

## Testing Failure Modes

Each failure mode has a corresponding test:

```python
# tests/test_failure_modes.py

def test_adapter_timeout_creates_trace():
    """Timeout still creates a trace with error."""
    ...

def test_missing_golden_warns():
    """Missing golden doesn't fail check."""
    ...

def test_invalid_expectation_fails_fast():
    """Bad expectation raises at decoration time."""
    ...
```

---

*Last updated: 2026-01-26*  
*Applies to: Phylax v1.0.0+*
