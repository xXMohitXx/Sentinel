# Phylax Graph Model

> **How to read and debug execution graphs.**

---

## What Is an Execution Graph?

When you use `with execution("name"):`, all LLM calls inside become nodes in a **directed acyclic graph (DAG)**.

```python
from sdk.context import execution

with execution("my-agent"):
    step1 = call_llm("Parse input")      # Node 1
    step2 = call_llm("Analyze")          # Node 2 (child of 1)
    step3 = call_llm("Generate output")  # Node 3 (child of 2)
```

This creates:
```
[Parse input] → [Analyze] → [Generate output]
```

---

## Graph Terminology

| Term | Meaning |
|------|---------|
| **Node** | One LLM call (trace) |
| **Edge** | Causality (parent → child) |
| **Root** | First node (no parent) |
| **Leaf** | Last node (no children) |
| **Stage** | Group of related nodes |
| **Critical Path** | Longest latency chain |

---

## Reading the UI

### Node Display

```
┌─────────────────────────────────────┐
│ ✅ 🤖 Parse User Input              │
│ LLM node | 150ms                    │
├─────────────────────────────────────┤
│ ████████████░░░░░░░ (latency bar)   │
└─────────────────────────────────────┘
```

- **✅/❌**: Pass or fail status
- **🤖/📥/🔧**: Node role icon
- **Label**: What the node does
- **Latency bar**: Visual time representation

### Node Roles

| Icon | Role | Meaning |
|------|------|---------|
| 📥 | INPUT | Receives external data |
| 🔄 | TRANSFORM | Data processing |
| 🤖 | LLM | AI model call |
| 🔧 | TOOL | External tool call |
| ✓ | VALIDATION | Output verification |
| 📤 | OUTPUT | Final result |

### Status Colors

| Color | Meaning |
|-------|---------|
| Green | Passed |
| Red | Failed |
| Yellow | Tainted (downstream of failure) |
| Gray | Pending/Unknown |

---

## Graph Verdict

The graph has an overall verdict:

```python
verdict = graph.compute_verdict()
# GraphVerdict(
#   status="fail",
#   root_cause_node="node-123",
#   failed_count=1,
#   tainted_count=2
# )
```

### Rules

1. **If ANY node fails → graph fails**
2. **Root cause = topologically first failing node**
3. **Tainted = all descendants of failed nodes**

---

## Forensics Mode

Toggle "🔬 Forensics Mode" to:

1. **Fade** non-relevant nodes
2. **Highlight** failure chain
3. **Pulse** root cause node
4. **Show** tainted downstream nodes

This helps you focus on what matters.

---

## Investigation Path

Phylax suggests a debug path:

```python
steps = graph.investigation_path()
# [
#   {step: 1, action: "Examine root cause", node_id: "..."},
#   {step: 2, action: "Review input", node_id: "..."},
#   {step: 3, action: "Review blast radius", count: 2}
# ]
```

This encodes how senior engineers debug:

1. **Start at root cause** — What failed first?
2. **Check parent input** — What data triggered the failure?
3. **Review validation** — Which rule was violated?
4. **Assess blast radius** — What else was affected?

---

## Critical Path

The critical path is the **longest latency chain**:

```python
path = graph.critical_path()
# {
#   path: ["node-1", "node-2", "node-3"],
#   total_latency_ms: 1500,
#   bottleneck_node: "node-2"
# }
```

Use this to find performance bottlenecks.

---

## Stages (Hierarchical View)

Graphs auto-group into stages:

| Stage | Contains |
|-------|----------|
| Input | INPUT nodes |
| Processing | TRANSFORM, LLM nodes |
| Validation | VALIDATION nodes |
| Output | OUTPUT nodes |

Click a stage header to collapse/expand.

---

## Graph APIs

### Get Graph
```bash
curl http://127.0.0.1:8000/v1/executions/{id}/graph
```

### Analyze Performance
```bash
curl http://127.0.0.1:8000/v1/executions/{id}/analysis
```

### Get Debug Path
```bash
curl http://127.0.0.1:8000/v1/executions/{id}/investigate
```

### Compare Two Graphs
```bash
curl http://127.0.0.1:8000/v1/executions/{a}/diff/{b}
```

---

## Example Graph

```
Execution: customer-support-agent
Total: 1200ms | 4 nodes | ❌ FAIL

Input Stage
  └─ 📥 Parse Query (100ms) ✅

Processing Stage
  ├─ 🤖 Classify Intent (200ms) ✅
  └─ 🔧 Fetch Knowledge (500ms) ❌ ← Root cause

Output Stage
  └─ 🤖 Generate Reply (400ms) ⚠️ TAINTED
```

Debug path:
1. Check "Fetch Knowledge" — why did tool fail?
2. Check "Classify Intent" — was intent parsed correctly?
3. Note "Generate Reply" is tainted (may have bad data)
