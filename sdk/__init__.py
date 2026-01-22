"""
Sentinel SDK - LLM Tracing & Debugging

This package provides the core capture layer for tracing LLM calls.
"""

from sdk.schema import Trace, TraceRequest, TraceResponse, TraceRuntime, Verdict
from sdk.decorator import trace, expect
from sdk.capture import CaptureLayer
from sdk.context import execution  # Phase 13: Execution context
from sdk.graph import ExecutionGraph, NodeRole, GraphStage, GraphDiff, NodeDiff  # Phase 14+

__version__ = "0.5.0"
__all__ = [
    "Trace",
    "TraceRequest",
    "TraceResponse",
    "TraceRuntime",
    "Verdict",
    "trace",
    "expect",
    "CaptureLayer",
    "execution",      # Phase 13
    "ExecutionGraph", # Phase 14
    "NodeRole",       # Phase 19
    "GraphStage",     # Phase 20
    "GraphDiff",      # Phase 23
    "NodeDiff",       # Phase 23
]
