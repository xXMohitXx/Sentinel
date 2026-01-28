# Phylax Documentation

Complete technical reference for Phylax v1.0 — the LLM regression prevention tool.

---

## Overview

Phylax prevents LLM regressions from reaching production by:
1. **Recording** every LLM call
2. **Evaluating** expectations (PASS/FAIL)
3. **Comparing** against golden baselines
4. **Visualizing** execution graphs
5. **Failing CI** when outputs regress

### Status: ✅ v1.0.0 STABLE

All features implemented. API contract frozen. Ready for production.

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [docs/quickstart.md](docs/quickstart.md) | 10 min to CI failure |
| [docs/mental-model.md](docs/mental-model.md) | What Phylax is/isn't |
| [docs/graph-model.md](docs/graph-model.md) | How to read graphs |
| [docs/failure-playbook.md](docs/failure-playbook.md) | Debug procedures |
| [docs/contract.md](docs/contract.md) | API stability guarantees |
| [docs/invariants.md](docs/invariants.md) | Semantic invariants |
| [docs/failure-modes.md](docs/failure-modes.md) | Error behavior |
| [docs/versioning.md](docs/versioning.md) | Release policy |
| [docs/performance.md](docs/performance.md) | Scale limits |

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

### Execution Context
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
    status: "pass" | "fail"  # Only two values, ever
    severity: "low" | "medium" | "high" | None
    violations: list[str]
```

---

## Execution Graphs

### Graph Features

| Feature | Description |
|---------|-------------|
| DAG Visualization | Nodes and edges with hierarchical stages |
| Semantic Nodes | Role labels (INPUT, LLM, VALIDATION...) |
| Time Visualization | Latency heatmap, bottleneck badges |
| Forensics Mode | Debug focus, root cause highlighting |
| Graph Diffs | Compare two executions |
| Investigation Paths | Guided debugging steps |
| Enterprise | Integrity hashing, snapshots, exports |

### Building Graphs
```python
from sdk.graph import ExecutionGraph

graph = ExecutionGraph.from_traces(traces)
verdict = graph.compute_verdict()
path = graph.investigation_path()
snapshot = graph.to_snapshot()
```

---

## Golden Traces

### Bless a Trace
```bash
Phylax bless <trace_id>
Phylax bless <trace_id> --yes    # Skip confirmation
Phylax bless <trace_id> --force  # Override existing
```

### How It Works
1. Output is hashed and stored
2. One golden per model/provider
3. `Phylax check` compares against golden
4. Hash mismatch → FAIL

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `Phylax init` | Initialize config |
| `Phylax server` | Start API server |
| `Phylax list` | List traces |
| `Phylax list --failed` | Failed only |
| `Phylax show <id>` | Show trace |
| `Phylax replay <id>` | Re-run trace |
| `Phylax bless <id>` | Mark golden |
| `Phylax check` | CI check (exits 1 on fail) |

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

### Executions & Graphs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/executions` | List executions |
| GET | `/v1/executions/{id}` | Get traces |
| GET | `/v1/executions/{id}/graph` | Get DAG |
| GET | `/v1/executions/{id}/analysis` | Performance |
| GET | `/v1/executions/{a}/diff/{b}` | Compare |
| GET | `/v1/executions/{id}/investigate` | Debug path |
| GET | `/v1/executions/{id}/snapshot` | Immutable copy |
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
~/.Phylax/
├── config.yaml
├── traces/
│   └── YYYY-MM-DD/
│       └── <trace_id>.json
└── Phylax.db  # SQLite index
```

---

## CI Integration

### GitHub Actions
```yaml
- run: python -m cli.main check
  env:
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `Phylax_HOME` | Config directory (optional) |

---

## Trace Schema

```python
class Trace:
    trace_id: str           # UUID, immutable
    execution_id: str       # Links to execution
    node_id: str            # Graph node ID
    parent_node_id: str     # Parent in DAG
    timestamp: str          # ISO-8601
    request: TraceRequest   # Input
    response: TraceResponse # Output
    verdict: Verdict | None # PASS/FAIL
    blessed: bool           # Golden?
```

---

## Links

- [README](README.md)
- [Development Guide](DEVELOPMENT.md)
- [Changelog](CHANGELOG.md)
- [GitHub](https://github.com/xXMohitXx/Phylax)
