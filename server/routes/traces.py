"""
Traces Routes

Endpoints for trace CRUD operations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from sdk.schema import Trace
from server.storage.files import FileStorage

router = APIRouter()
storage = FileStorage()


@router.get("/traces")
async def list_traces(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    model: Optional[str] = None,
    provider: Optional[str] = None,
    date: Optional[str] = None,
) -> dict:
    """
    List all traces with optional filtering.
    
    Args:
        limit: Maximum number of traces to return
        offset: Number of traces to skip
        model: Filter by model name
        provider: Filter by provider
        date: Filter by date (YYYY-MM-DD format)
    """
    traces = storage.list_traces(
        limit=limit,
        offset=offset,
        model=model,
        provider=provider,
        date=date,
    )
    
    total = storage.count_traces(model=model, provider=provider, date=date)
    
    return {
        "traces": [t.model_dump() for t in traces],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str) -> dict:
    """Get a specific trace by ID."""
    trace = storage.get_trace(trace_id)
    
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    return trace.model_dump()


@router.post("/traces")
async def create_trace(trace: Trace) -> dict:
    """Create a new trace."""
    storage.save_trace(trace)
    return {"status": "created", "trace_id": trace.trace_id}


@router.delete("/traces/{trace_id}")
async def delete_trace(trace_id: str) -> dict:
    """Delete a trace by ID."""
    success = storage.delete_trace(trace_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    return {"status": "deleted", "trace_id": trace_id}


@router.get("/traces/{trace_id}/lineage")
async def get_trace_lineage(trace_id: str) -> dict:
    """Get the lineage chain for a trace (original → replays)."""
    trace = storage.get_trace(trace_id)
    
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    lineage = storage.get_lineage(trace_id)
    
    return {
        "trace_id": trace_id,
        "lineage": [t.model_dump() for t in lineage],
    }


# =============================================================================
# Phase 14: Graph Endpoints
# =============================================================================

@router.get("/executions")
async def list_executions() -> dict:
    """List all unique execution IDs."""
    executions = storage.list_executions()
    return {"executions": executions, "count": len(executions)}


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str) -> dict:
    """Get all traces for an execution."""
    traces = storage.get_traces_by_execution(execution_id)
    
    if not traces:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    return {
        "execution_id": execution_id,
        "traces": [t.model_dump() for t in traces],
        "count": len(traces),
    }


@router.get("/executions/{execution_id}/graph")
async def get_execution_graph(execution_id: str) -> dict:
    """Get the execution graph for a specific execution."""
    graph = storage.get_execution_graph(execution_id)
    
    if graph is None:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    return graph.model_dump()


# =============================================================================
# Phase 18: Performance Analysis Endpoints
# =============================================================================

@router.get("/executions/{execution_id}/analysis")
async def analyze_execution(execution_id: str) -> dict:
    """
    Phase 18: Complete performance analysis for an execution.
    
    Returns:
    - Critical path (longest latency chain)
    - Bottleneck nodes
    - Graph verdict
    """
    graph = storage.get_execution_graph(execution_id)
    
    if graph is None:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    return {
        "execution_id": execution_id,
        "node_count": graph.node_count,
        "total_latency_ms": graph.total_latency_ms,
        "critical_path": graph.critical_path(),
        "bottlenecks": graph.find_bottlenecks(top_n=3),
        "verdict": graph.compute_verdict().model_dump(),
    }
