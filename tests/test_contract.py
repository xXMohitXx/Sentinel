"""
Contract Tests (Phase 26)

These tests enforce the API contract and invariants defined in:
- docs/contract.md
- docs/invariants.md

If these tests fail, v1.0 guarantees are broken.
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.schema import Trace, TraceRequest, TraceResponse, TraceMessage, Verdict, TraceRuntime
from sdk.graph import ExecutionGraph


# =============================================================================
# INVARIANT 1: Traces Are Immutable
# =============================================================================

def test_trace_immutability():
    """INVARIANT: Once a trace is created, it never changes."""
    trace = Trace(
        trace_id=str(uuid.uuid4()),
        execution_id=str(uuid.uuid4()),
        node_id=str(uuid.uuid4()),
        request=TraceRequest(provider="test", model="m1", messages=[]),
        response=TraceResponse(text="hello", latency_ms=100),
        runtime=TraceRuntime(library="test", version="1.0"),
        verdict=Verdict(status="pass", violations=[])
    )
    
    original_id = trace.trace_id
    
    # Attempting to modify should raise error
    try:
        trace.trace_id = "new-id"
        return False, "Should have raised error on modification"
    except Exception:
        pass
    
    assert trace.trace_id == original_id
    return True, "Traces are immutable"


# =============================================================================
# INVARIANT 2: Verdicts Never Change After Creation
# =============================================================================

def test_verdict_immutability():
    """INVARIANT: A verdict is computed once and frozen forever."""
    verdict = Verdict(status="fail", severity="high", violations=["test reason"])
    
    try:
        verdict.status = "pass"
        return False, "Should have raised error on modification"
    except Exception:
        pass
    
    assert verdict.status == "fail"
    return True, "Verdicts are immutable"


# =============================================================================
# INVARIANT 3: Graphs Are Read-Only Representations
# =============================================================================

def test_graph_determinism():
    """INVARIANT: Same traces → same graph (deterministic)."""
    exec_id = str(uuid.uuid4())
    n1 = str(uuid.uuid4())
    
    traces = [
        Trace(
            trace_id=str(uuid.uuid4()),
            execution_id=exec_id,
            node_id=n1,
            request=TraceRequest(provider="test", model="m1", 
                                messages=[TraceMessage(role="user", content="hello")]),
            response=TraceResponse(text="world", latency_ms=100),
            runtime=TraceRuntime(library="test", version="1.0"),
            verdict=Verdict(status="pass", violations=[])
        )
    ]
    
    # Build graph twice
    graph1 = ExecutionGraph.from_traces(traces)
    graph2 = ExecutionGraph.from_traces(traces)
    
    # Same hash
    assert graph1.compute_hash() == graph2.compute_hash()
    return True, "Graphs are deterministic"


# =============================================================================
# INVARIANT 5: Phylax Never Makes AI-Based Judgments
# =============================================================================

def test_deterministic_expectations():
    """INVARIANT: All verdicts are deterministic rules."""
    from sdk.expectations import evaluate
    
    # Same inputs MUST produce same outputs
    v1 = evaluate(
        response_text="hello world",
        latency_ms=100,
        must_include=["hello"],
        max_latency_ms=200
    )
    
    v2 = evaluate(
        response_text="hello world",
        latency_ms=100,
        must_include=["hello"],
        max_latency_ms=200
    )
    
    assert v1.status == v2.status
    assert v1.violations == v2.violations
    return True, "Expectations are deterministic"


# =============================================================================
# INVARIANT 9: Graph Verdict Follows Node Verdicts
# =============================================================================

def test_graph_verdict_derivation():
    """INVARIANT: Graph verdict is derived from node verdicts."""
    exec_id = str(uuid.uuid4())
    n1, n2 = str(uuid.uuid4()), str(uuid.uuid4())
    
    # One passing, one failing
    traces = [
        Trace(
            trace_id=str(uuid.uuid4()),
            execution_id=exec_id,
            node_id=n1,
            request=TraceRequest(provider="test", model="m1", messages=[]),
            response=TraceResponse(text="pass", latency_ms=100),
            runtime=TraceRuntime(library="test", version="1.0"),
            verdict=Verdict(status="pass", violations=[])
        ),
        Trace(
            trace_id=str(uuid.uuid4()),
            execution_id=exec_id,
            node_id=n2,
            parent_node_id=n1,
            request=TraceRequest(provider="test", model="m1", messages=[]),
            response=TraceResponse(text="fail", latency_ms=100),
            runtime=TraceRuntime(library="test", version="1.0"),
            verdict=Verdict(status="fail", violations=["test failure"])
        )
    ]
    
    graph = ExecutionGraph.from_traces(traces)
    verdict = graph.compute_verdict()
    
    # Graph fails if any node fails
    assert verdict.status == "fail"
    assert verdict.root_cause_node == n2
    assert verdict.failed_count == 1
    return True, "Graph verdict follows node verdicts"


# =============================================================================
# INVARIANT 10: Integrity Hashes Are Deterministic
# =============================================================================

def test_integrity_hash_determinism():
    """INVARIANT: compute_hash() is a pure function."""
    exec_id = str(uuid.uuid4())
    
    traces = [
        Trace(
            trace_id=str(uuid.uuid4()),
            execution_id=exec_id,
            node_id=str(uuid.uuid4()),
            request=TraceRequest(provider="test", model="m1", messages=[]),
            response=TraceResponse(text="test", latency_ms=100),
            runtime=TraceRuntime(library="test", version="1.0"),
            verdict=Verdict(status="pass", violations=[])
        )
    ]
    
    graph = ExecutionGraph.from_traces(traces)
    
    # Same graph, multiple calls
    hash1 = graph.compute_hash()
    hash2 = graph.compute_hash()
    hash3 = graph.compute_hash()
    
    assert hash1 == hash2 == hash3
    assert len(hash1) == 64  # SHA256
    return True, "Integrity hashes are deterministic"


# =============================================================================
# CONTRACT: Verdict Semantics
# =============================================================================

def test_verdict_only_pass_or_fail():
    """CONTRACT: verdict.status is always 'pass' or 'fail'."""
    pass_verdict = Verdict(status="pass", violations=[])
    fail_verdict = Verdict(status="fail", violations=["reason"])
    
    assert pass_verdict.status == "pass"
    assert fail_verdict.status == "fail"
    assert pass_verdict.status in ("pass", "fail")
    assert fail_verdict.status in ("pass", "fail")
    return True, "Verdict status is pass or fail only"


# =============================================================================
# Main
# =============================================================================

def main():
    print('')
    print('#' * 60)
    print('  CONTRACT & INVARIANT TESTS (v1.0)')
    print('#' * 60)
    print('')
    
    tests = [
        test_trace_immutability,
        test_verdict_immutability,
        test_graph_determinism,
        test_deterministic_expectations,
        test_graph_verdict_derivation,
        test_integrity_hash_determinism,
        test_verdict_only_pass_or_fail,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result, msg = test()
            if result:
                print(f'  [PASS] {test.__name__}: {msg}')
                passed += 1
            else:
                print(f'  [FAIL] {test.__name__}: {msg}')
                failed += 1
        except Exception as e:
            print(f'  [FAIL] {test.__name__}: {str(e)}')
            failed += 1
    
    print('')
    print('#' * 60)
    print(f'  Results: {passed} passed, {failed} failed')
    if failed == 0:
        print('  [PASS] ALL CONTRACT TESTS PASSED!')
    else:
        print('  [FAIL] Some contract tests failed')
    print('#' * 60)
    print('')
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

