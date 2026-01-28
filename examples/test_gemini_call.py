"""
Test Script - Gemini 2.0 Flash API Call with Trace Capture

This script makes a real API call to Google Gemini and captures the trace.
The trace will be stored in ~/.Phylax/traces/ and visible in the UI.

Usage:
    # Set your Google API key first
    $env:GOOGLE_API_KEY = "your-api-key-here"
    
    # Run the script
    python examples/test_gemini_call.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.adapters.gemini import GeminiAdapter


def main():
    # Check for API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not set!")
        print()
        print("Set it with:")
        print('  $env:GOOGLE_API_KEY = "your-key-here"')
        print()
        print("Get a key at: https://aistudio.google.com/apikey")
        print()
        print("Then run this script again.")
        return 1
    
    print("🚀 Making Gemini 2.5 Flash API call...")
    print()
    
    # Create adapter (this automatically captures traces)
    adapter = GeminiAdapter(api_key=api_key)
    
    # Define the messages
    messages = [
        {"role": "user", "content": "What is the capital of France? Answer in one word."},
    ]
    
    try:
        # Make the call - this is automatically traced!
        response, trace = adapter.chat_completion(
            model="gemini-2.5-flash",  # Gemini 2.5 Flash
            messages=messages,
        )
        
        print("✅ API call successful!")
        print()
        print(f"📝 Trace ID: {trace.trace_id}")
        print(f"⏱️  Latency: {trace.response.latency_ms}ms")
        print(f"🤖 Model: {trace.request.model}")
        print()
        print("Response:")
        print(f"  {response.text}")
        print()
        print("🔍 View this trace in the UI:")
        print("   http://127.0.0.1:8000/ui")
        print()
        print("Or via API:")
        print(f"   http://127.0.0.1:8000/v1/traces/{trace.trace_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
