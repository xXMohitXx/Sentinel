# Sentinel 🛡️

**Local-first developer tool that records, reproduces, compares, and debugs LLM calls.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is Sentinel?

Sentinel turns LLM development from guesswork into **inspectable, replayable, enforceable engineering**.

| Sentinel IS | Sentinel is NOT |
|-------------|-----------------|
| A truth layer between code & LLMs | A model hosting platform |
| Git-like memory for prompts & outputs | An agent framework |
| A debugger for LLM behavior drift | A training system |
| A CI gate for LLM regressions | A cloud service |

---

## 🚀 Current Status: Phase 10/12 Complete

| Phase | Feature | Status |
|-------|---------|--------|
| 0-7 | MVP + Integration | ✅ Complete |
| 8 | Expectation Engine (Judgment) | ✅ Complete |
| 9 | Golden Traces (Baselines) | ✅ Complete |
| 10 | CI Integration (Enforcement) | ✅ Complete |
| 11 | Failure-First UI | 🔲 Pending |
| 12 | README & Positioning | 🔲 In Progress |

**Sentinel can now FAIL your CI pipeline when LLM outputs regress!**

---

## ✨ Features

### 📝 Trace Capture
```python
from sdk.decorator import trace, expect

@trace(provider="gemini")
@expect(must_include=["refund"], max_latency_ms=1500)
def customer_support(query):
    return llm.generate(query)
```

### ⚖️ Expectation Engine
- `must_include` - Required substrings
- `must_not_include` - Forbidden content
- `max_latency_ms` - Performance gates
- `min_tokens` - Minimum response length

### ⭐ Golden Traces
```bash
# Mark a trace as the expected baseline
sentinel bless <trace_id>
```

### 🔒 CI Integration
```bash
# Fails with exit code 1 if any golden trace regresses
sentinel check
```

---

## 📦 Quick Start

### Installation
```bash
git clone https://github.com/xXMohitXx/Sentinel.git
cd Sentinel
python -m venv sentinel
.\sentinel\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Initialize
```bash
python -m cli.main init
```

### Start Server
```bash
python -m cli.main server
# Open http://127.0.0.1:8000/ui
```

### Capture Your First Trace
```python
from sdk.adapters.gemini import GeminiAdapter

adapter = GeminiAdapter()
response, trace = adapter.generate(
    prompt="Hello, world!",
    model="gemini-2.5-flash"
)
print(f"Trace ID: {trace.trace_id}")
```

---

## 🛠️ CLI Commands

| Command | Description |
|---------|-------------|
| `sentinel init` | Initialize config |
| `sentinel server` | Start API server |
| `sentinel list` | List traces |
| `sentinel list --failed` | Show only failed traces |
| `sentinel show <id>` | Show trace details |
| `sentinel replay <id>` | Replay a trace |
| `sentinel bless <id>` | Mark as golden baseline |
| `sentinel check` | CI regression check |

---

## 📁 Project Structure

```
sentinel/
├── sdk/                 # Python SDK
│   ├── adapters/        # OpenAI, Gemini, Llama adapters
│   ├── expectations/    # Rule-based judgment system
│   └── schema.py        # Trace schema (source of truth)
├── server/              # FastAPI backend
│   ├── routes/          # API endpoints
│   └── storage/         # JSON + SQLite storage
├── cli/                 # Command-line interface
├── ui/                  # Web inspection UI
├── examples/            # Example scripts
└── tests/               # Unit tests
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Setting Up Development Environment
```bash
git clone https://github.com/xXMohitXx/Sentinel.git
cd Sentinel
python -m venv sentinel
.\sentinel\Scripts\activate
pip install -r requirements.txt
pip install pytest  # For testing
```

### Running Tests
```bash
pytest tests/ -v
```

### Contribution Guidelines

1. **Fork the repository** and create your branch from `main`
2. **Write tests** for any new functionality
3. **Follow the code style** - we use standard Python conventions
4. **Update documentation** if you change APIs
5. **Submit a pull request** with a clear description

### Areas for Contribution

| Area | Difficulty | Description |
|------|------------|-------------|
| 🐛 Bug Fixes | Easy | Fix issues in GitHub Issues |
| 📖 Documentation | Easy | Improve docs and examples |
| 🧪 Tests | Medium | Add test coverage |
| 🎨 UI Improvements | Medium | Enhance the inspection UI |
| 🔌 New Adapters | Medium | Add Anthropic, Cohere, etc. |
| ⚡ Performance | Hard | Optimize storage and queries |

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Documentation**: [DOCUMENTATION.md](DOCUMENTATION.md)
- **Development Guide**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **GitHub**: [github.com/xXMohitXx/Sentinel](https://github.com/xXMohitXx/Sentinel)
