"""
SQLite Index Backend

Optional but default indexing layer for fast queries.
The JSON files remain the ground truth.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from sdk.schema import Trace


class SQLiteIndex:
    """
    SQLite-based index for fast trace queries.
    
    This is an optional optimization layer. The JSON files remain the
    source of truth.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite index.
        
        Args:
            db_path: Path to SQLite database. Defaults to ~/.Phylax/index.sqlite
        """
        if db_path is None:
            import os
            base_path = os.path.expanduser("~/.Phylax")
            Path(base_path).mkdir(parents=True, exist_ok=True)
            db_path = os.path.join(base_path, "index.sqlite")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    latency_ms INTEGER,
                    replay_of TEXT,
                    file_path TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_timestamp
                ON traces(timestamp DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_model
                ON traces(model)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_provider
                ON traces(provider)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_replay_of
                ON traces(replay_of)
            """)
            
            conn.commit()
    
    def index_trace(self, trace: Trace, file_path: str):
        """
        Add a trace to the index.
        
        Args:
            trace: The trace to index
            file_path: Path to the JSON file
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO traces
                (trace_id, timestamp, provider, model, latency_ms, replay_of, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                trace.trace_id,
                trace.timestamp,
                trace.request.provider,
                trace.request.model,
                trace.response.latency_ms,
                trace.replay_of,
                file_path,
            ))
            conn.commit()
    
    def search(
        self,
        limit: int = 50,
        offset: int = 0,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        date: Optional[str] = None,
    ) -> list[dict]:
        """
        Search traces using the index.
        
        Returns:
            List of dicts with trace_id and file_path
        """
        query = "SELECT trace_id, file_path FROM traces WHERE 1=1"
        params = []
        
        if model:
            query += " AND model = ?"
            params.append(model)
        
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        
        if date:
            query += " AND timestamp LIKE ?"
            params.append(f"{date}%")
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def count(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        date: Optional[str] = None,
    ) -> int:
        """Count traces matching the filter criteria."""
        query = "SELECT COUNT(*) FROM traces WHERE 1=1"
        params = []
        
        if model:
            query += " AND model = ?"
            params.append(model)
        
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        
        if date:
            query += " AND timestamp LIKE ?"
            params.append(f"{date}%")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
    
    def get_lineage_ids(self, trace_id: str) -> list[str]:
        """Get all trace IDs in the lineage chain."""
        lineage = []
        visited = set()
        
        # Find root
        current_id = trace_id
        with sqlite3.connect(self.db_path) as conn:
            while current_id and current_id not in visited:
                visited.add(current_id)
                cursor = conn.execute(
                    "SELECT replay_of FROM traces WHERE trace_id = ?",
                    (current_id,)
                )
                row = cursor.fetchone()
                if row and row[0]:
                    current_id = row[0]
                else:
                    break
            
            # Now find all descendants
            queue = [current_id]
            while queue:
                tid = queue.pop(0)
                if tid in lineage:
                    continue
                lineage.append(tid)
                
                cursor = conn.execute(
                    "SELECT trace_id FROM traces WHERE replay_of = ?",
                    (tid,)
                )
                for row in cursor.fetchall():
                    queue.append(row[0])
        
        return lineage
    
    def remove(self, trace_id: str):
        """Remove a trace from the index."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM traces WHERE trace_id = ?", (trace_id,))
            conn.commit()
