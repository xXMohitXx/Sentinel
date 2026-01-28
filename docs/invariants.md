# Phylax Invariants (v1.0)

> **This is Phylax's constitution.**  
> These invariants are non-negotiable and enforced by tests.

---

## Purpose

Invariants are properties that Phylax guarantees to **always** hold true. Unlike the API contract (which covers syntax), invariants cover **semantics** — the meaning of Phylax's behavior.

---

## Core Invariants

### 1. Traces Are Immutable

```
INVARIANT: Once a trace is created, it never changes.
```

- Trace fields cannot be modified after creation
- `trace_id` is permanent
- Stored JSON files are append-only (logically)
- Replay creates NEW traces, does not modify originals

**Why**: Traces are audit artifacts. Mutation would destroy trust.

**Test**: `test_trace_immutability()`

---

### 2. Verdicts Never Change After Creation

```
INVARIANT: A verdict is computed once and frozen forever.
```

- `verdict.status` is set at trace creation
- Same trace always has same verdict
- Verdicts are not recalculated on read
- Changing expectations does not affect existing traces

**Why**: CI decisions must be reproducible. Verdicts are facts, not opinions.

**Test**: `test_verdict_immutability()`

---

### 3. Graphs Are Read-Only Representations

```
INVARIANT: Graphs are derived views, not mutable state.
```

- `ExecutionGraph.from_traces()` is a pure function
- Same traces → same graph (deterministic)
- Graphs have no side effects
- Graph verdict is derived from node verdicts

**Why**: Graphs are for understanding, not for mutation.

**Test**: `test_graph_determinism()`

---

### 4. Phylax Never Executes User Logic

```
INVARIANT: Phylax observes but does not control.
```

- Phylax captures traces AFTER user code runs
- Phylax never modifies user function behavior
- `@trace` is transparent — function output is unchanged
- Replay re-invokes adapters, not user functions

**Why**: Phylax is an observer. If it changed behavior, tracing would be meaningless.

**Test**: `test_trace_transparency()`

---

### 5. Phylax Never Makes AI-Based Judgments

```
INVARIANT: All verdicts are deterministic rules.
```

- Only 4 expectation rules exist (v1.0):
  - `must_include` — substring present
  - `must_not_include` — substring absent
  - `max_latency_ms` — performance threshold
  - `min_tokens` — minimum length
- No LLM is used to evaluate LLM output
- No fuzzy matching, similarity scores, or embeddings
- Same input → same verdict, always

**Why**: AI-based judgment would make CI flaky and unpredictable.

**Test**: `test_deterministic_expectations()`

---

### 6. Execution Context Creates Causality

```
INVARIANT: Traces in an execution form a DAG.
```

- `with execution()` links all traces inside
- `parent_node_id` creates directed edges
- Execution graphs are acyclic
- Topological ordering is always valid

**Why**: Causality enables root cause analysis.

**Test**: `test_graph_acyclicity()`

---

### 7. Golden Traces Are Hash-Verified

```
INVARIANT: Blessed traces are compared by content hash.
```

- `Phylax bless` stores output hash
- `Phylax check` compares current hash to blessed hash
- Hash mismatch = regression
- Hash collision (false positive) is astronomically rare

**Why**: Hash comparison is exact and fast.

**Test**: `test_golden_hash_comparison()`

---

### 8. CI Exit Codes Are Dependable

```
INVARIANT: `Phylax check` returns predictable exit codes.
```

| Condition | Exit Code |
|-----------|-----------|
| All golden traces pass | 0 |
| Any golden trace fails | 1 |
| No golden traces exist | 0 (with warning) |
| Error during check | 2 |

**Why**: CI systems depend on exit codes.

**Test**: `test_ci_exit_codes()`

---

### 9. Graph Verdict Follows Node Verdicts

```
INVARIANT: Graph verdict is a pure function of node verdicts.
```

- If ANY node fails → graph fails
- Root cause = topologically first failing node
- Tainted nodes = descendants of failed nodes
- Graph status is never "pending" if all nodes are resolved

**Why**: Graph verdict must be predictable.

**Test**: `test_graph_verdict_derivation()`

---

### 10. Integrity Hashes Are Deterministic

```
INVARIANT: compute_hash() is a pure function.
```

- Same graph → same hash
- Hash covers all semantic content
- Hash is SHA256 (64 hex characters)
- `verify_integrity()` returns consistent results

**Why**: Enterprise trust requires verifiable integrity.

**Test**: `test_integrity_hash_determinism()`

---

## Enforcement

These invariants are enforced by:

1. **Contract Tests** — `tests/test_invariants.py`
2. **CI Pipeline** — Invariant tests run on every commit
3. **Code Review** — Changes that violate invariants are rejected

### Test Pattern

Each invariant has a corresponding test:

```python
def test_trace_immutability():
    """INVARIANT: Once a trace is created, it never changes."""
    trace = create_test_trace()
    original = trace.model_dump()
    
    # Attempt modification should fail
    with pytest.raises(ValidationError):
        trace.trace_id = "new-id"
    
    # Content unchanged
    assert trace.model_dump() == original
```

---

## Violation Response

If an invariant is violated:

1. **File a bug** — This is a critical defect
2. **Fix immediately** — Invariants are non-negotiable
3. **Add regression test** — Prevent future violations
4. **Consider patch release** — Users may be affected

---

*Last updated: 2026-01-26*  
*Applies to: Phylax v1.0.0+*
