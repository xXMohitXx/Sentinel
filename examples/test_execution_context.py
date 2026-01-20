"""
Example: Phase 13 Execution Context

Demonstrates:
- Traces grouped by execution_id
- Parent-child relationships via node_id/parent_node_id
- sentinel.execution() context manager
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sdk
from sdk.decorator import trace
from sdk.adapters.gemini import GeminiAdapter


@trace(provider="gemini")
def step_1_fetch_data():
    """First step: Get some data."""
    adapter = GeminiAdapter()
    response, _ = adapter.generate(
        prompt="What is 2 + 2? Answer with just the number.",
        model="gemini-2.5-flash",
    )
    return response


@trace(provider="gemini")
def step_2_process(data):
    """Second step: Process the data."""
    adapter = GeminiAdapter()
    response, _ = adapter.generate(
        prompt=f"The answer was: {data}. Is this correct? Yes or No.",
        model="gemini-2.5-flash",
    )
    return response


@trace(provider="gemini")
def step_3_summarize(result):
    """Third step: Summarize."""
    adapter = GeminiAdapter()
    response, _ = adapter.generate(
        prompt=f"Summarize: {result}",
        model="gemini-2.5-flash",
    )
    return response


def main():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set!")
        print('Set it with: $env:GOOGLE_API_KEY = "your-key"')
        return 1
    
    print("=" * 60)
    print("Phase 13: Execution Context Demo")
    print("=" * 60)
    print()
    
    # Without context - each trace gets independent execution_id
    print("1. WITHOUT execution context:")
    print("-" * 40)
    print("   (Each trace has separate execution_id)")
    
    # With context - all traces share same execution_id
    print()
    print("2. WITH execution context:")
    print("-" * 40)
    
    with sdk.execution() as exec_id:
        print(f"   Execution ID: {exec_id[:20]}...")
        
        data = step_1_fetch_data()
        print(f"   Step 1: {data.text[:30]}...")
        
        result = step_2_process(data.text)
        print(f"   Step 2: {result.text[:30]}...")
        
        summary = step_3_summarize(result.text)
        print(f"   Step 3: {summary.text[:30]}...")
    
    print()
    print("=" * 60)
    print("Check traces in UI: http://127.0.0.1:8000/ui")
    print("Traces from this run share the same execution_id!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
