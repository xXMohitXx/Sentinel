# Sentinel Documentation

Complete technical reference for Sentinel — the LLM regression prevention tool.

---

## Overview

Sentinel prevents LLM regressions from reaching production by:
1. **Recording** every LLM call
2. **Evaluating** expectations (PASS/FAIL)
3. **Comparing** against golden baselines
4. **Failing CI** when outputs regress

### Status: ✅ COMPLETE

All features implemented and ready for production use.

---

## SDK Reference

### Installation
```python
from sdk.decorator import trace, expect
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

### Programmatic Usage
```python
from sdk.expectations import evaluate

verdict = evaluate(
    response_text="Paris is the capital",
    latency_ms=1200,
    must_include=["paris"],
    max_latency_ms=2000
)
print(verdict.status)  # "pass"
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

### Pytest
```python
import subprocess
import sys

def test_sentinel():
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "check"],
        capture_output=True
    )
    assert result.returncode == 0
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

---

## Links

- [README](README.md)
- [Development Guide](DEVELOPMENT.md)
- [GitHub](https://github.com/xXMohitXx/Sentinel)
