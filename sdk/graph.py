"""
Execution Graph Model (Phase 14+)

Represents execution as a Directed Acyclic Graph (DAG).

Design principles:
- Read-only after construction
- No mutation, no logic
- Edges written at runtime, not inferred later
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# =============================================================================
# Phase 19: Semantic Node Roles
# =============================================================================

class NodeRole(str, Enum):
    """
    Semantic role of a node in the execution graph.
    
    These roles make graphs self-describing and human-readable.
    """
    INPUT = "input"           # User input, API request
    TRANSFORM = "transform"   # Data transformation, parsing
    LLM = "llm"              # LLM call (default for traces)
    TOOL = "tool"            # Tool/function call
    VALIDATION = "validation" # Expectation check, validation
    OUTPUT = "output"         # Final output, response


class GraphNode(BaseModel):
    """
    A node in the execution graph (corresponds to one trace).
    
    Phase 19: Now includes semantic role and human-readable labels.
    """
    node_id: str
    trace_id: str
    
    # Phase 19: Semantic identification
    role: NodeRole = Field(default=NodeRole.LLM, description="Semantic role of this node")
    human_label: str = Field(default="", description="Human-readable label like 'Answer question'")
    description: str = Field(default="", description="Short description of what this node does")
    
    # Technical metadata
    node_type: str = Field(default="llm", description="llm | function | tool")
    model: Optional[str] = None
    provider: Optional[str] = None
    latency_ms: int = 0
    verdict_status: Optional[str] = None  # pass | fail | None
    label: str = ""  # Legacy short label
    
    class Config:
        frozen = True  # Immutable


class GraphEdge(BaseModel):
    """An edge in the execution graph (parent -> child relationship)."""
    from_node: str
    to_node: str
    edge_type: str = Field(default="calls", description="calls | data_flow")
    
    class Config:
        frozen = True  # Immutable


# =============================================================================
# Phase 20: Hierarchical Graphs
# =============================================================================

class GraphStage(BaseModel):
    """
    A stage groups related nodes together for hierarchical visualization.
    
    Stages enable:
    - Collapsible groups in UI
    - Zoom: Execution → Stages → Nodes
    - Readable large graphs
    """
    stage_id: str
    name: str = Field(description="Human-readable stage name")
    description: str = ""
    node_ids: list[str] = Field(default_factory=list)
    
    # Stage-level aggregates
    total_latency_ms: int = 0
    node_count: int = 0
    has_failure: bool = False
    
    # UI state (not persisted, set by client)
    collapsed: bool = Field(default=True, description="Whether stage is collapsed in UI")
    
    class Config:
        frozen = True


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


# =============================================================================
# Phase 23: Graph-Level Diffs
# =============================================================================

class NodeDiff(BaseModel):
    """Difference in a single node between two graphs."""
    node_label: str
    change_type: str = Field(description="added | removed | changed")
    latency_delta_ms: Optional[int] = None  # For changed nodes
    verdict_changed: bool = False
    old_verdict: Optional[str] = None
    new_verdict: Optional[str] = None


class GraphDiff(BaseModel):
    """
    Phase 23: Diff between two execution graphs.
    
    Enables comparison of:
    - Added/removed nodes
    - Latency changes
    - Verdict changes
    """
    execution_a: str
    execution_b: str
    
    added_nodes: list[NodeDiff] = Field(default_factory=list)
    removed_nodes: list[NodeDiff] = Field(default_factory=list)
    changed_nodes: list[NodeDiff] = Field(default_factory=list)
    
    # Summary
    total_changes: int = 0
    latency_delta_ms: int = 0  # B minus A
    verdict_changed: bool = False
    
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
    
    # Phase 20: Hierarchical stages
    stages: list[GraphStage] = Field(default_factory=list)
    
    # Graph-level metadata
    root_node_id: Optional[str] = None  # First node in execution
    total_latency_ms: int = 0
    node_count: int = 0
    
    # Phase 16: Graph verdict
    verdict: Optional[GraphVerdict] = None
    
    # Phase 25: Enterprise hardening
    integrity_hash: Optional[str] = Field(
        default=None,
        description="SHA256 hash for integrity verification"
    )
    snapshot_at: Optional[str] = Field(
        default=None,
        description="Timestamp when this snapshot was taken"
    )
    
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
        
        for i, trace in enumerate(traces):
            # Phase 19: Infer semantic role and labels
            role, human_label, description = _infer_semantics(trace, i, len(traces))
            
            # Create node with semantic metadata
            node = GraphNode(
                node_id=trace.node_id,
                trace_id=trace.trace_id,
                role=role,
                human_label=human_label,
                description=description,
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
        
        # Phase 20: Auto-generate stages based on node roles
        stages = _generate_stages(nodes)
        
        return cls(
            execution_id=execution_id,
            nodes=nodes,
            edges=edges,
            stages=stages,
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
    
    def diff_with(self, other: "ExecutionGraph") -> "GraphDiff":
        """
        Phase 23: Compare this graph with another graph.
        
        Args:
            other: Another ExecutionGraph to compare against
            
        Returns:
            GraphDiff object showing differences
        """
        # Build label-indexed maps for comparison
        # We compare by label (semantic content) not node_id (random UUID)
        self_nodes = {n.human_label or n.label: n for n in self.nodes}
        other_nodes = {n.human_label or n.label: n for n in other.nodes}
        
        self_labels = set(self_nodes.keys())
        other_labels = set(other_nodes.keys())
        
        added = []
        removed = []
        changed = []
        
        # Nodes only in 'other' (added)
        for label in other_labels - self_labels:
            node = other_nodes[label]
            added.append(NodeDiff(
                node_label=label,
                change_type="added",
                latency_delta_ms=node.latency_ms,
                new_verdict=node.verdict_status,
            ))
        
        # Nodes only in 'self' (removed)
        for label in self_labels - other_labels:
            node = self_nodes[label]
            removed.append(NodeDiff(
                node_label=label,
                change_type="removed",
                latency_delta_ms=-node.latency_ms,
                old_verdict=node.verdict_status,
            ))
        
        # Nodes in both (check for changes)
        for label in self_labels & other_labels:
            self_node = self_nodes[label]
            other_node = other_nodes[label]
            
            latency_delta = other_node.latency_ms - self_node.latency_ms
            verdict_changed = self_node.verdict_status != other_node.verdict_status
            
            if abs(latency_delta) > 50 or verdict_changed:  # 50ms threshold
                changed.append(NodeDiff(
                    node_label=label,
                    change_type="changed",
                    latency_delta_ms=latency_delta,
                    verdict_changed=verdict_changed,
                    old_verdict=self_node.verdict_status,
                    new_verdict=other_node.verdict_status,
                ))
        
        # Summary stats
        total_changes = len(added) + len(removed) + len(changed)
        latency_delta = other.total_latency_ms - self.total_latency_ms
        
        self_verdict = self.compute_verdict().status
        other_verdict = other.compute_verdict().status
        verdict_changed = self_verdict != other_verdict
        
        return GraphDiff(
            execution_a=self.execution_id,
            execution_b=other.execution_id,
            added_nodes=added,
            removed_nodes=removed,
            changed_nodes=changed,
            total_changes=total_changes,
            latency_delta_ms=latency_delta,
            verdict_changed=verdict_changed,
        )
    
    def investigation_path(self) -> list[dict]:
        """
        Phase 24: Generate a suggested investigation path for debugging.
        
        This is deterministic graph reasoning, not AI.
        It encodes how senior engineers debug:
        1. Start at failing node (root cause)
        2. Check its inputs (parent nodes)
        3. Review validation rules if any
        4. Check tainted downstream nodes
        
        Returns:
            List of investigation steps with node info and reasoning
        """
        steps = []
        verdict = self.compute_verdict()
        
        if verdict.status == "pass":
            return [{
                "step": 1,
                "action": "No failures detected",
                "node_id": None,
                "reasoning": "All nodes passed. No investigation needed.",
            }]
        
        # Step 1: Identify root cause node
        root_cause_id = verdict.root_cause_node
        root_cause = self.get_node(root_cause_id) if root_cause_id else None
        
        if root_cause:
            steps.append({
                "step": 1,
                "action": "Examine root cause",
                "node_id": root_cause.node_id,
                "label": root_cause.human_label or root_cause.label,
                "role": root_cause.role.value if hasattr(root_cause.role, 'value') else str(root_cause.role),
                "reasoning": "This is the first node that failed in the execution chain.",
            })
        
        # Step 2: Check input/parent node
        if root_cause_id:
            parent_id = self.get_parent(root_cause_id)
            if parent_id:
                parent = self.get_node(parent_id)
                if parent:
                    steps.append({
                        "step": 2,
                        "action": "Review input",
                        "node_id": parent.node_id,
                        "label": parent.human_label or parent.label,
                        "role": parent.role.value if hasattr(parent.role, 'value') else str(parent.role),
                        "reasoning": "Check what data was passed to the failing node.",
                    })
        
        # Step 3: Find any validation nodes
        validation_nodes = [n for n in self.nodes if (n.role.value if hasattr(n.role, 'value') else str(n.role)) == "validation"]
        if validation_nodes:
            vn = validation_nodes[0]
            steps.append({
                "step": len(steps) + 1,
                "action": "Review validation rules",
                "node_id": vn.node_id,
                "label": vn.human_label or vn.label,
                "role": "validation",
                "reasoning": "Check why validation failed and what rules were violated.",
            })
        
        # Step 4: Show tainted downstream nodes
        if root_cause_id:
            tainted = self.get_tainted_nodes(root_cause_id)
            if tainted:
                steps.append({
                    "step": len(steps) + 1,
                    "action": "Review blast radius",
                    "node_ids": tainted,
                    "count": len(tainted),
                    "reasoning": f"{len(tainted)} downstream node(s) may have been affected by this failure.",
                })
        
        return steps
    
    # =========================================================================
    # Phase 25: Enterprise Hardening
    # =========================================================================
    
    def compute_hash(self) -> str:
        """
        Compute SHA256 hash of the graph for integrity verification.
        
        The hash covers all immutable content:
        - execution_id, nodes, edges, stages
        - Excludes: snapshot_at, integrity_hash (circular)
        """
        import hashlib
        import json
        
        # Build canonical JSON representation
        canonical = {
            "execution_id": self.execution_id,
            "created_at": self.created_at,
            "nodes": [n.model_dump() for n in self.nodes],
            "edges": [e.model_dump() for e in self.edges],
            "root_node_id": self.root_node_id,
            "total_latency_ms": self.total_latency_ms,
            "node_count": self.node_count,
        }
        
        # Sort keys for deterministic output
        content = json.dumps(canonical, sort_keys=True, default=str)
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_snapshot(self) -> "ExecutionGraph":
        """
        Create an immutable snapshot with integrity hash and timestamp.
        
        Returns a new ExecutionGraph with:
        - integrity_hash set
        - snapshot_at timestamp
        """
        from datetime import datetime
        
        # Compute hash before snapshot
        hash_value = self.compute_hash()
        
        # Create new snapshot (Pydantic frozen models are immutable)
        return ExecutionGraph(
            execution_id=self.execution_id,
            created_at=self.created_at,
            nodes=self.nodes,
            edges=self.edges,
            stages=self.stages,
            root_node_id=self.root_node_id,
            total_latency_ms=self.total_latency_ms,
            node_count=self.node_count,
            verdict=self.verdict,
            integrity_hash=hash_value,
            snapshot_at=datetime.now().isoformat(),
        )
    
    def export_json(self, pretty: bool = True) -> str:
        """
        Export graph as JSON artifact for auditing.
        
        Args:
            pretty: If True, format with indentation
            
        Returns:
            JSON string representation
        """
        import json
        
        data = self.model_dump()
        
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
    
    def verify_integrity(self) -> bool:
        """
        Verify that the graph has not been tampered with.
        
        Returns:
            True if integrity_hash matches computed hash
        """
        if not self.integrity_hash:
            return False
        
        return self.compute_hash() == self.integrity_hash


def _get_label(trace) -> str:
    """Generate short label for a trace."""
    messages = trace.request.messages or []
    if messages:
        content = messages[0].content or ""
        return content[:30] + "..." if len(content) > 30 else content
    return trace.request.model or "unknown"


def _infer_semantics(trace, index: int, total: int) -> tuple:
    """
    Phase 19: Infer semantic role and generate human-readable labels.
    
    Returns:
        (role: NodeRole, human_label: str, description: str)
    """
    messages = trace.request.messages or []
    first_content = messages[0].content.lower() if messages and messages[0].content else ""
    model = trace.request.model or ""
    provider = trace.request.provider or ""
    has_verdict = trace.verdict is not None
    
    # Infer role based on context
    role = NodeRole.LLM  # Default
    
    # Check if this is a validation step
    if has_verdict or "check" in first_content or "validate" in first_content or "verify" in first_content:
        role = NodeRole.VALIDATION
    # Check for input/parsing patterns
    elif "parse" in first_content or "extract" in first_content:
        role = NodeRole.TRANSFORM
    # First node is often input handler
    elif index == 0 and trace.parent_node_id is None:
        role = NodeRole.INPUT
    # Last node might be output
    elif index == total - 1:
        role = NodeRole.OUTPUT
    
    # Generate human-readable label
    if first_content:
        # Capitalize first letter, truncate to readable length
        label_text = first_content[:40].strip()
        if len(first_content) > 40:
            label_text += "..."
        # Capitalize first letter
        human_label = label_text[0].upper() + label_text[1:] if label_text else ""
    else:
        human_label = f"{role.value.title()} ({model})"
    
    # Generate description
    role_desc = {
        NodeRole.INPUT: "Handles incoming request",
        NodeRole.TRANSFORM: "Transforms or parses data",
        NodeRole.LLM: f"LLM call to {model}",
        NodeRole.TOOL: "Executes tool or function",
        NodeRole.VALIDATION: "Validates expectations",
        NodeRole.OUTPUT: "Produces final output",
    }
    description = role_desc.get(role, f"LLM call via {provider}")
    
    return role, human_label, description


def _generate_stages(nodes: list) -> list:
    """
    Phase 20: Auto-generate stages by grouping consecutive nodes with similar roles.
    
    This creates a hierarchical view:
    - Input Processing
    - LLM Reasoning  
    - Validation
    - Output
    """
    import uuid
    
    if not nodes:
        return []
    
    stages = []
    current_group = None
    current_nodes = []
    
    # Stage name templates by role
    stage_names = {
        NodeRole.INPUT: "Input Processing",
        NodeRole.TRANSFORM: "Data Transformation",
        NodeRole.LLM: "LLM Processing",
        NodeRole.TOOL: "Tool Execution",
        NodeRole.VALIDATION: "Validation",
        NodeRole.OUTPUT: "Output Generation",
    }
    
    for node in nodes:
        role = node.role
        
        # Start new group if role changes
        if current_group != role:
            if current_nodes:
                # Finalize previous stage
                stage = GraphStage(
                    stage_id=str(uuid.uuid4()),
                    name=stage_names.get(current_group, "Processing"),
                    description=f"{len(current_nodes)} node(s)",
                    node_ids=[n.node_id for n in current_nodes],
                    total_latency_ms=sum(n.latency_ms for n in current_nodes),
                    node_count=len(current_nodes),
                    has_failure=any(n.verdict_status == "fail" for n in current_nodes),
                )
                stages.append(stage)
            
            current_group = role
            current_nodes = [node]
        else:
            current_nodes.append(node)
    
    # Finalize last stage
    if current_nodes:
        stage = GraphStage(
            stage_id=str(uuid.uuid4()),
            name=stage_names.get(current_group, "Processing"),
            description=f"{len(current_nodes)} node(s)",
            node_ids=[n.node_id for n in current_nodes],
            total_latency_ms=sum(n.latency_ms for n in current_nodes),
            node_count=len(current_nodes),
            has_failure=any(n.verdict_status == "fail" for n in current_nodes),
        )
        stages.append(stage)
    
    return stages
