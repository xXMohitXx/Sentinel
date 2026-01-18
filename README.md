# Sentinel prevents LLM regressions from reaching production.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Complete](https://img.shields.io/badge/status-complete-green.svg)](#)

---

## The Problem

LLM outputs change unexpectedly. Same prompt, different model version → different behavior.  
Without Sentinel, you discover this **in production**.

## The Solution

```python
from sdk.decorator import trace, expect

@trace(provider="gemini")
@expect(must_include=["refund"], max_latency_ms=1500)
def customer_reply(query):
    return llm.generate(query)
```

```bash
# Mark a known-good response as baseline
sentinel bless <trace_id>

# In CI: fail if output regresses
sentinel check  # exits 1 on failure
```

That's it. Your CI now blocks LLM regressions.

---

## Quick Start

```bash
git clone https://github.com/xXMohitXx/Sentinel.git
cd Sentinel
pip install -r requirements.txt
python -m cli.main server
```

Open http://127.0.0.1:8000/ui

---

## Features

| Feature | Description |
|---------|-------------|
| **Trace Capture** | Record every LLM call automatically |
| **Expectations** | Define PASS/FAIL rules (4 deterministic rules) |
| **Golden Traces** | Baseline comparisons with hash verification |
| **CI Integration** | `sentinel check` exits 1 on regression |
| **Failure-First UI** | See what broke in < 10 seconds |

---

## Commands

| Command | What it does |
|---------|--------------|
| `sentinel init` | Initialize config |
| `sentinel server` | Start API server |
| `sentinel list` | List traces |
| `sentinel list --failed` | Show only failed traces |
| `sentinel show <id>` | Show trace details |
| `sentinel replay <id>` | Re-run a trace |
| `sentinel bless <id>` | Mark as golden baseline |
| `sentinel check` | CI regression check |

---

## Expectations

```python
@expect(
    must_include=["word"],       # Required content
    must_not_include=["sorry"],  # Forbidden content
    max_latency_ms=2000,         # Performance gate
    min_tokens=10                # Minimum length
)
```

All rules are deterministic. No AI judgment. No ambiguity.

---

## CI Integration

```yaml
# .github/workflows/sentinel.yml
- run: python -m cli.main check
  env:
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

Pipeline fails if any golden trace regresses.

---

## When NOT to Use Sentinel

- You're experimenting casually
- You don't care about regressions
- You're building a prototype
- You don't have LLM calls in production

Sentinel is infrastructure, not a toy.

---

## Architecture

```
sentinel/
├── sdk/                  # Python SDK
│   ├── schema.py         # Trace schema
│   ├── decorator.py      # @trace, @expect
│   ├── expectations/     # 4 rules + evaluator
│   └── adapters/         # OpenAI, Gemini
├── server/               # FastAPI backend
├── cli/                  # Command-line interface
├── ui/                   # Failure-first web UI
└── tests/                # Unit tests
```

---

## Status: ✅ COMPLETE

All 12 phases implemented:

- ✅ SDK with OpenAI & Gemini adapters
- ✅ FastAPI server with REST API
- ✅ CLI with all commands
- ✅ Expectation Engine (4 deterministic rules)
- ✅ Golden Traces with hash comparison
- ✅ CI integration (`sentinel check`)
- ✅ Failure-First UI

---

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup and contribution guidelines.

---

## Links

- [Documentation](DOCUMENTATION.md)
- [Development Guide](DEVELOPMENT.md)
- [GitHub](https://github.com/xXMohitXx/Sentinel)

---

MIT License
