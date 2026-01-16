"""
Llama Adapter

Provides integration with llama.cpp Python bindings.
Stub implementation for initial release.
"""

from typing import Any, Optional

from sdk.capture import CaptureLayer, get_capture_layer
from sdk.schema import Trace


class LlamaAdapter:
    """
    Adapter for llama.cpp Python bindings.
    
    Usage:
        adapter = LlamaAdapter(model_path="/path/to/model.gguf")
        response = adapter.chat_completion(
            messages=[{"role": "user", "content": "Hello!"}]
        )
    
    Note: This is a stub implementation. Full support coming in Phase 2.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        capture_layer: Optional[CaptureLayer] = None,
        **llama_kwargs,
    ):
        """
        Initialize the Llama adapter.
        
        Args:
            model_path: Path to the GGUF model file
            capture_layer: Optional custom capture layer
            **llama_kwargs: Additional arguments for llama.cpp
        """
        self.model_path = model_path
        self.capture_layer = capture_layer or get_capture_layer()
        self.llama_kwargs = llama_kwargs
        self._llm: Optional[Any] = None
    
    @property
    def llm(self):
        """Lazy-load the Llama model."""
        if self._llm is None:
            if self.model_path is None:
                raise ValueError("model_path is required for LlamaAdapter")
            
            try:
                from llama_cpp import Llama
                self._llm = Llama(
                    model_path=self.model_path,
                    **self.llama_kwargs,
                )
            except ImportError:
                raise ImportError(
                    "llama-cpp-python not installed. "
                    "Install with: pip install llama-cpp-python"
                )
        return self._llm
    
    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 256,
        **kwargs,
    ) -> tuple[Any, Trace]:
        """
        Create a chat completion with automatic tracing.
        
        Args:
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (response, Trace)
        """
        parameters = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        
        def make_call():
            return self.llm.create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        
        # Extract model name from path
        model_name = self.model_path.split("/")[-1] if self.model_path else "unknown"
        
        response, trace = self.capture_layer.capture(
            provider="local",
            model=model_name,
            messages=messages,
            parameters=parameters,
            call_fn=make_call,
        )
        
        return response, trace
    
    def completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 256,
        **kwargs,
    ) -> tuple[Any, Trace]:
        """
        Create a completion with automatic tracing.
        
        Args:
            prompt: The prompt text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (response, Trace)
        """
        messages = [{"role": "user", "content": prompt}]
        
        parameters = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        
        def make_call():
            return self.llm(
                prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        
        model_name = self.model_path.split("/")[-1] if self.model_path else "unknown"
        
        response, trace = self.capture_layer.capture(
            provider="local",
            model=model_name,
            messages=messages,
            parameters=parameters,
            call_fn=make_call,
        )
        
        return response, trace
