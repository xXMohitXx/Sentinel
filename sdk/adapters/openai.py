"""
OpenAI Adapter

Provides integration with the OpenAI Python client.
Normalizes request/response shapes to the standard trace schema.
"""

from typing import Any, Optional

from sdk.capture import CaptureLayer, get_capture_layer
from sdk.schema import Trace


class OpenAIAdapter:
    """
    Adapter for OpenAI Python client.
    
    Usage:
        adapter = OpenAIAdapter()
        response = adapter.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        capture_layer: Optional[CaptureLayer] = None,
    ):
        """
        Initialize the OpenAI adapter.
        
        Args:
            api_key: Optional API key (uses OPENAI_API_KEY env var if not provided)
            capture_layer: Optional custom capture layer
        """
        self.api_key = api_key
        self.capture_layer = capture_layer or get_capture_layer()
        self._client: Optional[Any] = None
    
    @property
    def client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install openai"
                )
        return self._client
    
    def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 256,
        **kwargs,
    ) -> tuple[Any, Trace]:
        """
        Create a chat completion with automatic tracing.
        
        Args:
            model: The model to use
            messages: List of messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to OpenAI
            
        Returns:
            Tuple of (OpenAI response, Trace)
        """
        parameters = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        
        def make_call():
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        
        response, trace = self.capture_layer.capture(
            provider="openai",
            model=model,
            messages=messages,
            parameters=parameters,
            call_fn=make_call,
        )
        
        return response, trace
    
    def completion(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 256,
        **kwargs,
    ) -> tuple[Any, Trace]:
        """
        Create a completion with automatic tracing.
        
        Args:
            model: The model to use
            prompt: The prompt text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (OpenAI response, Trace)
        """
        # Convert prompt to messages format for consistency
        messages = [{"role": "user", "content": prompt}]
        
        parameters = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        
        def make_call():
            return self.client.completions.create(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        
        response, trace = self.capture_layer.capture(
            provider="openai",
            model=model,
            messages=messages,
            parameters=parameters,
            call_fn=make_call,
        )
        
        return response, trace
