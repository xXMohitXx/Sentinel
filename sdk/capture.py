"""
Capture Layer - Core Logic

Purpose: Intercept LLM calls without changing developer workflows.

Responsibilities:
- Accept input payloads
- Normalize them into a standard trace schema
- Forward request to actual LLM client
- Receive response
- Emit a trace record
"""

import time
from datetime import datetime
from typing import Any, Callable, Optional
from contextlib import contextmanager

from sdk.schema import (
    Trace,
    TraceRequest,
    TraceResponse,
    TraceRuntime,
    TraceMessage,
    TraceParameters,
)


class CaptureLayer:
    """
    Core capture layer for tracing LLM calls.
    
    This class provides the main interface for capturing and storing traces.
    It can be used directly, as a context manager, or via the decorator.
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        auto_store: bool = True,
    ):
        """
        Initialize the capture layer.
        
        Args:
            storage_path: Path to store traces. Defaults to ~/.sentinel/traces
            auto_store: Whether to automatically store traces after capture
        """
        self.storage_path = storage_path
        self.auto_store = auto_store
        self._pending_traces: list[Trace] = []
    
    def capture(
        self,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        parameters: Optional[dict[str, Any]] = None,
        call_fn: Optional[Callable] = None,
        **kwargs,
    ) -> tuple[Any, Trace]:
        """
        Capture an LLM call and create a trace.
        
        Args:
            provider: The LLM provider (openai, local, custom)
            model: The model name
            messages: List of message dicts with 'role' and 'content'
            parameters: Optional parameters (temperature, max_tokens, etc.)
            call_fn: The function to execute for the actual LLM call
            **kwargs: Additional arguments passed to call_fn
            
        Returns:
            Tuple of (response, trace)
        """
        # Build request
        trace_messages = [TraceMessage(**msg) for msg in messages]
        trace_params = TraceParameters(**(parameters or {}))
        
        request = TraceRequest(
            provider=provider,
            model=model,
            messages=trace_messages,
            parameters=trace_params,
        )
        
        # Execute the call and measure latency
        start_time = time.perf_counter()
        
        if call_fn is not None:
            response_data = call_fn(**kwargs)
        else:
            response_data = {"text": "", "usage": None}
        
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Build response
        response_text = self._extract_response_text(response_data)
        response = TraceResponse(
            text=response_text,
            latency_ms=latency_ms,
            usage=self._extract_usage(response_data),
        )
        
        # Build runtime info
        runtime = TraceRuntime(
            library=self._detect_library(provider),
            version=self._get_library_version(provider),
        )
        
        # Create trace
        trace = Trace(
            request=request,
            response=response,
            runtime=runtime,
        )
        
        # Store if auto_store is enabled
        if self.auto_store:
            self._store_trace(trace)
        else:
            self._pending_traces.append(trace)
        
        return response_data, trace
    
    @contextmanager
    def context(
        self,
        provider: str,
        model: str,
    ):
        """
        Context manager for capturing LLM calls.
        
        Usage:
            with capture_layer.context("openai", "gpt-4") as ctx:
                response = openai.chat.completions.create(...)
                ctx.record(messages, response)
        """
        ctx = CaptureContext(self, provider, model)
        try:
            yield ctx
        finally:
            if ctx.trace is not None and self.auto_store:
                self._store_trace(ctx.trace)
    
    def _extract_response_text(self, response_data: Any) -> str:
        """Extract text from various response formats."""
        if isinstance(response_data, dict):
            return response_data.get("text", str(response_data))
        if isinstance(response_data, str):
            return response_data
        # Handle OpenAI response objects
        if hasattr(response_data, "choices") and response_data.choices:
            choice = response_data.choices[0]
            if hasattr(choice, "message"):
                return choice.message.content or ""
            if hasattr(choice, "text"):
                return choice.text or ""
        return str(response_data)
    
    def _extract_usage(self, response_data: Any) -> Optional[dict[str, int]]:
        """Extract token usage from response."""
        if isinstance(response_data, dict):
            return response_data.get("usage")
        if hasattr(response_data, "usage") and response_data.usage:
            return {
                "prompt_tokens": response_data.usage.prompt_tokens,
                "completion_tokens": response_data.usage.completion_tokens,
                "total_tokens": response_data.usage.total_tokens,
            }
        return None
    
    def _detect_library(self, provider: str) -> str:
        """Detect the library based on provider."""
        mapping = {
            "openai": "openai",
            "local": "llama_cpp",
            "llama": "llama_cpp",
            "transformers": "transformers",
        }
        return mapping.get(provider.lower(), provider)
    
    def _get_library_version(self, provider: str) -> str:
        """Get the version of the library."""
        try:
            if provider.lower() == "openai":
                import openai
                return openai.__version__
            elif provider.lower() in ("local", "llama"):
                try:
                    import llama_cpp
                    return llama_cpp.__version__
                except ImportError:
                    return "unknown"
        except Exception:
            pass
        return "unknown"
    
    def _store_trace(self, trace: Trace) -> None:
        """Store a trace to the configured storage."""
        # Import here to avoid circular dependency
        from server.storage.files import FileStorage
        
        storage = FileStorage(base_path=self.storage_path)
        storage.save_trace(trace)
    
    def flush(self) -> list[Trace]:
        """Flush and return all pending traces."""
        traces = self._pending_traces.copy()
        for trace in traces:
            self._store_trace(trace)
        self._pending_traces.clear()
        return traces


class CaptureContext:
    """Context for manual trace recording."""
    
    def __init__(self, capture_layer: CaptureLayer, provider: str, model: str):
        self.capture_layer = capture_layer
        self.provider = provider
        self.model = model
        self.trace: Optional[Trace] = None
        self._start_time: float = time.perf_counter()
    
    def record(
        self,
        messages: list[dict[str, str]],
        response: Any,
        parameters: Optional[dict[str, Any]] = None,
    ) -> Trace:
        """Record the captured call."""
        latency_ms = int((time.perf_counter() - self._start_time) * 1000)
        
        trace_messages = [TraceMessage(**msg) for msg in messages]
        trace_params = TraceParameters(**(parameters or {}))
        
        request = TraceRequest(
            provider=self.provider,
            model=self.model,
            messages=trace_messages,
            parameters=trace_params,
        )
        
        response_text = self.capture_layer._extract_response_text(response)
        trace_response = TraceResponse(
            text=response_text,
            latency_ms=latency_ms,
            usage=self.capture_layer._extract_usage(response),
        )
        
        runtime = TraceRuntime(
            library=self.capture_layer._detect_library(self.provider),
            version=self.capture_layer._get_library_version(self.provider),
        )
        
        self.trace = Trace(
            request=request,
            response=trace_response,
            runtime=runtime,
        )
        
        return self.trace


# Global capture layer instance
_default_capture_layer: Optional[CaptureLayer] = None


def get_capture_layer() -> CaptureLayer:
    """Get or create the default capture layer."""
    global _default_capture_layer
    if _default_capture_layer is None:
        _default_capture_layer = CaptureLayer()
    return _default_capture_layer
