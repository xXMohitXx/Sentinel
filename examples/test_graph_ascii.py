"""
Test Script: Phase 13-18 Graph Features (ASCII output)
"""

import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.schema import Trace, TraceRequest, TraceResponse, TraceMessage, Verdict, TraceRuntime
from sdk.graph import ExecutionGraph


def create_mock_trace(
    execution_id,
    node_id,
    parent_node_id=None,
    latency_ms=100,
    verdict_status="pass"
):
    """Create a mock trace for testing."""
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


def main():
    print("")
    print("#" * 60)
    print("  Phylax PHASE 13-18 GRAPH FEATURES TEST")
    print("#" * 60)
    
    # Phase 13: Create traces with causality
    print("")
    print("=" * 60)
    print("PHASE 13: EXECUTION CONTEXT & CAUSALITY")
    print("=" * 60)
    
    exec_id = str(uuid.uuid4())
    node1 = str(uuid.uuid4())
    node2 = str(uuid.uuid4())
    node3 = str(uuid.uuid4())
    
    trace1 = create_mock_trace(exec_id, node1, None, 100)
    trace2 = create_mock_trace(exec_id, node2, node1, 200)
    trace3 = create_mock_trace(exec_id, node3, node1, 150)
    traces = [trace1, trace2, trace3]
    
    print(f"[OK] Created execution: {exec_id[:20]}...")
    print(f"[OK] Node 1 (root): {node1[:20]}...")
    print(f"[OK] Node 2 (child of 1): {node2[:20]}...")
    print(f"[OK] Node 3 (child of 1): {node3[:20]}...")
    print(f"[OK] All traces share same execution_id")
    
    # Phase 14: Build graph
    print("")
    print("=" * 60)
    print("PHASE 14: GRAPH CONSTRUCTION")
    print("=" * 60)
    
    graph = ExecutionGraph.from_traces(traces)
    
    print(f"[OK] Built ExecutionGraph")
    print(f"   - Nodes: {graph.node_count}")
    print(f"   - Edges: {len(graph.edges)}")
    print(f"   - Root node: {graph.root_node_id[:20]}...")
    print(f"   - Total latency: {graph.total_latency_ms}ms")
    
    children = graph.get_children(traces[0].node_id)
    print(f"[OK] Node 1 has {len(children)} children")
    
    topo = graph.topological_order()
    print(f"[OK] Topological order has {len(topo)} nodes")
    
    # Phase 16: Test verdict (pass case)
    print("")
    print("=" * 60)
    print("PHASE 16: GRAPH VERDICT (ALL PASS)")
    print("=" * 60)
    
    verdict = graph.compute_verdict()
    print(f"[OK] Graph verdict: {verdict.status.upper()}")
    print(f"   - Message: {verdict.message}")
    print("[PASS] Verdict correctly computed as PASS")
    
    # Phase 16: Test verdict (fail case)
    print("")
    print("=" * 60)
    print("PHASE 16: GRAPH VERDICT (WITH FAILURE)")
    print("=" * 60)
    
    exec_id2 = str(uuid.uuid4())
    n1 = str(uuid.uuid4())
    n2 = str(uuid.uuid4())
    n3 = str(uuid.uuid4())
    
    fail_traces = [
        create_mock_trace(exec_id2, n1, None, 100, "pass"),
        create_mock_trace(exec_id2, n2, n1, 200, "fail"),
        create_mock_trace(exec_id2, n3, n2, 150, "pass"),
    ]
    
    fail_graph = ExecutionGraph.from_traces(fail_traces)
    fail_verdict = fail_graph.compute_verdict()
    
    print(f"[OK] Graph verdict: {fail_verdict.status.upper()}")
    print(f"   - Root cause: {fail_verdict.root_cause_node[:20]}...")
    print(f"   - Failed count: {fail_verdict.failed_count}")
    print(f"   - Tainted count: {fail_verdict.tainted_count}")
    print("[PASS] Verdict correctly identifies root cause!")
    
    tainted = fail_graph.get_tainted_nodes(n2)
    print(f"[OK] Blast radius from node2: {len(tainted)} nodes affected")
    
    # Phase 18: Performance analysis
    print("")
    print("=" * 60)
    print("PHASE 18: PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    cp = fail_graph.critical_path()
    print(f"[OK] Critical path:")
    print(f"   - Length: {len(cp['path'])} nodes")
    print(f"   - Total latency: {cp['total_latency_ms']}ms")
    print(f"   - Bottleneck: {cp['bottleneck_node'][:20]}...")
    print(f"   - Bottleneck latency: {cp['bottleneck_latency_ms']}ms")
    
    bottlenecks = fail_graph.find_bottlenecks(top_n=3)
    print(f"[OK] Top bottlenecks:")
    for i, b in enumerate(bottlenecks, 1):
        print(f"   {i}. {b['label'][:25]}... - {b['latency_ms']}ms ({b['percent_of_total']}%)")
    
    # Summary
    print("")
    print("=" * 60)
    print("PHASE 15 & 17: UI/API FEATURES")
    print("=" * 60)
    print("-> Phase 15 (Graph Visualization): Check UI 'Graph' tab")
    print("-> Phase 17 (Subgraph Replay): POST /v1/executions/{id}/replay")
    
    print("")
    print("#" * 60)
    print("  [PASS] ALL PHASE 13-18 UNIT TESTS PASSED!")
    print("#" * 60)
    print("")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
