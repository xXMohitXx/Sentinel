# Development Guide

Complete guide for local development, testing, and contributing to Sentinel.

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
python -m cli.main graph-check <id>  # Graph CI check
```

---

## Testing

```bash
pytest tests/ -v                    # All tests
pytest tests/test_expectations.py   # Specific
pytest tests/ --cov=sdk             # Coverage

# Phase 19-25 tests
python examples/test_phases_19_25.py
```

---

## Project Structure

```
sentinel/
├── sdk/
│   ├── schema.py              # Trace schema
│   ├── decorator.py           # @trace, @expect
│   ├── capture.py             # Core capture
│   ├── context.py             # Execution context (Phase 13)
│   ├── graph.py               # Graph models (Phase 14-25)
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
│   └── app.js                 # Logic (Phase 19-25)
├── examples/
│   └── test_phases_19_25.py   # Comprehensive tests
└── tests/
```

---

## Key Design Decisions

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

### Execution Graphs (Phase 14+)
- DAG built from traces
- Causality via `parent_node_id`
- Semantic roles per node
- Hierarchical stages
- Immutable after construction

---

## Phase Overview

| Phase | Feature | Files |
|-------|---------|-------|
| 1-12 | Core SDK, Server, CLI, UI | `sdk/`, `server/`, `cli/`, `ui/` |
| 13 | Execution Context | `sdk/context.py` |
| 14 | Graph Construction | `sdk/graph.py` |
| 15 | Graph UI | `ui/app.js` |
| 16 | Graph Verdict | `sdk/graph.py` |
| 17 | Subgraph Replay | `server/routes/traces.py` |
| 18 | Performance Analysis | `sdk/graph.py` |
| 19 | Semantic Nodes | `sdk/graph.py`, `ui/app.js` |
| 20 | Hierarchical Stages | `sdk/graph.py`, `ui/app.js` |
| 21 | Time Visualization | `ui/app.js`, `ui/index.html` |
| 22 | Forensics Mode | `ui/app.js`, `ui/index.html` |
| 23 | Graph Diffs | `sdk/graph.py`, `server/routes/traces.py` |
| 24 | Investigation Paths | `sdk/graph.py`, `server/routes/traces.py` |
| 25 | Enterprise Hardening | `sdk/graph.py`, `server/routes/traces.py` |

---

## Contributing

### Workflow
1. Fork the repo
2. Create branch: `git checkout -b feature/my-feature`
3. Make changes + add tests
4. Run tests: `pytest tests/ -v`
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
| Graph features | Hard |

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

---

## API Testing (Phases 19-25)

```bash
# Graph endpoints
curl http://127.0.0.1:8000/v1/executions
curl http://127.0.0.1:8000/v1/executions/{id}/graph
curl http://127.0.0.1:8000/v1/executions/{id}/analysis
curl http://127.0.0.1:8000/v1/executions/{id}/investigate
curl http://127.0.0.1:8000/v1/executions/{id}/snapshot
curl http://127.0.0.1:8000/v1/executions/{id}/verify
curl http://127.0.0.1:8000/v1/executions/{a}/diff/{b}
```

---

## Status: ✅ COMPLETE (v0.5.0)

All 25 phases implemented. Ready for production.
