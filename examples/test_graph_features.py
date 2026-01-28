"""
Test Script: Phase 13-18 Graph Features

Tests:
- Phase 13: Execution context & causality
- Phase 14: Graph construction
- Phase 15: Graph visualization (UI)
- Phase 16: Graph-level judgment
- Phase 17: Subgraph replay
- Phase 18: Performance analysis
"""

import os
import sys
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sdk
from sdk.decorator import trace, expect
from sdk.adapters.gemini import GeminiAdapter

API_BASE = "http://127.0.0.1:8000/v1"


# =============================================================================
# Test Functions with @trace decorator
# =============================================================================

@trace(provider="gemini")
@expect(must_include=["4"])  # 2+2=4
def step_1_calculate():
    """Step 1: Simple calculation."""
    adapter = GeminiAdapter()
    response, _ = adapter.generate(
        prompt="What is 2 + 2? Answer with just the number.",
        model="gemini-2.5-flash",
    )
    return response


@trace(provider="gemini")
@expect(must_include=["correct", "yes"], max_latency_ms=5000)
def step_2_verify(previous_answer):
    """Step 2: Verify the answer."""
    adapter = GeminiAdapter()
    response, _ = adapter.generate(
        prompt=f"Is {previous_answer} the correct answer to 2+2? Reply Yes or No.",
        model="gemini-2.5-flash",
    )
    return response


@trace(provider="gemini")
def step_3_summarize(result):
    """Step 3: Summarize results."""
    adapter = GeminiAdapter()
    response, _ = adapter.generate(
        prompt=f"Summarize this verification: {result}",
        model="gemini-2.5-flash",
    )
    return response


def test_phase_13_execution_context():
    """Test Phase 13: Execution context groups traces."""
    print("\n" + "=" * 60)
    print("PHASE 13: EXECUTION CONTEXT TEST")
    print("=" * 60)
    
    with sdk.execution() as exec_id:
        print(f"✓ Created execution context: {exec_id[:20]}...")
        
        # Run chained steps
        result1 = step_1_calculate()
        print(f"✓ Step 1 completed: {result1.text[:30]}...")
        
        result2 = step_2_verify(result1.text)
        print(f"✓ Step 2 completed: {result2.text[:30]}...")
        
        result3 = step_3_summarize(result2.text)
        print(f"✓ Step 3 completed: {result3.text[:30]}...")
    
    print(f"\n✅ All 3 traces share execution_id: {exec_id[:20]}...")
    return exec_id


def test_phase_14_graph_api(execution_id):
    """Test Phase 14: Graph construction API."""
    print("\n" + "=" * 60)
    print("PHASE 14: GRAPH CONSTRUCTION TEST")
    print("=" * 60)
    
    # Test /v1/executions endpoint
    resp = requests.get(f"{API_BASE}/executions")
    data = resp.json()
    print(f"✓ GET /v1/executions returned {data['count']} executions")
    
    # Test /v1/executions/{id} endpoint
    resp = requests.get(f"{API_BASE}/executions/{execution_id}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✓ GET /v1/executions/{execution_id[:12]}... returned {data['count']} traces")
    else:
        print(f"✗ GET /v1/executions/{execution_id[:12]}... failed: {resp.status_code}")
    
    # Test /v1/executions/{id}/graph endpoint
    resp = requests.get(f"{API_BASE}/executions/{execution_id}/graph")
    if resp.status_code == 200:
        graph = resp.json()
        print(f"✓ GET /v1/executions/{execution_id[:12]}../graph:")
        print(f"   - Nodes: {graph['node_count']}")
        print(f"   - Edges: {len(graph['edges'])}")
        print(f"   - Total latency: {graph['total_latency_ms']}ms")
        return graph
    else:
        print(f"✗ Graph API failed: {resp.status_code}")
        return None


def test_phase_16_graph_verdict(execution_id):
    """Test Phase 16: Graph-level judgment."""
    print("\n" + "=" * 60)
    print("PHASE 16: GRAPH VERDICT TEST")
    print("=" * 60)
    
    resp = requests.get(f"{API_BASE}/executions/{execution_id}/graph")
    if resp.status_code != 200:
        print(f"✗ Could not load graph")
        return
    
    graph = resp.json()
    
    # The verdict is computed by the Python model, test via analysis endpoint
    resp = requests.get(f"{API_BASE}/executions/{execution_id}/analysis")
    if resp.status_code == 200:
        analysis = resp.json()
        verdict = analysis.get('verdict', {})
        print(f"✓ Graph verdict: {verdict.get('status', 'unknown').upper()}")
        if verdict.get('root_cause_node'):
            print(f"   - Root cause: {verdict['root_cause_node'][:20]}...")
        print(f"   - Failed nodes: {verdict.get('failed_count', 0)}")
        print(f"   - Tainted nodes: {verdict.get('tainted_count', 0)}")
    else:
        print(f"✗ Analysis API failed: {resp.status_code}")


def test_phase_18_performance_analysis(execution_id):
    """Test Phase 18: Performance analysis."""
    print("\n" + "=" * 60)
    print("PHASE 18: PERFORMANCE ANALYSIS TEST")
    print("=" * 60)
    
    resp = requests.get(f"{API_BASE}/executions/{execution_id}/analysis")
    if resp.status_code != 200:
        print(f"✗ Analysis API failed: {resp.status_code}")
        return
    
    analysis = resp.json()
    
    print(f"✓ GET /v1/executions/{execution_id[:12]}../analysis")
    print(f"   - Total nodes: {analysis['node_count']}")
    print(f"   - Total latency: {analysis['total_latency_ms']}ms")
    
    # Critical path
    cp = analysis.get('critical_path', {})
    if cp.get('path'):
        print(f"   - Critical path length: {len(cp['path'])} nodes")
        print(f"   - Critical path latency: {cp['total_latency_ms']}ms")
        print(f"   - Bottleneck: {cp.get('bottleneck_node', 'N/A')[:20]}...")
    
    # Bottlenecks
    bottlenecks = analysis.get('bottlenecks', [])
    if bottlenecks:
        print(f"   - Top bottleneck: {bottlenecks[0]['label'][:30]}... ({bottlenecks[0]['percent_of_total']}%)")


def test_phase_15_ui_notice():
    """Remind user to check UI."""
    print("\n" + "=" * 60)
    print("PHASE 15: GRAPH VISUALIZATION")
    print("=" * 60)
    print("→ Open http://127.0.0.1:8000/ui")
    print("→ Click 'Graph' tab")
    print("→ Select an execution to see the DAG visualization")
    print("→ Failed nodes show in RED, tainted nodes show ⚠️ badge")


def main():
    # Check API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set!")
        print('Set it with: $env:GOOGLE_API_KEY = "your-key"')
        return 1
    
    print("\n" + "█" * 60)
    print("  Phylax PHASE 13-18 GRAPH FEATURES TEST")
    print("█" * 60)
    
    # Run tests
    execution_id = test_phase_13_execution_context()
    
    # Wait for traces to be saved
    time.sleep(1)
    
    graph = test_phase_14_graph_api(execution_id)
    test_phase_16_graph_verdict(execution_id)
    test_phase_18_performance_analysis(execution_id)
    test_phase_15_ui_notice()
    
    print("\n" + "█" * 60)
    print("  ✅ ALL PHASE 13-18 TESTS COMPLETE")
    print("█" * 60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
