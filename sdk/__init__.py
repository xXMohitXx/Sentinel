"""
Sentinel SDK - LLM Tracing & Debugging

This package provides the core capture layer for tracing LLM calls.
"""

from sdk.schema import Trace, TraceRequest, TraceResponse, TraceRuntime
from sdk.decorator import trace
from sdk.capture import CaptureLayer

__version__ = "0.1.0"
__all__ = [
    "Trace",
    "TraceRequest",
    "TraceResponse",
    "TraceRuntime",
    "trace",
    "CaptureLayer",
]
