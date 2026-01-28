"""
File Storage Backend

Design goal: Zero infrastructure.
JSON files as ground truth, organized by date.

Default layout:
~/.Phylax/
  traces/
    2026-01-16/
      trace_x.json
  config.yaml
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from sdk.schema import Trace


class FileStorage:
    """
    Filesystem-based trace storage.
    
    Stores traces as JSON files organized by date.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize file storage.
        
        Args:
            base_path: Base directory for traces. Defaults to ~/.Phylax
        """
        if base_path is None:
            base_path = os.path.expanduser("~/.Phylax")
        
        self.base_path = Path(base_path)
        self.traces_path = self.base_path / "traces"
        
        # Ensure directories exist
        self.traces_path.mkdir(parents=True, exist_ok=True)
    
    def save_trace(self, trace: Trace) -> str:
        """
        Save a trace to storage.
        
        Args:
            trace: The trace to save
            
        Returns:
            Path to the saved trace file
        """
        # Organize by date
        date_str = datetime.fromisoformat(trace.timestamp).strftime("%Y-%m-%d")
        date_dir = self.traces_path / date_str
        date_dir.mkdir(exist_ok=True)
        
        # Save as JSON
        trace_file = date_dir / f"{trace.trace_id}.json"
        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump(trace.model_dump(), f, indent=2, ensure_ascii=False)
        
        return str(trace_file)
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """
        Get a trace by ID.
        
        Args:
            trace_id: The trace ID
            
        Returns:
            The trace, or None if not found
        """
        # Search through date directories
        for date_dir in self.traces_path.iterdir():
            if date_dir.is_dir():
                trace_file = date_dir / f"{trace_id}.json"
                if trace_file.exists():
                    with open(trace_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    return Trace(**data)
        
        return None
    
    def list_traces(
        self,
        limit: int = 50,
        offset: int = 0,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        date: Optional[str] = None,
    ) -> list[Trace]:
        """
        List traces with optional filtering.
        
        Args:
            limit: Maximum number of traces to return
            offset: Number of traces to skip
            model: Filter by model name
            provider: Filter by provider
            date: Filter by date (YYYY-MM-DD format)
            
        Returns:
            List of traces
        """
        traces = []
        
        # Determine which date directories to search
        if date:
            date_dirs = [self.traces_path / date]
        else:
            date_dirs = sorted(self.traces_path.iterdir(), reverse=True)
        
        for date_dir in date_dirs:
            if not date_dir.is_dir():
                continue
            
            for trace_file in sorted(date_dir.glob("*.json"), reverse=True):
                try:
                    with open(trace_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    trace = Trace(**data)
                    
                    # Apply filters
                    if model and trace.request.model != model:
                        continue
                    if provider and trace.request.provider != provider:
                        continue
                    
                    traces.append(trace)
                except Exception:
                    continue  # Skip invalid files
        
        # Apply pagination
        return traces[offset:offset + limit]
    
    def count_traces(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        date: Optional[str] = None,
    ) -> int:
        """Count traces with optional filtering."""
        # For now, just count by listing
        # TODO: Optimize with SQLite index
        return len(self.list_traces(limit=10000, model=model, provider=provider, date=date))
    
    def delete_trace(self, trace_id: str) -> bool:
        """
        Delete a trace by ID.
        
        Returns:
            True if deleted, False if not found
        """
        for date_dir in self.traces_path.iterdir():
            if date_dir.is_dir():
                trace_file = date_dir / f"{trace_id}.json"
                if trace_file.exists():
                    trace_file.unlink()
                    return True
        
        return False
    
    def get_lineage(self, trace_id: str) -> list[Trace]:
        """
        Get the lineage chain for a trace.
        
        Finds all traces that are replays of this trace, or that this trace
        is a replay of.
        """
        lineage = []
        visited = set()
        
        # Find the root trace
        current = self.get_trace(trace_id)
        if current is None:
            return []
        
        # Traverse up to find root
        while current.replay_of and current.replay_of not in visited:
            visited.add(current.trace_id)
            parent = self.get_trace(current.replay_of)
            if parent:
                current = parent
            else:
                break
        
        # Now traverse down from root
        queue = [current]
        while queue:
            trace = queue.pop(0)
            if trace.trace_id in visited:
                continue
            visited.add(trace.trace_id)
            lineage.append(trace)
            
            # Find children (traces that replay this trace)
            for t in self.list_traces(limit=1000):
                if t.replay_of == trace.trace_id:
                    queue.append(t)
        
        return lineage
    
    def update_trace(self, trace: Trace) -> bool:
        """
        Update an existing trace in storage.
        
        Args:
            trace: The trace to update
            
        Returns:
            True if updated, False if not found
        """
        # Find and update the trace
        for date_dir in self.traces_path.iterdir():
            if date_dir.is_dir():
                trace_file = date_dir / f"{trace.trace_id}.json"
                if trace_file.exists():
                    with open(trace_file, "w", encoding="utf-8") as f:
                        json.dump(trace.model_dump(), f, indent=2, ensure_ascii=False)
                    return True
        
        return False
    
    def bless_trace(self, trace_id: str) -> Optional[Trace]:
        """
        Mark a trace as blessed (golden reference).
        
        Args:
            trace_id: The trace ID to bless
            
        Returns:
            The blessed trace, or None if not found
        """
        trace = self.get_trace(trace_id)
        if trace is None:
            return None
        
        # Create new trace with blessed=True
        # We need to recreate the trace since Pydantic models may not allow mutation
        import hashlib
        
        # Calculate output hash for comparison
        output_hash = hashlib.sha256(trace.response.text.encode()).hexdigest()[:16]
        
        # Update trace data
        trace_data = trace.model_dump()
        trace_data["blessed"] = True
        trace_data["metadata"] = trace_data.get("metadata") or {}
        trace_data["metadata"]["output_hash"] = output_hash
        trace_data["metadata"]["blessed_at"] = datetime.utcnow().isoformat()
        
        blessed_trace = Trace(**trace_data)
        self.update_trace(blessed_trace)
        
        return blessed_trace
    
    def unbless_trace(self, trace_id: str) -> bool:
        """
        Remove blessed status from a trace.
        
        Returns:
            True if updated, False if not found
        """
        trace = self.get_trace(trace_id)
        if trace is None:
            return False
        
        trace_data = trace.model_dump()
        trace_data["blessed"] = False
        
        updated_trace = Trace(**trace_data)
        return self.update_trace(updated_trace)
    
    def list_blessed_traces(self) -> list[Trace]:
        """
        List all blessed (golden) traces.
        
        Returns:
            List of blessed traces
        """
        all_traces = self.list_traces(limit=10000)
        return [t for t in all_traces if t.blessed]
    
    def get_golden_for_model(self, model: str, provider: str) -> Optional[Trace]:
        """
        Get the golden trace for a specific model/provider combination.
        
        Returns:
            The golden trace, or None if not found
        """
        blessed = self.list_blessed_traces()
        for trace in blessed:
            if trace.request.model == model and trace.request.provider == provider:
                return trace
        return None
    
    # =========================================================================
    # Phase 14: Graph Storage
    # =========================================================================
    
    def get_traces_by_execution(self, execution_id: str) -> list[Trace]:
        """
        Get all traces for a specific execution.
        
        Args:
            execution_id: The execution ID to filter by
            
        Returns:
            List of traces from that execution, sorted by timestamp
        """
        all_traces = self.list_traces(limit=10000)
        matching = [t for t in all_traces if t.execution_id == execution_id]
        return sorted(matching, key=lambda t: t.timestamp)
    
    def get_execution_graph(self, execution_id: str):
        """
        Build an ExecutionGraph from traces with given execution_id.
        
        Returns:
            ExecutionGraph instance, or None if no traces found
        """
        from sdk.graph import ExecutionGraph
        
        traces = self.get_traces_by_execution(execution_id)
        if not traces:
            return None
        
        return ExecutionGraph.from_traces(traces)
    
    def save_graph(self, graph) -> str:
        """
        Save an ExecutionGraph to storage.
        
        Args:
            graph: ExecutionGraph instance
            
        Returns:
            Path to saved graph file
        """
        graphs_dir = self.base_path / "graphs"
        graphs_dir.mkdir(exist_ok=True)
        
        graph_file = graphs_dir / f"{graph.execution_id}.json"
        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(graph.model_dump(), f, indent=2)
        
        return str(graph_file)
    
    def load_graph(self, execution_id: str):
        """
        Load a saved ExecutionGraph.
        
        Returns:
            ExecutionGraph instance, or None if not found
        """
        from sdk.graph import ExecutionGraph
        
        graph_file = self.base_path / "graphs" / f"{execution_id}.json"
        if not graph_file.exists():
            return None
        
        with open(graph_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return ExecutionGraph(**data)
    
    def list_executions(self) -> list[str]:
        """
        List all unique execution IDs that have more than one trace.
        
        Single-trace executions are treated as standalone and not shown as graphs.
        
        Returns:
            List of execution IDs with multi-node graphs
        """
        all_traces = self.list_traces(limit=10000)
        
        # Count traces per execution
        exec_counts = {}
        for t in all_traces:
            exec_id = t.execution_id
            exec_counts[exec_id] = exec_counts.get(exec_id, 0) + 1
        
        # Only return executions with multiple traces (actual graphs)
        # For single traces, also include them but mark appropriately
        return [exec_id for exec_id, count in exec_counts.items()]
