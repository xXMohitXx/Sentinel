# Sentinel Documentation

Complete technical documentation for the Sentinel LLM debugging platform.

---

## Table of Contents

1. [Overview](#overview)
2. [SDK Reference](#sdk-reference)
3. [Expectation Engine](#expectation-engine)
4. [Golden Traces](#golden-traces)
5. [CLI Reference](#cli-reference)
6. [API Reference](#api-reference)
7. [Storage](#storage)
8. [CI Integration](#ci-integration)

---

## Overview

Sentinel is a **local-first developer tool** that records, reproduces, compares, and debugs LLM calls.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Trace Capture** | Record every LLM call with full context |
| **Replay** | Re-execute traces with optional overrides |
| **Expectations** | Define PASS/FAIL rules for LLM outputs |
| **Golden Traces** | Baseline comparisons for regression detection |
| **CI Integration** | Fail builds when LLM outputs regress |

### Current Status

**Phase 10 of 12 Complete**

- ✅ SDK with OpenAI, Gemini, Llama adapters
- ✅ FastAPI server with REST API
- ✅ CLI with list, show, replay, bless, check commands
- ✅ Web UI with verdict display and filtering
- ✅ Expectation Engine (4 deterministic rules)
- ✅ Golden Traces with hash comparison
- ✅ CI integration with exit code signaling

---

## SDK Reference

### Installation

```python
# Import the SDK
from sdk import trace, expect, Trace, Verdict
from sdk.adapters.gemini import GeminiAdapter
from sdk.adapters.openai import OpenAIAdapter
```

### @trace Decorator

Automatically capture LLM calls:

```python
from sdk.decorator import trace

@trace(provider="gemini", model="gemini-2.5-flash")
def my_function(prompt):
    adapter = GeminiAdapter()
    return adapter.generate(prompt)
```

**Parameters:**
- `provider` (str): "openai" | "gemini" | "local"
- `model` (str, optional): Override model name

### @expect Decorator

Define expectations for automatic PASS/FAIL verdicts:

```python
from sdk.decorator import trace, expect

@trace(provider="gemini")
@expect(
    must_include=["refund"],
    must_not_include=["I'm sorry"],
    max_latency_ms=1500,
    min_tokens=10
)
def customer_support(query):
    return llm.generate(query)
```

### Adapters

#### GeminiAdapter
```python
from sdk.adapters.gemini import GeminiAdapter

adapter = GeminiAdapter(api_key="...")  # or use GOOGLE_API_KEY env
response, trace = adapter.generate(
    prompt="Hello!",
    model="gemini-2.5-flash",
    temperature=0.7,
    max_tokens=256
)
```

#### OpenAIAdapter
```python
from sdk.adapters.openai import OpenAIAdapter

adapter = OpenAIAdapter(api_key="...")  # or use OPENAI_API_KEY env
response, trace = adapter.chat_completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7
)
```

### Trace Schema

```python
class Trace:
    trace_id: str           # UUID
    timestamp: str          # ISO-8601 local time
    request: TraceRequest   # Input data
    response: TraceResponse # Output data
    runtime: TraceRuntime   # Environment info
    verdict: Verdict | None # PASS/FAIL (if expectations set)
    blessed: bool           # Is this a golden trace?
    replay_of: str | None   # Parent trace ID if replayed
    metadata: dict | None   # Custom metadata
```

---

## Expectation Engine

Phase 8 introduced deterministic rules for automatic PASS/FAIL verdicts.

### Rules

| Rule | Severity | Description |
|------|----------|-------------|
| `must_include` | LOW | Substring(s) must appear in response |
| `must_not_include` | HIGH | Substring(s) must NOT appear |
| `max_latency_ms` | MEDIUM | Response time ceiling |
| `min_tokens` | LOW | Minimum response length |

### Verdict Model

```python
class Verdict:
    status: "pass" | "fail"
    severity: "low" | "medium" | "high" | None
    violations: list[str]  # Human-readable violation messages
```

### Design Rules

1. **Computed at trace creation** - Never deferred
2. **Immutable once written** - Traces are audit artifacts
3. **Deterministic only** - No AI-based judgment
4. **All violations reported** - No short-circuiting

### Programmatic Usage

```python
from sdk.expectations import evaluate

verdict = evaluate(
    response_text="Paris is the capital of France",
    latency_ms=1200,
    must_include=["paris"],
    max_latency_ms=2000
)

print(verdict.status)  # "pass"
```

---

## Golden Traces

Phase 9 introduced baseline traces for regression detection.

### Blessing a Trace

```bash
# Interactive (with confirmation)
sentinel bless <trace_id>

# Skip confirmation
sentinel bless <trace_id> --yes

# Override existing golden for same model
sentinel bless <trace_id> --force
```

### How It Works

1. When blessed, the trace's output is **hashed** and stored
2. Only **one golden trace per model/provider** is allowed
3. During `sentinel check`, outputs are compared against golden hashes
4. If hash differs → **FAIL**

### Storage

Golden traces have:
```json
{
  "blessed": true,
  "metadata": {
    "output_hash": "sha256_prefix_16_chars",
    "blessed_at": "2026-01-17T16:00:00"
  }
}
```

---

## CLI Reference

### sentinel init
Initialize Sentinel configuration.

```bash
sentinel init
sentinel init --force  # Overwrite existing
```

### sentinel server
Start the API server.

```bash
sentinel server
sentinel server --port 8080
sentinel server --reload  # Auto-reload on changes
```

### sentinel list
List traces.

```bash
sentinel list
sentinel list -n 10        # Limit to 10
sentinel list --failed     # Failed traces only
sentinel list --model gpt-4
```

### sentinel show
Show trace details.

```bash
sentinel show <trace_id>
sentinel show <trace_id> --json
```

### sentinel replay
Replay a trace.

```bash
sentinel replay <trace_id>
sentinel replay <trace_id> --model gpt-4o  # Override model
sentinel replay <trace_id> --dry-run       # Preview only
```

### sentinel bless
Mark a trace as golden baseline.

```bash
sentinel bless <trace_id>
sentinel bless <trace_id> --yes    # Skip confirmation
sentinel bless <trace_id> --force  # Override existing
```

### sentinel check
**CI-safe command.** Replays all golden traces and exits:
- `0` - All pass
- `1` - Any failure

```bash
sentinel check
sentinel check --json  # Output JSON report
```

---

## API Reference

Base URL: `http://127.0.0.1:8000`

### Traces

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/traces` | List traces |
| GET | `/v1/traces/{id}` | Get trace |
| POST | `/v1/traces` | Create trace |
| DELETE | `/v1/traces/{id}` | Delete trace |
| GET | `/v1/traces/{id}/lineage` | Get replay chain |

### Replay

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/replay/{id}` | Replay trace |
| GET | `/v1/replay/{id}/preview` | Preview replay |

### Chat (OpenAI-compatible)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/chat/completions` | OpenAI-compatible chat |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

---

## Storage

### File Structure

```
~/.sentinel/
├── config.yaml          # Configuration
├── traces/              # Trace storage
│   └── YYYY-MM-DD/      # Date-organized
│       └── <id>.json    # Individual traces
└── sentinel.db          # SQLite index (optional)
```

### Trace Files

Each trace is a JSON file:
```json
{
  "trace_id": "uuid",
  "timestamp": "2026-01-17T16:00:00",
  "request": { ... },
  "response": { ... },
  "runtime": { ... },
  "verdict": { "status": "pass", ... },
  "blessed": false
}
```

---

## CI Integration

### GitHub Actions

```yaml
name: Sentinel Check

on: [push, pull_request]

jobs:
  sentinel:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python -m cli.main check --json
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

### Pytest Integration

```python
import subprocess
import sys

def test_sentinel_check():
    result = subprocess.run(
        [sys.executable, "-m", "cli.main", "check"],
        capture_output=True
    )
    assert result.returncode == 0, "Golden trace regression!"
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `SENTINEL_HOME` | Override config directory |

---

## Contributing

See [README.md](README.md#-contributing) for contribution guidelines.
