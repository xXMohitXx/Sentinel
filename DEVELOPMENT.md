# Development Guide

This guide covers local development setup, testing, and debugging for Sentinel.

---

## 🚀 Quick Setup

### Prerequisites
- Python 3.10+
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/xXMohitXx/Sentinel.git
cd Sentinel

# Create virtual environment
python -m venv sentinel
.\sentinel\Scripts\activate  # Windows
# source sentinel/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
```powershell
# Required for Gemini
$env:GOOGLE_API_KEY = "your-gemini-api-key"

# Required for OpenAI
$env:OPENAI_API_KEY = "your-openai-api-key"
```

---

## 🏃 Running the Application

### Start the Server
```bash
python -m cli.main server
# or with auto-reload:
python -m uvicorn server.main:app --reload
```

**Endpoints:**
- UI: http://127.0.0.1:8000/ui
- API Docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

### CLI Commands
```bash
python -m cli.main init           # Initialize config
python -m cli.main list           # List traces
python -m cli.main list --failed  # Failed traces only
python -m cli.main show <id>      # Show trace details
python -m cli.main replay <id>    # Replay trace
python -m cli.main bless <id>     # Mark as golden
python -m cli.main check          # CI regression test
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_schema.py -v
pytest tests/test_expectations.py -v
```

### Run with Coverage
```bash
pip install pytest-cov
pytest tests/ --cov=sdk --cov=server --cov-report=html
```

---

## 📁 Project Architecture

```
sentinel/
├── sdk/                      # Python SDK
│   ├── __init__.py           # Public exports
│   ├── schema.py             # Trace schema (Pydantic)
│   ├── capture.py            # Core capture logic
│   ├── decorator.py          # @trace and @expect decorators
│   ├── adapters/             # LLM Provider Adapters
│   │   ├── openai.py         # OpenAI adapter
│   │   ├── gemini.py         # Google Gemini adapter
│   │   └── llama.py          # Llama.cpp adapter (stub)
│   └── expectations/         # Expectation Engine (Phase 8)
│       ├── rules.py          # 4 deterministic rules
│       └── evaluator.py      # Verdict evaluation
│
├── server/                   # FastAPI Backend
│   ├── main.py               # App entry point
│   ├── routes/
│   │   ├── traces.py         # CRUD endpoints
│   │   ├── replay.py         # Replay engine
│   │   └── chat.py           # OpenAI-compatible endpoint
│   └── storage/
│       ├── files.py          # JSON file storage
│       └── sqlite.py         # SQLite index
│
├── cli/                      # Command Line Interface
│   └── main.py               # All commands
│
├── ui/                       # Web UI
│   ├── index.html            # Main page
│   └── app.js                # JavaScript logic
│
├── examples/                 # Example Scripts
│   ├── test_gemini_call.py   # Basic Gemini usage
│   ├── test_expectations.py  # Expectation engine demo
│   └── ci/                   # CI integration examples
│
└── tests/                    # Unit Tests
    ├── test_schema.py
    └── test_expectations.py
```

---

## 🔧 Key Design Decisions

### Trace Schema (`sdk/schema.py`)
- **Single source of truth** for all trace data
- Pydantic models for validation
- JSON-serializable for storage

### Verdict Immutability
- Verdicts computed at trace creation time
- **Never recalculated** after storage
- Ensures traces are audit artifacts

### Storage Strategy
- **JSON files** as source of truth (`~/.sentinel/traces/`)
- SQLite index for fast queries
- Date-organized directories

### Expectation Rules
All rules are **deterministic** (no AI judgment):
- `must_include` - Substring presence
- `must_not_include` - Substring absence
- `max_latency_ms` - Performance threshold
- `min_tokens` - Minimum length

---

## 🐛 Debugging

### View Trace Files
```bash
# Traces stored in:
~/.sentinel/traces/YYYY-MM-DD/<trace_id>.json
```

### Common Issues

| Issue | Solution |
|-------|----------|
| API key not found | Set `GOOGLE_API_KEY` or `OPENAI_API_KEY` |
| Traces not showing | Ensure server is running, refresh UI |
| Hourglass (⏳) verdict | Trace has no `@expect` decorator |
| Import errors | Run from project root, activate venv |

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📊 Current Development Status

**Phase 10 of 12 Complete**

| Phase | Feature | Status |
|-------|---------|--------|
| 0-7 | MVP (SDK, Server, CLI, UI) | ✅ |
| 8 | Expectation Engine | ✅ |
| 9 | Golden Traces | ✅ |
| 10 | CI Integration | ✅ |
| 11 | Failure-First UI | 🔲 |
| 12 | Final Polish | 🔲 |

---

## 🤝 Contributing

See [README.md](README.md#-contributing) for contribution guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run tests: `pytest tests/ -v`
5. Commit: `git commit -m "feat: add my feature"`
6. Push and create a Pull Request

### Commit Message Format
```
feat: add new feature
fix: resolve bug
docs: update documentation
refactor: improve code structure
test: add tests
```
