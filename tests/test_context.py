"""
Test Phase 13: Execution Context and Causality

Tests for:
- execution_id grouping
- node_id and parent_node_id tracking
- Phylax.execution() context manager
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.context import (
    execution,
    get_execution_id,
    get_parent_node_id,
    push_node,
    pop_node,
    in_execution_context,
)


class TestExecutionContext:
    """Test execution context manager."""
    
    def test_execution_creates_context(self):
        """execution() should create a context with execution_id."""
        assert not in_execution_context()
        
        with execution() as exec_id:
            assert in_execution_context()
            assert exec_id is not None
            assert len(exec_id) == 36  # UUID format
            
        assert not in_execution_context()
    
    def test_get_execution_id_in_context(self):
        """get_execution_id() should return same ID within context."""
        with execution() as exec_id:
            assert get_execution_id() == exec_id
            assert get_execution_id() == exec_id  # Same ID
    
    def test_get_execution_id_outside_context(self):
        """get_execution_id() should generate new ID outside context."""
        id1 = get_execution_id()
        id2 = get_execution_id()
        # Each call generates a new ID when not in context
        assert id1 != id2
    
    def test_parent_node_tracking(self):
        """push_node/pop_node should track parent correctly."""
        with execution():
            # Initially no parent
            assert get_parent_node_id() is None
            
            # Push first node
            push_node("node_1")
            assert get_parent_node_id() == "node_1"
            
            # Push second node (nested)
            push_node("node_2")
            assert get_parent_node_id() == "node_2"
            
            # Pop back to node_1
            pop_node()
            assert get_parent_node_id() == "node_1"
            
            # Pop back to None
            pop_node()
            assert get_parent_node_id() is None
    
    def test_nested_execution_contexts(self):
        """Nested execution() calls should be independent."""
        with execution() as outer_id:
            assert get_execution_id() == outer_id
            
            # Nested context has different ID
            with execution() as inner_id:
                assert inner_id != outer_id
                assert get_execution_id() == inner_id
            
            # Back to outer
            assert get_execution_id() == outer_id


class TestTraceSchema:
    """Test schema has new fields."""
    
    def test_trace_has_execution_fields(self):
        """Trace should have execution_id, node_id, parent_node_id."""
        from sdk.schema import Trace, TraceRequest, TraceResponse, TraceRuntime
        
        trace = Trace(
            request=TraceRequest(
                provider="test",
                model="test-model",
                messages=[],
            ),
            response=TraceResponse(
                text="test response",
                latency_ms=100,
            ),
            runtime=TraceRuntime(
                library="test",
                version="1.0",
            ),
        )
        
        # Check fields exist and have values
        assert trace.execution_id is not None
        assert trace.node_id is not None
        assert trace.parent_node_id is None  # Optional
        assert len(trace.execution_id) == 36  # UUID
        assert len(trace.node_id) == 36


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
