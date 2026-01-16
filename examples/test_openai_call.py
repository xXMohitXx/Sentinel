"""
Test Script - Real OpenAI API Call with Trace Capture

This script makes a real API call to OpenAI and captures the trace.
The trace will be stored in ~/.sentinel/traces/ and visible in the UI.

Usage:
    # Set your OpenAI API key first
    $env:OPENAI_API_KEY = "your-api-key-here"
    
    # Run the script
    python examples/test_openai_call.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.adapters.openai import OpenAIAdapter


def main():
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set!")
        print()
        print("Set it with:")
        print('  $env:OPENAI_API_KEY = "sk-your-key-here"')
        print()
        print("Then run this script again.")
        return 1
    
    print("🚀 Making OpenAI API call...")
    print()
    
    # Create adapter (this automatically captures traces)
    adapter = OpenAIAdapter(api_key=api_key)
    
    # Define the messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Keep responses brief."},
        {"role": "user", "content": "What is the capital of France? Answer in one word."},
    ]
    
    try:
        # Make the call - this is automatically traced!
        response, trace = adapter.chat_completion(
            model="gpt-4o-mini",  # Using cheaper model for testing
            messages=messages,
            temperature=0.7,
            max_tokens=50,
        )
        
        print("✅ API call successful!")
        print()
        print(f"📝 Trace ID: {trace.trace_id}")
        print(f"⏱️  Latency: {trace.response.latency_ms}ms")
        print(f"🤖 Model: {trace.request.model}")
        print()
        print("Response:")
        print(f"  {response.choices[0].message.content}")
        print()
        print("🔍 View this trace in the UI:")
        print("   http://127.0.0.1:8000/ui")
        print()
        print("Or via API:")
        print(f"   http://127.0.0.1:8000/v1/traces/{trace.trace_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
