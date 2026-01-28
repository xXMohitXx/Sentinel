# Phylax API Contract (v1.0)

> **This document defines what Phylax promises forever.**  
> If it's not in this contract, it's not promised.

---

## Purpose

This contract guarantees API stability for Phylax v1.x releases. Breaking changes to items in this contract require a major version bump (v2.0).

---

## Guaranteed Stable APIs (v1+)

The following are **frozen** and will not change in any v1.x release:

### Decorators

```python
@trace(provider: str, model: str = None, **metadata)
```
- Records LLM call as a trace
- Creates `Trace` object with request/response
- Sends to storage backend
- **Guarantee**: Signature will not change

```python
@expect(
    must_include: list[str] = None,
    must_not_include: list[str] = None,
    max_latency_ms: int = None,
    min_tokens: int = None
)
```
- Evaluates response against expectations
- Produces `Verdict` with status="pass" or "fail"
- **Guarantee**: All 4 rules remain deterministic and unchanged

### Execution Context

```python
from sdk.context import execution

with execution(name: str):
    # All traces inside are linked by execution_id
    pass
```
- Links traces into a single execution graph
- Sets `execution_id` and `node_id` on traces
- Tracks parent-child relationships
- **Guarantee**: Context manager interface will not change

### CLI Commands

| Command | Behavior (Guaranteed) |
|---------|----------------------|
| `Phylax init` | Creates `~/.Phylax/` directory and config |
| `Phylax server` | Starts API server on port 8000 |
| `Phylax list` | Lists traces (newest first) |
| `Phylax list --failed` | Lists only failed traces |
| `Phylax show <id>` | Displays trace details |
| `Phylax replay <id>` | Re-executes trace with same prompt |
| `Phylax bless <id>` | Marks trace as golden baseline |
| `Phylax check` | CI check: exits 0 (pass) or 1 (fail) |

### Trace Schema (Core Fields)

```python
class Trace:
    trace_id: str           # UUID, immutable
    execution_id: str       # Links to execution
    node_id: str            # Graph node ID
    timestamp: str          # ISO-8601 format
    
    request: TraceRequest   # Input data
    response: TraceResponse # Output data
    verdict: Verdict | None # PASS/FAIL status
    
    blessed: bool           # Is golden?
```

**Guarantee**: These fields will never be removed or renamed.

### Verdict Semantics

```python
class Verdict:
    status: "pass" | "fail"  # Only two values, ever
    severity: "low" | "medium" | "high" | None
    violations: list[str]    # Human-readable reasons
```

**Guarantee**: 
- `status` is always "pass" or "fail" (no third state)
- Verdict is computed at trace creation and never changes
- Same inputs → same verdict (deterministic)

### Graph Verdict Semantics

```python
graph.compute_verdict() → GraphVerdict

class GraphVerdict:
    status: "pass" | "fail"
    root_cause_node: str | None  # First failing node
    failed_count: int
    tainted_count: int
```

**Guarantee**:
- If any node fails, graph fails
- Root cause is topologically first failing node
- Tainted nodes are downstream of failed nodes

---

## Explicitly NOT Guaranteed

The following may change in any v1.x release without notice:

### UI Layout
- Component positions
- Color schemes
- Animation styles
- Button placements

### Internal Graph Storage
- File format for graphs
- Index structure
- Cache mechanisms

### Adapter Internals
- How adapters call LLM APIs
- Retry logic
- Error handling details

### Server Endpoints (unless public)
Only these endpoints are public API:
- `GET /v1/traces`
- `GET /v1/traces/{id}`
- `POST /v1/traces`
- `GET /v1/executions`
- `GET /v1/executions/{id}/graph`
- `POST /v1/golden/bless/{id}`
- `GET /v1/golden/check`

All other endpoints are internal and may change.

### Performance Characteristics
- Response times
- Memory usage
- Storage efficiency

---

## Stability Rules

### What Requires a Major Version (v2.0)
- Removing a guaranteed API
- Changing guaranteed behavior
- Breaking backward compatibility

### What Requires a Minor Version (v1.x)
- Adding new features
- New optional parameters
- New endpoints

### What Requires a Patch Version (v1.x.y)
- Bug fixes
- Performance improvements
- Documentation updates

---

## Deprecation Policy

Before removing any guaranteed API:
1. Mark as deprecated in v1.x
2. Log warning when used
3. Remove in v2.0 (minimum 6 months notice)

---

## Enforcement

This contract is enforced by:
1. Contract tests in `tests/test_contract.py`
2. CI checks that fail on contract violations
3. Code review requirements

---

*Last updated: 2026-01-26*  
*Applies to: Phylax v1.0.0+*
