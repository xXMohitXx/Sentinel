"""
Test script for Expectation Engine

Demonstrates how to use @trace and @expect decorators together.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.decorator import trace, expect
from sdk.adapters.gemini import GeminiAdapter


# Example 1: Passing expectation
@trace(provider="gemini")
@expect(must_include=["paris"], max_latency_ms=5000)
def ask_capital():
    """Ask about capital - should PASS (response contains 'paris')."""
    adapter = GeminiAdapter()
    response, _ = adapter.generate(
        prompt="What is the capital of France? Answer in one word.",
        model="gemini-2.5-flash",
    )
    return response


# Example 2: Failing expectation 
@trace(provider="gemini")
@expect(must_include=["tokyo"], must_not_include=["paris"])
def ask_wrong_capital():
    """Ask about France but expect Tokyo - should FAIL."""
    adapter = GeminiAdapter()
    response, _ = adapter.generate(
        prompt="What is the capital of France? Answer in one word.",
        model="gemini-2.5-flash",
    )
    return response


# Example 3: Latency expectation
@trace(provider="gemini")
@expect(max_latency_ms=100)  # Very tight latency, likely to fail
def ask_fast():
    """Ask with very tight latency requirement - likely to FAIL."""
    adapter = GeminiAdapter()
    response, _ = adapter.generate(
        prompt="Say hello.",
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
    print("Phylax Expectation Engine Test")
    print("=" * 60)
    print()
    
    # Test 1: Should PASS
    print("Test 1: ask_capital() - Expect PASS")
    print("-" * 40)
    try:
        result = ask_capital()
        print(f"Response: {result.text}")
        print("✅ Check trace in UI for verdict")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 2: Should FAIL
    print("Test 2: ask_wrong_capital() - Expect FAIL")
    print("-" * 40)
    try:
        result = ask_wrong_capital()
        print(f"Response: {result.text}")
        print("❌ Check trace in UI for violations")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 3: Latency likely to FAIL
    print("Test 3: ask_fast() - Expect FAIL (latency)")
    print("-" * 40)
    try:
        result = ask_fast()
        print(f"Response: {result.text}")
        print("⏱️ Check trace in UI for latency violation")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    print("=" * 60)
    print("View results in UI: http://127.0.0.1:8000/ui")
    print("Or CLI: python -m cli.main list --failed")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
