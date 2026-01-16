"""
File Storage Backend

Design goal: Zero infrastructure.
JSON files as ground truth, organized by date.

Default layout:
~/.sentinel/
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
            base_path: Base directory for traces. Defaults to ~/.sentinel
        """
        if base_path is None:
            base_path = os.path.expanduser("~/.sentinel")
        
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
