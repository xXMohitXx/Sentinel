"""
Chat Routes

OpenAI-compatible chat completion endpoint.
This allows drop-in replacement for OpenAI base URL.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import time
import uuid

from sdk.schema import Trace, TraceRequest, TraceResponse, TraceRuntime, TraceMessage, TraceParameters
from sdk.adapters.openai import OpenAIAdapter
from server.storage.files import FileStorage

router = APIRouter()
storage = FileStorage()


class ChatMessage(BaseModel):
    """OpenAI-compatible message format."""
    role: str
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str
    messages: list[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 256
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[list[str]] = None
    stream: Optional[bool] = False
    
    # Phylax-specific options
    trace: Optional[bool] = True  # Whether to record a trace


class ChatCompletionChoice(BaseModel):
    """OpenAI-compatible choice format."""
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    """OpenAI-compatible usage format."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage
    # Phylax addition
    trace_id: Optional[str] = None


@router.post("/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """
    OpenAI-compatible chat completion endpoint.
    
    This enables:
    - Drop-in replacement for OpenAI base URL
    - LangChain compatibility
    - Automatic tracing
    """
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Streaming not yet supported. Set stream=false."
        )
    
    start_time = time.perf_counter()
    
    try:
        adapter = OpenAIAdapter()
        
        # Convert messages to dict format
        messages = [msg.model_dump() for msg in request.messages]
        
        # Build parameters
        params = {
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.top_p is not None:
            params["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            params["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            params["presence_penalty"] = request.presence_penalty
        if request.stop is not None:
            params["stop"] = request.stop
        
        # Make the call
        response, trace = adapter.chat_completion(
            model=request.model,
            messages=messages,
            **params,
        )
        
        # Build OpenAI-compatible response
        completion_response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=response.choices[0].message.content,
                    ),
                    finish_reason=response.choices[0].finish_reason or "stop",
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            ),
            trace_id=trace.trace_id if request.trace else None,
        )
        
        return completion_response
        
    except Exception as e:
        # Log the error as a trace with failed response
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        error_trace = Trace(
            request=TraceRequest(
                provider="openai",
                model=request.model,
                messages=[TraceMessage(**msg.model_dump()) for msg in request.messages],
                parameters=TraceParameters(
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                ),
            ),
            response=TraceResponse(
                text=f"ERROR: {str(e)}",
                latency_ms=latency_ms,
            ),
            runtime=TraceRuntime(
                library="openai",
                version="unknown",
            ),
            metadata={"error": str(e)},
        )
        
        if request.trace:
            storage.save_trace(error_trace)
        
        raise HTTPException(
            status_code=500,
            detail=f"Chat completion failed: {str(e)}"
        )
