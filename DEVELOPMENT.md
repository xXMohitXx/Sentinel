# Development Guide

Complete guide for local development, testing, and contributing to Sentinel v1.0.

---

## Quick Setup

```bash
# Clone
git clone https://github.com/xXMohitXx/Sentinel.git
cd Sentinel

# Virtual environment
python -m venv sentinel
.\sentinel\Scripts\activate  # Windows
# source sentinel/bin/activate  # Linux/Mac

# Install
pip install -r requirements.txt
```

## Environment Variables

```powershell
$env:GOOGLE_API_KEY = "your-gemini-key"
$env:OPENAI_API_KEY = "your-openai-key"  # optional
```

---

## Running

### Start Server
```bash
python -m cli.main server
# UI: http://127.0.0.1:8000/ui
# API: http://127.0.0.1:8000/docs
```

### CLI Commands
```bash
python -m cli.main init           # Initialize
python -m cli.main list           # List traces
python -m cli.main list --failed  # Failed only
python -m cli.main show <id>      # Show trace
python -m cli.main replay <id>    # Replay
python -m cli.main bless <id>     # Mark golden
python -m cli.main check          # CI check
```

---

## Testing

```bash
# Contract and invariant tests
python tests/test_contract.py

# Phase 19-25 tests
python examples/test_phases_19_25.py

# All examples
python examples/test_graph_features.py
```

---

## Project Structure

```
sentinel/
├── sdk/
│   ├── __init__.py            # Version (1.0.0)
│   ├── schema.py              # Trace schema
│   ├── decorator.py           # @trace, @expect
│   ├── capture.py             # Core capture
│   ├── context.py             # Execution context
│   ├── graph.py               # Graph models
│   ├── expectations/
│   │   ├── rules.py           # 4 rules
│   │   └── evaluator.py       # Verdict logic
│   └── adapters/
│       ├── openai.py
│       └── gemini.py
├── server/
│   ├── main.py                # FastAPI app
│   ├── routes/
│   │   ├── traces.py          # CRUD + Graph endpoints
│   │   ├── replay.py          # Replay engine
│   │   └── chat.py            # OpenAI compat
│   └── storage/
│       ├── files.py           # JSON storage
│       └── sqlite.py          # Index
├── cli/
│   └── main.py                # All commands
├── ui/
│   ├── index.html             # Failure-first UI
│   └── app.js                 # Frontend logic
├── docs/                      # v1.0 Documentation
│   ├── contract.md            # API guarantees
│   ├── invariants.md          # Semantic invariants
│   ├── failure-modes.md       # Error behavior
│   ├── quickstart.md          # Getting started
│   ├── mental-model.md        # Conceptual guide
│   ├── graph-model.md         # Graph visualization
│   ├── failure-playbook.md    # Debug procedures
│   ├── versioning.md          # Release policy
│   └── performance.md         # Scale limits
├── tests/
│   └── test_contract.py       # Contract enforcement
└── examples/
    └── test_phases_19_25.py   # Comprehensive tests
```

---

## Key Design Decisions

### API Contract (v1.0)
- Guaranteed APIs in [docs/contract.md](docs/contract.md)
- 10 semantic invariants in [docs/invariants.md](docs/invariants.md)
- Breaking changes require major version bump

### Verdict Immutability
- Verdicts computed at trace creation
- Never recalculated after storage
- Traces are audit artifacts

### Storage
- JSON files as source of truth (`~/.sentinel/traces/`)
- SQLite index for queries
- Date-organized directories

### Expectations
All deterministic (no AI):
- `must_include` — substring present
- `must_not_include` — substring absent
- `max_latency_ms` — performance
- `min_tokens` — minimum length

---

## Contributing

### Workflow
1. Fork the repo
2. Create branch: `git checkout -b feature/my-feature`
3. Make changes + add tests
4. Run tests: `python tests/test_contract.py`
5. Commit: `git commit -m "feat: add feature"`
6. Push and create PR

### Commit Format
```
feat: new feature
fix: bug fix
docs: documentation
refactor: code improvement
test: add tests
```

### Areas for Contribution
| Area | Difficulty |
|------|------------|
| Bug fixes | Easy |
| Documentation | Easy |
| Tests | Medium |
| UI improvements | Medium |
| New adapters | Medium |

---

## Debugging

### Trace Files
```
~/.sentinel/traces/YYYY-MM-DD/<trace_id>.json
```

### Common Issues
| Issue | Solution |
|-------|----------|
| API key not found | Set environment variable |
| Traces not showing | Restart server, refresh UI |
| ⏳ verdict | No `@expect` decorator |
| Graph empty | Use `execution()` context |
| UI cached | Hard refresh (Ctrl+Shift+R) |

---

## API Testing

```bash
# Health check
curl http://127.0.0.1:8000/health

# List traces
curl http://127.0.0.1:8000/v1/traces

# Get execution graph
curl http://127.0.0.1:8000/v1/executions/{id}/graph

# Get investigation path
curl http://127.0.0.1:8000/v1/executions/{id}/investigate

# Create snapshot
curl http://127.0.0.1:8000/v1/executions/{id}/snapshot
```

---

## Release Process

1. Update `sdk/__init__.py` version
2. Update CHANGELOG.md
3. Run all tests
4. Commit and tag: `git tag -a v1.0.x -m "Release"`
5. Push: `git push --tags`

See [docs/versioning.md](docs/versioning.md) for full policy.

---

## Status: ✅ v1.0.0 STABLE

All 35 phases complete. Ready for production.
