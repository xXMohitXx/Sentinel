"""
Trace Schema - Single Source of Truth

All traces conform to this schema. Design rules:
- Immutable after creation
- JSON-serializable
- Portable across machines
- Verdicts are computed at trace creation time and never recalculated
"""

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
import uuid


# Severity levels for verdict violations
SeverityLevel = Literal["low", "medium", "high"]


class Verdict(BaseModel):
    """
    Immutable verdict for an LLM call.
    
    DESIGN RULE: Once a verdict is written to a trace, it MUST NEVER
    be recalculated or modified. This maintains trace as an audit artifact.
    """
    status: Literal["pass", "fail"]
    severity: Optional[SeverityLevel] = None  # None when passing
    violations: list[str] = []
    
    class Config:
        frozen = True  # Enforce immutability


class TraceParameters(BaseModel):
    """LLM request parameters."""
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 256
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[list[str]] = None


class TraceMessage(BaseModel):
    """A single message in the conversation."""
    role: str
    content: str
    name: Optional[str] = None


class TraceRequest(BaseModel):
    """The request portion of a trace."""
    provider: str = Field(description="openai | local | custom | gemini")
    model: str
    messages: list[TraceMessage]
    parameters: TraceParameters = Field(default_factory=TraceParameters)


class TraceResponse(BaseModel):
    """The response portion of a trace."""
    text: str
    tokens: Optional[list[str]] = None
    latency_ms: int
    usage: Optional[dict[str, int]] = None


class TraceRuntime(BaseModel):
    """Runtime environment information."""
    library: str = Field(description="openai | llama_cpp | transformers | gemini")
    version: str


class Trace(BaseModel):
    """
    Complete trace record.
    
    This is the canonical schema for all LLM call traces.
    """
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    request: TraceRequest
    response: TraceResponse
    runtime: TraceRuntime
    replay_of: Optional[str] = Field(
        default=None,
        description="If this trace is a replay, the original trace_id"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional user-defined metadata"
    )
    # Phase 8: Verdict (immutable once written)
    verdict: Optional[Verdict] = Field(
        default=None,
        description="Pass/fail verdict with violations. Immutable once set."
    )
    # Phase 9: Golden trace support
    blessed: bool = Field(
        default=False,
        description="If true, this trace is a golden reference"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-01-17T02:00:00.000000",
                "request": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello!"}],
                    "parameters": {"temperature": 0.7, "max_tokens": 256}
                },
                "response": {
                    "text": "Hello! How can I help you today?",
                    "latency_ms": 1234
                },
                "runtime": {
                    "library": "openai",
                    "version": "1.0.0"
                },
                "replay_of": None,
                "verdict": {
                    "status": "pass",
                    "severity": None,
                    "violations": []
                },
                "blessed": False
            }
        }

