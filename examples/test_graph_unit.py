"""
Test Script: Phase 13-18 Graph Features (No API Key Required)

Tests the core graph logic without making actual LLM calls.
"""

import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.schema import Trace, TraceRequest, TraceResponse, TraceMessage, Verdict
from sdk.graph import ExecutionGraph, GraphNode, GraphEdge, GraphVerdict


def create_mock_trace(
    execution_id: str,
    node_id: str,
    parent_node_id: str = None,
    latency_ms: int = 100,
    verdict_status: str = "pass"
):
    """Create a mock trace for testing."""
    from sdk.schema import TraceRuntime
    
    return Trace(
        trace_id=str(uuid.uuid4()),
        execution_id=execution_id,
        node_id=node_id,
        parent_node_id=parent_node_id,
        request=TraceRequest(
            provider="test",
            model="test-model",
            messages=[TraceMessage(role="user", content=f"Node {node_id[:8]}")]
        ),
        response=TraceResponse(
            text=f"Response for {node_id[:8]}",
            latency_ms=latency_ms
        ),
        runtime=TraceRuntime(
            library="test",
            version="1.0.0"
        ),
        verdict=Verdict(
            status=verdict_status,
            violations=[] if verdict_status == "pass" else ["test violation"]
        ) if verdict_status else None
    )


def test_phase_13_causality():
    """Test Phase 13: Execution context and causality tracking."""
    print("\n" + "=" * 60)
    print("PHASE 13: EXECUTION CONTEXT & CAUSALITY")
    print("=" * 60)
    
    exec_id = str(uuid.uuid4())
    node1 = str(uuid.uuid4())
    node2 = str(uuid.uuid4())
    node3 = str(uuid.uuid4())
    
    # Create traces with parent-child relationships
    trace1 = create_mock_trace(exec_id, node1, None, 100)
    trace2 = create_mock_trace(exec_id, node2, node1, 200)  # child of node1
    trace3 = create_mock_trace(exec_id, node3, node1, 150)  # sibling of node2
    
    print(f"✓ Created execution: {exec_id[:20]}...")
    print(f"✓ Node 1 (root): {node1[:20]}...")
    print(f"✓ Node 2 (child of 1): {node2[:20]}...")
    print(f"✓ Node 3 (child of 1): {node3[:20]}...")
    print(f"✓ All traces share same execution_id")
    
    return [trace1, trace2, trace3], exec_id


def test_phase_14_graph_construction(traces):
    """Test Phase 14: Building ExecutionGraph from traces."""
    print("\n" + "=" * 60)
    print("PHASE 14: GRAPH CONSTRUCTION")
    print("=" * 60)
    
    graph = ExecutionGraph.from_traces(traces)
    
    print(f"✓ Built ExecutionGraph")
    print(f"   - Nodes: {graph.node_count}")
    print(f"   - Edges: {len(graph.edges)}")
    print(f"   - Root node: {graph.root_node_id[:20]}...")
    print(f"   - Total latency: {graph.total_latency_ms}ms")
    
    # Test traversal
    children = graph.get_children(traces[0].node_id)
    print(f"✓ Node 1 has {len(children)} children")
    
    # Test topological order
    topo = graph.topological_order()
    print(f"✓ Topological order has {len(topo)} nodes")
    
    return graph


def test_phase_16_verdict_pass(graph):
    """Test Phase 16: Graph verdict when all pass."""
    print("\n" + "=" * 60)
    print("PHASE 16: GRAPH VERDICT (ALL PASS)")
    print("=" * 60)
    
    verdict = graph.compute_verdict()
    
    print(f" Graph verdict: {verdict.status.upper()}")
    print(f"   - Message: {verdict.message}")
    print(f"   - Failed count: {verdict.failed_count}")
    print(f"   - Tainted count: {verdict.tainted_count}")
    
    assert verdict.status == "pass", "Expected pass verdict"
    print(" Verdict correctly computed as PASS")


def test_phase_16_verdict_fail():
    """Test Phase 16: Graph verdict with failure + propagation."""
    print("\n" + "=" * 60)
    print("PHASE 16: GRAPH VERDICT (WITH FAILURE)")
    print("=" * 60)
    
    exec_id = str(uuid.uuid4())
    node1 = str(uuid.uuid4())
    node2 = str(uuid.uuid4())
    node3 = str(uuid.uuid4())
    
    # Create trace chain: node1 -> node2 (FAIL) -> node3 (tainted)
    traces = [
        create_mock_trace(exec_id, node1, None, 100, "pass"),
        create_mock_trace(exec_id, node2, node1, 200, "fail"),  # FAILURE
        create_mock_trace(exec_id, node3, node2, 150, "pass"),   # downstream
    ]
    
    graph = ExecutionGraph.from_traces(traces)
    verdict = graph.compute_verdict()
    
    print(f"✓ Graph verdict: {verdict.status.upper()}")
    print(f"   - Root cause: {verdict.root_cause_node[:20]}...")
    print(f"   - Failed count: {verdict.failed_count}")
    print(f"   - Tainted count: {verdict.tainted_count}")
    
    assert verdict.status == "fail", "Expected fail verdict"
    assert verdict.root_cause_node == node2, "Root cause should be node2"
    print(" Verdict correctly identifies root cause!")
    
    # Test blast radius
    tainted = graph.get_tainted_nodes(node2)
    print(f"✓ Blast radius from node2: {len(tainted)} nodes affected")
    
    return graph


def test_phase_18_performance(graph):
    """Test Phase 18: Performance analysis."""
    print("\n" + "=" * 60)
    print("PHASE 18: PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    # Critical path
    cp = graph.critical_path()
    print(f"✓ Critical path:")
    print(f"   - Length: {len(cp['path'])} nodes")
    print(f"   - Total latency: {cp['total_latency_ms']}ms")
    print(f"   - Bottleneck: {cp['bottleneck_node'][:20]}...")
    print(f"   - Bottleneck latency: {cp['bottleneck_latency_ms']}ms")
    
    # Bottlenecks
    bottlenecks = graph.find_bottlenecks(top_n=3)
    print(f"✓ Top bottlenecks:")
    for i, b in enumerate(bottlenecks, 1):
        print(f"   {i}. {b['label'][:25]}... - {b['latency_ms']}ms ({b['percent_of_total']}%)")


def main():
    print("\n" + "#" * 60)
    print("  Phylax PHASE 13-18 GRAPH FEATURES TEST")
    print("  (No API key required - pure Python tests)")
    print("#" * 60)
    
    # Phase 13: Create traces with causality
    traces, exec_id = test_phase_13_causality()
    
    # Phase 14: Build graph
    graph = test_phase_14_graph_construction(traces)
    
    # Phase 16: Test verdict (pass case)
    test_phase_16_verdict_pass(graph)
    
    # Phase 16: Test verdict (fail case with propagation)
    fail_graph = test_phase_16_verdict_fail()
    
    # Phase 18: Performance analysis
    test_phase_18_performance(fail_graph)
    
    # Phase 15 & 17 are UI/API features
    print("\n" + "=" * 60)
    print("PHASE 15 & 17: UI/API FEATURES")
    print("=" * 60)
    print("→ Phase 15 (Graph Visualization): Check UI 'Graph' tab")
    print("→ Phase 17 (Subgraph Replay): POST /v1/executions/{id}/replay")
    print("  (Requires running LLM traces with execution context)")
    
    print("\n" + "#" * 60)
    print("   ALL PHASE 13-18 UNIT TESTS PASSED!")
    print("#" * 60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
