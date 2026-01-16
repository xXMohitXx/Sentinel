"""
Gemini Adapter

Provides integration with Google's Gemini API.
"""

from typing import Any, Optional

from sdk.capture import CaptureLayer, get_capture_layer
from sdk.schema import Trace


class GeminiAdapter:
    """
    Adapter for Google Gemini API.
    
    Usage:
        adapter = GeminiAdapter(api_key="your-key")
        response = adapter.chat_completion(
            model="gemini-2.0-flash",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        capture_layer: Optional[CaptureLayer] = None,
    ):
        """
        Initialize the Gemini adapter.
        
        Args:
            api_key: Optional API key (uses GOOGLE_API_KEY env var if not provided)
            capture_layer: Optional custom capture layer
        """
        self.api_key = api_key
        self.capture_layer = capture_layer or get_capture_layer()
        self._client = None
    
    def _get_client(self, model: str):
        """Get or create the Gemini client."""
        try:
            import google.generativeai as genai
            
            if self.api_key:
                genai.configure(api_key=self.api_key)
            
            return genai.GenerativeModel(model)
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
    
    def chat_completion(
        self,
        model: str = "gemini-2.0-flash",
        messages: list[dict[str, str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
        **kwargs,
    ) -> tuple[Any, Trace]:
        """
        Create a chat completion with automatic tracing.
        
        Args:
            model: The model to use (e.g., "gemini-2.0-flash")
            messages: List of messages with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (Gemini response, Trace)
        """
        messages = messages or []
        parameters = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        
        def make_call():
            client = self._get_client(model)
            
            # Convert messages to Gemini format
            # Gemini uses a different format - combine into a single prompt or use chat
            contents = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                # Map roles to Gemini format
                if role == "system":
                    # Prepend system message to first user message
                    contents.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    contents.append({"role": "model", "parts": [content]})
                else:
                    contents.append({"role": "user", "parts": [content]})
            
            # Create generation config
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            # Make the call
            response = client.generate_content(
                contents,
                generation_config=generation_config,
            )
            
            return response
        
        response, trace = self.capture_layer.capture(
            provider="gemini",
            model=model,
            messages=messages,
            parameters=parameters,
            call_fn=make_call,
        )
        
        return response, trace
    
    def generate(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 256,
        **kwargs,
    ) -> tuple[Any, Trace]:
        """
        Simple text generation with a prompt.
        
        Args:
            prompt: The prompt text
            model: The model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Tuple of (response, Trace)
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
