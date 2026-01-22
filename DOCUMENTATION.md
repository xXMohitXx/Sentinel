# Sentinel Documentation

Complete technical reference for Sentinel — the LLM regression prevention tool.

---

## Overview

Sentinel prevents LLM regressions from reaching production by:
1. **Recording** every LLM call
2. **Evaluating** expectations (PASS/FAIL)
3. **Comparing** against golden baselines
4. **Visualizing** execution graphs
5. **Failing CI** when outputs regress

### Status: ✅ COMPLETE (v0.5.0)

All features implemented and ready for production use.

---

## SDK Reference

### Installation
```python
from sdk.decorator import trace, expect
from sdk.context import execution
from sdk.adapters.gemini import GeminiAdapter
from sdk.adapters.openai import OpenAIAdapter
```

### @trace Decorator
```python
@trace(provider="gemini", model="gemini-2.5-flash")
def my_function(prompt):
    adapter = GeminiAdapter()
    return adapter.generate(prompt)
```

### @expect Decorator
```python
@trace(provider="gemini")
@expect(
    must_include=["refund"],
    must_not_include=["sorry"],
    max_latency_ms=1500,
    min_tokens=10
)
def customer_support(query):
    return llm.generate(query)
```

### Execution Context (Phase 13)
```python
from sdk.context import execution

# Track multi-step workflows
with execution("my-agent-flow"):
    step1 = call_llm("First step")
    step2 = call_llm("Second step")  # Automatically linked
```

### Adapters

**GeminiAdapter**
```python
adapter = GeminiAdapter()  # uses GOOGLE_API_KEY env
response, trace = adapter.generate(
    prompt="Hello!",
    model="gemini-2.5-flash"
)
```

**OpenAIAdapter**
```python
adapter = OpenAIAdapter()  # uses OPENAI_API_KEY env
response, trace = adapter.chat_completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Expectation Engine

### Rules

| Rule | Severity | Description |
|------|----------|-------------|
| `must_include` | LOW | Substring must appear |
| `must_not_include` | HIGH | Substring must NOT appear |
| `max_latency_ms` | MEDIUM | Response time ceiling |
| `min_tokens` | LOW | Minimum response length |

### Verdict Model
```python
class Verdict:
    status: "pass" | "fail"
    severity: "low" | "medium" | "high" | None
    violations: list[str]
```

---

## Execution Graphs (Phase 14-25)

### Graph Features

| Phase | Feature | Description |
|-------|---------|-------------|
| 14 | Graph Construction | DAG from traces |
| 16 | Graph Verdict | Root cause detection |
| 18 | Performance Analysis | Critical path, bottlenecks |
| 19 | Semantic Nodes | Role labels (INPUT, LLM, VALIDATION...) |
| 20 | Hierarchical Stages | Collapsible groups |
| 21 | Time Visualization | Latency heatmap |
| 22 | Forensics Mode | Debug focus mode |
| 23 | Graph Diffs | Compare executions |
| 24 | Investigation Paths | Guided debugging |
| 25 | Enterprise | Integrity, snapshots, exports |

### Building Graphs
```python
from sdk.graph import ExecutionGraph

# Get graph for an execution
graph = ExecutionGraph.from_traces(traces)

# Analyze
verdict = graph.compute_verdict()
path = graph.investigation_path()
snapshot = graph.to_snapshot()
```

---

## Golden Traces

### Bless a Trace
```bash
sentinel bless <trace_id>
sentinel bless <trace_id> --yes    # Skip confirmation
sentinel bless <trace_id> --force  # Override existing
```

### How It Works
1. Output is hashed and stored
2. One golden per model/provider
3. `sentinel check` compares against golden
4. Hash mismatch → FAIL

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `sentinel init` | Initialize config |
| `sentinel server` | Start API server |
| `sentinel list` | List traces |
| `sentinel list --failed` | Failed only |
| `sentinel show <id>` | Show trace |
| `sentinel replay <id>` | Re-run trace |
| `sentinel bless <id>` | Mark golden |
| `sentinel check` | CI check (exits 1 on fail) |
| `sentinel graph-check <id>` | CI graph verdict check |

---

## API Reference

Base: `http://127.0.0.1:8000`

### Traces
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/traces` | List |
| GET | `/v1/traces/{id}` | Get |
| POST | `/v1/traces` | Create |
| DELETE | `/v1/traces/{id}` | Delete |

### Executions & Graphs (Phase 14+)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/executions` | List executions |
| GET | `/v1/executions/{id}` | Get execution traces |
| GET | `/v1/executions/{id}/graph` | Get DAG |
| GET | `/v1/executions/{id}/analysis` | Performance analysis |
| GET | `/v1/executions/{a}/diff/{b}` | Compare graphs |
| GET | `/v1/executions/{id}/investigate` | Debug guidance |
| GET | `/v1/executions/{id}/snapshot` | Immutable snapshot |
| GET | `/v1/executions/{id}/export` | Export artifact |
| GET | `/v1/executions/{id}/verify` | Verify integrity |

### Replay
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/replay/{id}` | Replay |
| GET | `/v1/replay/{id}/preview` | Preview |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/chat/completions` | OpenAI compat |
| GET | `/health` | Health check |

---

## Storage

```
~/.sentinel/
├── config.yaml
├── traces/
│   └── YYYY-MM-DD/
│       └── <trace_id>.json
└── sentinel.db  # SQLite index
```

---

## CI Integration

### GitHub Actions
```yaml
- run: python -m cli.main check
  env:
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

### Graph-Level CI
```yaml
- run: python -m cli.main graph-check ${{ env.EXECUTION_ID }}
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `SENTINEL_HOME` | Config directory (optional) |

---

## Trace Schema

```python
class Trace:
    trace_id: str           # UUID
    execution_id: str       # Execution context
    node_id: str            # Graph node ID
    parent_node_id: str     # Parent in DAG
    timestamp: str          # ISO-8601
    request: TraceRequest   # Input
    response: TraceResponse # Output
    runtime: TraceRuntime   # Environment
    verdict: Verdict | None # PASS/FAIL
    blessed: bool           # Golden?
    replay_of: str | None   # Parent ID
    metadata: dict | None   # Custom
```

---

## Failure-First UI

The UI opens in **failed-only mode** by default:

- ❌ Large failure banner with violations
- Prev/Next navigation between failures
- Inline diff for golden mismatches
- No distractions during damage control

### Graph Tab
- 📊 Execution DAG visualization
- 🔬 Forensics Mode toggle
- ⏱️ Time-scaled nodes
- Collapsible stages

---

## Links

- [README](README.md)
- [Development Guide](DEVELOPMENT.md)
- [GitHub](https://github.com/xXMohitXx/Sentinel)
