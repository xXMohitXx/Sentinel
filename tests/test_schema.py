"""
Tests for SDK Schema
"""

import pytest
from datetime import datetime

from sdk.schema import (
    Trace,
    TraceRequest,
    TraceResponse,
    TraceRuntime,
    TraceMessage,
    TraceParameters,
)


class TestTraceSchema:
    """Tests for the Trace schema."""
    
    def test_create_minimal_trace(self):
        """Test creating a trace with minimal required fields."""
        trace = Trace(
            request=TraceRequest(
                provider="openai",
                model="gpt-4",
                messages=[TraceMessage(role="user", content="Hello!")],
            ),
            response=TraceResponse(
                text="Hello! How can I help?",
                latency_ms=150,
            ),
            runtime=TraceRuntime(
                library="openai",
                version="1.0.0",
            ),
        )
        
        assert trace.trace_id is not None
        assert trace.timestamp is not None
        assert trace.request.model == "gpt-4"
        assert trace.response.text == "Hello! How can I help?"
        assert trace.replay_of is None
    
    def test_trace_with_parameters(self):
        """Test creating a trace with custom parameters."""
        trace = Trace(
            request=TraceRequest(
                provider="openai",
                model="gpt-4",
                messages=[TraceMessage(role="user", content="Test")],
                parameters=TraceParameters(
                    temperature=0.5,
                    max_tokens=100,
                    top_p=0.9,
                ),
            ),
            response=TraceResponse(
                text="Response",
                latency_ms=200,
            ),
            runtime=TraceRuntime(
                library="openai",
                version="1.0.0",
            ),
        )
        
        assert trace.request.parameters.temperature == 0.5
        assert trace.request.parameters.max_tokens == 100
        assert trace.request.parameters.top_p == 0.9
    
    def test_trace_json_serialization(self):
        """Test that traces can be serialized to JSON."""
        trace = Trace(
            request=TraceRequest(
                provider="openai",
                model="gpt-4",
                messages=[TraceMessage(role="user", content="Test")],
            ),
            response=TraceResponse(
                text="Response",
                latency_ms=100,
            ),
            runtime=TraceRuntime(
                library="openai",
                version="1.0.0",
            ),
        )
        
        json_data = trace.model_dump()
        
        assert json_data["request"]["model"] == "gpt-4"
        assert json_data["response"]["text"] == "Response"
        assert "trace_id" in json_data
    
    def test_trace_from_json(self):
        """Test that traces can be created from JSON."""
        json_data = {
            "trace_id": "test-id-123",
            "timestamp": "2026-01-17T00:00:00",
            "request": {
                "provider": "openai",
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
                "parameters": {"temperature": 0.7, "max_tokens": 256},
            },
            "response": {
                "text": "Hi there!",
                "latency_ms": 150,
            },
            "runtime": {
                "library": "openai",
                "version": "1.0.0",
            },
        }
        
        trace = Trace(**json_data)
        
        assert trace.trace_id == "test-id-123"
        assert trace.request.model == "gpt-4"
        assert trace.request.messages[0].content == "Hello"
    
    def test_trace_with_replay_lineage(self):
        """Test creating a trace that is a replay of another."""
        original_id = "original-trace-id"
        
        trace = Trace(
            request=TraceRequest(
                provider="openai",
                model="gpt-4",
                messages=[TraceMessage(role="user", content="Test")],
            ),
            response=TraceResponse(
                text="Response",
                latency_ms=100,
            ),
            runtime=TraceRuntime(
                library="openai",
                version="1.0.0",
            ),
            replay_of=original_id,
        )
        
        assert trace.replay_of == original_id
    
    def test_trace_with_metadata(self):
        """Test creating a trace with custom metadata."""
        trace = Trace(
            request=TraceRequest(
                provider="openai",
                model="gpt-4",
                messages=[TraceMessage(role="user", content="Test")],
            ),
            response=TraceResponse(
                text="Response",
                latency_ms=100,
            ),
            runtime=TraceRuntime(
                library="openai",
                version="1.0.0",
            ),
            metadata={
                "user_id": "user-123",
                "session_id": "session-456",
                "experiment": "A/B test v1",
            },
        )
        
        assert trace.metadata["user_id"] == "user-123"
        assert trace.metadata["experiment"] == "A/B test v1"


class TestTraceMessage:
    """Tests for TraceMessage schema."""
    
    def test_create_user_message(self):
        """Test creating a user message."""
        msg = TraceMessage(role="user", content="Hello!")
        assert msg.role == "user"
        assert msg.content == "Hello!"
    
    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = TraceMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
    
    def test_message_with_name(self):
        """Test message with optional name field."""
        msg = TraceMessage(role="user", content="Hello", name="John")
        assert msg.name == "John"


class TestTraceParameters:
    """Tests for TraceParameters schema."""
    
    def test_default_parameters(self):
        """Test default parameter values."""
        params = TraceParameters()
        assert params.temperature == 0.7
        assert params.max_tokens == 256
    
    def test_custom_parameters(self):
        """Test custom parameter values."""
        params = TraceParameters(
            temperature=0.0,
            max_tokens=1000,
            top_p=0.5,
        )
        assert params.temperature == 0.0
        assert params.max_tokens == 1000
        assert params.top_p == 0.5
