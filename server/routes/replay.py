"""
Replay Routes

Endpoint for replaying historical traces.

Replay means:
- Load historical trace
- Optionally override model or parameters
- Execute again
- Store new trace with lineage
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

from sdk.schema import Trace, TraceParameters
from sdk.adapters.openai import OpenAIAdapter
from sdk.adapters.gemini import GeminiAdapter
from server.storage.files import FileStorage

router = APIRouter()
storage = FileStorage()


class ReplayRequest(BaseModel):
    """Request body for replay endpoint."""
    # Optional overrides
    model: Optional[str] = None
    provider: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    # If true, only simulate (don't execute actual LLM call)
    dry_run: bool = False


class ReplayResponse(BaseModel):
    """Response from replay endpoint."""
    original_trace_id: str
    new_trace_id: str
    dry_run: bool
    overrides_applied: dict[str, Any]
    trace: dict


@router.post("/replay/{trace_id}")
async def replay_trace(
    trace_id: str,
    request: ReplayRequest = ReplayRequest(),
) -> ReplayResponse:
    """
    Replay a historical trace.
    
    This enables:
    - Regression testing
    - Model comparison
    - Prompt evolution tracking
    """
    # Load the original trace
    original = storage.get_trace(trace_id)
    
    if original is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    # Determine final values (original or overridden)
    final_model = request.model or original.request.model
    final_provider = request.provider or original.request.provider
    
    # Merge parameters
    original_params = original.request.parameters.model_dump()
    if request.parameters:
        original_params.update(request.parameters)
    final_params = TraceParameters(**original_params)
    
    # Track what was overridden
    overrides = {}
    if request.model:
        overrides["model"] = request.model
    if request.provider:
        overrides["provider"] = request.provider
    if request.parameters:
        overrides["parameters"] = request.parameters
    
    # Convert messages to dict format
    messages = [msg.model_dump() for msg in original.request.messages]
    
    if request.dry_run:
        # Dry run - just return what would be executed
        new_trace = Trace(
            request=original.request.model_copy(
                update={
                    "model": final_model,
                    "provider": final_provider,
                    "parameters": final_params,
                }
            ),
            response=original.response,
            runtime=original.runtime,
            replay_of=trace_id,
        )
        
        return ReplayResponse(
            original_trace_id=trace_id,
            new_trace_id=new_trace.trace_id,
            dry_run=True,
            overrides_applied=overrides,
            trace=new_trace.model_dump(),
        )
    
    # Execute the replay based on provider
    try:
        if final_provider.lower() == "openai":
            adapter = OpenAIAdapter()
            response, new_trace = adapter.chat_completion(
                model=final_model,
                messages=messages,
                **final_params.model_dump(exclude_none=True),
            )
        elif final_provider.lower() == "gemini":
            adapter = GeminiAdapter()
            response, new_trace = adapter.chat_completion(
                model=final_model,
                messages=messages,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Replay not supported for provider: {final_provider}"
            )
        
        # Update replay_of field
        new_trace.replay_of = trace_id
        storage.save_trace(new_trace)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Replay execution failed: {str(e)}"
        )
    
    return ReplayResponse(
        original_trace_id=trace_id,
        new_trace_id=new_trace.trace_id,
        dry_run=False,
        overrides_applied=overrides,
        trace=new_trace.model_dump(),
    )


@router.get("/replay/{trace_id}/preview")
async def preview_replay(trace_id: str) -> dict:
    """
    Preview what a replay would execute without running it.
    """
    original = storage.get_trace(trace_id)
    
    if original is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    return {
        "original_trace_id": trace_id,
        "request": original.request.model_dump(),
        "original_response": original.response.model_dump(),
        "can_replay": original.request.provider.lower() in ["openai", "gemini"],
    }
