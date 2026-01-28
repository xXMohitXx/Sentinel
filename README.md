<p align="center">
  <img src="assets/logo/phylaxlogo.png" alt="Phylax Logo" width="200">
</p>

# Phylax prevents LLM regressions from reaching production.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![SDK: v1.0.0](https://img.shields.io/badge/SDK-v1.0.0-green.svg)](#)
[![Status: Stable](https://img.shields.io/badge/status-stable-brightgreen.svg)](#)

---

## The Problem

LLM outputs change unexpectedly. Same prompt, different model version → different behavior.  
Without Phylax, you discover this **in production**.

## The Solution

```python
from sdk.decorator import trace, expect
from sdk.context import execution

@trace(provider="gemini")
@expect(must_include=["refund"], max_latency_ms=1500)
def customer_reply(query):
    return llm.generate(query)

# Track multi-step agent flows
with execution("customer-support-flow"):
    result = customer_reply("I want a refund")
```

```bash
# Mark a known-good response as baseline
phylax bless <trace_id>

# In CI: fail if output regresses
phylax check  # exits 1 on failure
```

That's it. Your CI now blocks LLM regressions.

---

## Quick Start

```bash
git clone https://github.com/xXMohitXx/Phylax.git
cd Phylax
pip install -r requirements.txt
python -m cli.main server
```

Open http://127.0.0.1:8000/ui

**New to Phylax?** See [docs/quickstart.md](docs/quickstart.md) for a 10-minute guide.

---

## Features

| Feature | Description |
|---------|-------------|
| **Trace Capture** | Record every LLM call automatically |
| **Expectations** | Define PASS/FAIL rules (4 deterministic rules) |
| **Golden Traces** | Baseline comparisons with hash verification |
| **CI Integration** | `phylax check` exits 1 on regression |
| **Failure-First UI** | See what broke in < 10 seconds |
| **Execution Graphs** | Visualize multi-step agent workflows |
| **Forensics Mode** | Debug failures with guided investigation |
| **Enterprise Hardening** | Integrity hashing, snapshots, exports |

---

## Commands

| Command | What it does |
|---------|--------------|
| `phylax init` | Initialize config |
| `phylax server` | Start API server |
| `phylax list` | List traces |
| `phylax list --failed` | Show only failed traces |
| `phylax show <id>` | Show trace details |
| `phylax replay <id>` | Re-run a trace |
| `phylax bless <id>` | Mark as golden baseline |
| `phylax check` | CI regression check |

---

## Execution Graphs

Track multi-step LLM workflows with causality:

```python
from sdk.context import execution

with execution("my-agent"):
    step1 = call_llm("First step")
    step2 = call_llm("Second step")  # Tracks parent-child
```

**Graph Features:**
- 📊 DAG visualization with hierarchical stages
- 🔬 Forensics mode for debugging
- ⏱️ Time-scaled nodes by latency
- 🔍 Investigation paths with guided debugging
- 🔒 Enterprise: integrity hashing, snapshots, exports

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
# .github/workflows/phylax.yml
- run: python -m cli.main check
  env:
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

Pipeline fails if any golden trace regresses.

---

## Architecture

```
phylax/
├── sdk/                  # Python SDK (v1.0.0)
│   ├── schema.py         # Trace schema
│   ├── decorator.py      # @trace, @expect
│   ├── context.py        # Execution context
│   ├── graph.py          # Graph models
│   ├── expectations/     # 4 rules + evaluator
│   └── adapters/         # OpenAI, Gemini
├── server/               # FastAPI backend
├── cli/                  # Command-line interface
├── ui/                   # Failure-first web UI
├── docs/                 # v1.0 Documentation
└── tests/                # Unit tests
```

---

## v1.0 Documentation

| Document | Purpose |
|----------|---------|
| [docs/quickstart.md](docs/quickstart.md) | 10 min to CI failure |
| [docs/mental-model.md](docs/mental-model.md) | What Phylax is/isn't |
| [docs/graph-model.md](docs/graph-model.md) | How to read graphs |
| [docs/failure-playbook.md](docs/failure-playbook.md) | Debug procedures |
| [docs/contract.md](docs/contract.md) | API stability guarantees |
| [docs/invariants.md](docs/invariants.md) | Semantic invariants |

---

## Status: ✅ v1.0.0 STABLE

All 35 phases complete:

- ✅ SDK with OpenAI & Gemini adapters
- ✅ FastAPI server with 20+ endpoints
- ✅ CLI with all commands
- ✅ Expectation Engine (4 deterministic rules)
- ✅ Golden Traces with hash comparison
- ✅ CI integration (`phylax check`)
- ✅ Failure-First UI
- ✅ Execution Graphs & DAG visualization
- ✅ Semantic Nodes & Hierarchical Stages
- ✅ Forensics Mode & Investigation Paths
- ✅ Enterprise Hardening (integrity, export)
- ✅ API Contract Frozen
- ✅ Documentation Complete

---

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup and contribution guidelines.

---

## Links

- [Documentation](DOCUMENTATION.md)
- [Development Guide](DEVELOPMENT.md)
- [Changelog](CHANGELOG.md)
- [GitHub](https://github.com/xXMohitXx/Phylax)

---

MIT License
