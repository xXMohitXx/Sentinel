"""
Execution Graph Model (Phase 14)

Represents execution as a Directed Acyclic Graph (DAG).

Design principles:
- Read-only after construction
- No mutation, no logic
- Edges written at runtime, not inferred later
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class GraphNode(BaseModel):
    """A node in the execution graph (corresponds to one trace)."""
    node_id: str
    trace_id: str
    node_type: str = Field(default="llm", description="llm | function | tool")
    model: Optional[str] = None
    provider: Optional[str] = None
    latency_ms: int = 0
    verdict_status: Optional[str] = None  # pass | fail | None
    label: str = ""  # Short label for display
    
    class Config:
        frozen = True  # Immutable


class GraphEdge(BaseModel):
    """An edge in the execution graph (parent -> child relationship)."""
    from_node: str
    to_node: str
    edge_type: str = Field(default="calls", description="calls | data_flow")
    
    class Config:
        frozen = True  # Immutable


class GraphVerdict(BaseModel):
    """
    Phase 16: Graph-level verdict.
    
    Determines if the entire execution passed or failed,
    and identifies the root cause node.
    """
    status: str = Field(description="pass | fail")
    root_cause_node: Optional[str] = Field(
        default=None, 
        description="First failing node in topological order"
    )
    failed_count: int = 0
    tainted_count: int = 0
    message: str = ""
    
    class Config:
        frozen = True


class ExecutionGraph(BaseModel):
    """
    Complete execution graph.
    
    This is a read-only snapshot of one program execution.
    All nodes and edges are immutable after construction.
    """
    execution_id: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    
    # Graph-level metadata
    root_node_id: Optional[str] = None  # First node in execution
    total_latency_ms: int = 0
    node_count: int = 0
    
    # Phase 16: Graph verdict
    verdict: Optional[GraphVerdict] = None
    
    class Config:
        frozen = True  # Immutable
    
    @classmethod
    def from_traces(cls, traces: list) -> "ExecutionGraph":
        """
        Build a graph from a list of traces with same execution_id.
        
        Args:
            traces: List of Trace objects with same execution_id
            
        Returns:
            ExecutionGraph instance
        """
        if not traces:
            raise ValueError("Cannot create graph from empty trace list")
        
        execution_id = traces[0].execution_id
        
        # Build nodes
        nodes = []
        edges = []
        root_node_id = None
        total_latency = 0
        
        for trace in traces:
            # Create node
            node = GraphNode(
                node_id=trace.node_id,
                trace_id=trace.trace_id,
                node_type="llm",
                model=trace.request.model,
                provider=trace.request.provider,
                latency_ms=trace.response.latency_ms,
                verdict_status=trace.verdict.status if trace.verdict else None,
                label=_get_label(trace),
            )
            nodes.append(node)
            total_latency += trace.response.latency_ms
            
            # Create edge if has parent
            if trace.parent_node_id:
                edge = GraphEdge(
                    from_node=trace.parent_node_id,
                    to_node=trace.node_id,
                )
                edges.append(edge)
            else:
                # This is a root node
                if root_node_id is None:
                    root_node_id = trace.node_id
        
        return cls(
            execution_id=execution_id,
            nodes=nodes,
            edges=edges,
            root_node_id=root_node_id,
            total_latency_ms=total_latency,
            node_count=len(nodes),
        )
    
    def get_children(self, node_id: str) -> list[str]:
        """Get all direct children of a node."""
        return [e.to_node for e in self.edges if e.from_node == node_id]
    
    def get_parent(self, node_id: str) -> Optional[str]:
        """Get parent of a node."""
        for e in self.edges:
            if e.to_node == node_id:
                return e.from_node
        return None
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        return None
    
    def topological_order(self) -> list[str]:
        """Return node IDs in topological order (parents before children)."""
        # Build adjacency list
        children: dict[str, list[str]] = {n.node_id: [] for n in self.nodes}
        in_degree: dict[str, int] = {n.node_id: 0 for n in self.nodes}
        
        for e in self.edges:
            if e.from_node in children:
                children[e.from_node].append(e.to_node)
            if e.to_node in in_degree:
                in_degree[e.to_node] += 1
        
        # Kahn's algorithm
        queue = [n for n, d in in_degree.items() if d == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            for child in children.get(node, []):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        
        return result
    
    def get_failed_nodes(self) -> list[GraphNode]:
        """Get all nodes with failed verdicts."""
        return [n for n in self.nodes if n.verdict_status == "fail"]
    
    def get_tainted_nodes(self, failed_node_id: str) -> list[str]:
        """Get all nodes downstream of a failed node (blast radius)."""
        tainted = set()
        queue = [failed_node_id]
        
        while queue:
            node_id = queue.pop(0)
            if node_id not in tainted:
                tainted.add(node_id)
                queue.extend(self.get_children(node_id))
        
        return list(tainted)
    
    def compute_verdict(self) -> GraphVerdict:
        """
        Phase 16: Compute graph-level verdict.
        
        Rules:
        - Graph fails if any node fails
        - Root cause = first failing node in topological order
        - Tainted = all nodes downstream of failures
        """
        failed_nodes = self.get_failed_nodes()
        
        if not failed_nodes:
            return GraphVerdict(
                status="pass",
                message="All nodes passed"
            )
        
        # Find root cause: first failure in topological order
        topo_order = self.topological_order()
        failed_ids = {n.node_id for n in failed_nodes}
        
        root_cause = None
        for node_id in topo_order:
            if node_id in failed_ids:
                root_cause = node_id
                break
        
        # Calculate blast radius (tainted nodes)
        all_tainted = set()
        for node in failed_nodes:
            all_tainted.update(self.get_tainted_nodes(node.node_id))
        
        # Don't count failed nodes as tainted
        tainted_only = all_tainted - failed_ids
        
        root_node = self.get_node(root_cause) if root_cause else None
        root_label = root_node.label if root_node else "unknown"
        
        return GraphVerdict(
            status="fail",
            root_cause_node=root_cause,
            failed_count=len(failed_nodes),
            tainted_count=len(tainted_only),
            message=f"Root cause: {root_label}"
        )
    
    # =========================================================================
    # Phase 18: Performance Analysis
    # =========================================================================
    
    def critical_path(self) -> dict:
        """
        Find the critical path (longest latency path) through the graph.
        
        Returns:
            dict with path (node IDs), total_latency, and bottleneck node
        """
        if not self.nodes:
            return {"path": [], "total_latency_ms": 0, "bottleneck": None}
        
        # Build adjacency and latency maps
        latency = {n.node_id: n.latency_ms for n in self.nodes}
        children: dict[str, list[str]] = {n.node_id: [] for n in self.nodes}
        parents: dict[str, list[str]] = {n.node_id: [] for n in self.nodes}
        
        for e in self.edges:
            if e.from_node in children:
                children[e.from_node].append(e.to_node)
            if e.to_node in parents:
                parents[e.to_node].append(e.from_node)
        
        # Find all end nodes (no children)
        end_nodes = [n.node_id for n in self.nodes if not children[n.node_id]]
        
        # Calculate longest path to each node (dynamic programming)
        longest_to = {n.node_id: (latency[n.node_id], [n.node_id]) for n in self.nodes}
        
        for node_id in self.topological_order():
            for parent in parents[node_id]:
                parent_dist, parent_path = longest_to[parent]
                new_dist = parent_dist + latency[node_id]
                if new_dist > longest_to[node_id][0]:
                    longest_to[node_id] = (new_dist, parent_path + [node_id])
        
        # Find the end node with longest path
        best_end = max(end_nodes, key=lambda n: longest_to[n][0]) if end_nodes else None
        
        if not best_end:
            return {"path": [], "total_latency_ms": 0, "bottleneck": None}
        
        path_dist, path = longest_to[best_end]
        
        # Find bottleneck (slowest node on critical path)
        bottleneck = max(path, key=lambda n: latency.get(n, 0))
        
        return {
            "path": path,
            "total_latency_ms": path_dist,
            "bottleneck_node": bottleneck,
            "bottleneck_latency_ms": latency.get(bottleneck, 0),
        }
    
    def find_bottlenecks(self, top_n: int = 3) -> list[dict]:
        """
        Find the slowest nodes in the graph.
        
        Args:
            top_n: Number of bottlenecks to return
            
        Returns:
            List of dicts with node_id, latency_ms, percentage of total
        """
        if not self.nodes or self.total_latency_ms == 0:
            return []
        
        sorted_nodes = sorted(self.nodes, key=lambda n: n.latency_ms, reverse=True)
        
        return [
            {
                "node_id": n.node_id,
                "label": n.label,
                "latency_ms": n.latency_ms,
                "percent_of_total": round(n.latency_ms / self.total_latency_ms * 100, 1),
            }
            for n in sorted_nodes[:top_n]
        ]


def _get_label(trace) -> str:
    """Generate short label for a trace."""
    messages = trace.request.messages or []
    if messages:
        content = messages[0].content or ""
        return content[:30] + "..." if len(content) > 30 else content
    return trace.request.model or "unknown"
