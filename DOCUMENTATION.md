# Sentinel - Project Documentation

> **Developer-First Local LLM Tracing, Replay & Debugging System**
> 
> Current Version: **v0.1.0** | Status: **MVP Complete**

---

## 📊 Development Stage

Based on the original roadmap, we are at **~Phase 5-6 Complete**:

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Design Lock | ✅ Complete |
| Phase 1 | SDK Core | ✅ Complete |
| Phase 2 | Runtime Adapters | ✅ Complete (OpenAI + Gemini) |
| Phase 3 | FastAPI Server | ✅ Complete |
| Phase 4 | Replay Engine | ✅ Complete |
| Phase 5 | CLI | ✅ Complete |
| Phase 6 | UI | ✅ Complete |
| Phase 7 | Integration & Polish | 🔄 In Progress |

---

## 🎯 Current Capabilities

### ✅ SDK (Python Package)

**Trace Capture Layer**
- Function decorator `@trace` for automatic tracing
- Context manager for manual control
- Explicit `CaptureLayer` class for full control

**Adapters (LLM Providers)**
| Provider | Status | Models Tested |
|----------|--------|---------------|
| OpenAI | ✅ Full Support | GPT-4, GPT-4o-mini |
| Google Gemini | ✅ Full Support | Gemini 2.5 Flash |
| Llama.cpp | 🔧 Stub Ready | - |

**Trace Schema**
- Immutable, JSON-serializable traces
- Full request/response capture
- Token usage tracking
- Latency measurement
- Replay lineage tracking

---

### ✅ Server (FastAPI)

**API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/traces` | GET | List all traces with filtering |
| `/v1/traces/{id}` | GET | Get specific trace details |
| `/v1/traces` | POST | Create a new trace |
| `/v1/traces/{id}` | DELETE | Delete a trace |
| `/v1/traces/{id}/lineage` | GET | Get replay lineage chain |
| `/v1/replay/{id}` | POST | Replay a trace |
| `/v1/replay/{id}/preview` | GET | Preview replay without executing |
| `/v1/chat/completions` | POST | OpenAI-compatible endpoint |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger API documentation |

**Storage**
- JSON file-based storage (primary)
- Organized by date (`~/.sentinel/traces/YYYY-MM-DD/`)
- SQLite index (optional, for fast queries)

---

### ✅ CLI (Command Line Interface)

```bash
sentinel init          # Initialize configuration
sentinel server        # Start the server
sentinel list          # List recent traces
sentinel show <id>     # Show trace details
sentinel replay <id>   # Replay a trace
```

---

### ✅ Web UI (Trace Inspector)

- **Trace List**: View all captured traces with metadata
- **Detail View**: Full request/response inspection
- **Replay Button**: Re-execute traces with one click
- **Real-time Updates**: Refresh to see new traces
- **Dark Theme**: Modern, developer-friendly design

Access at: `http://127.0.0.1:8000/ui`

---

## 🏗️ Architecture

```
┌──────────────────────────┐
│     Application Code      │
│  (Your Python/LangChain)  │
└────────────▲─────────────┘
             │ @trace decorator
┌────────────┴─────────────┐
│   SDK Capture Layer       │  ← Intercepts LLM calls
│   - OpenAI Adapter        │
│   - Gemini Adapter        │
└────────────▲─────────────┘
             │ HTTP / SDK
┌────────────┴─────────────┐
│   FastAPI Server          │  ← Stores & serves traces
│   - REST API              │
│   - Replay Engine         │
│   - File Storage          │
└────────────▲─────────────┘
             │
┌────────────┴─────────────┐
│   Web UI                  │  ← Visual inspection
└──────────────────────────┘
```

---

## 📁 Project Structure

```
sentinel_v0/
├── sdk/                    # Python SDK
│   ├── schema.py           # Trace schema (Pydantic)
│   ├── capture.py          # Core capture layer
│   ├── decorator.py        # @trace decorator
│   └── adapters/           # Provider adapters
│       ├── openai.py       # OpenAI integration
│       ├── gemini.py       # Google Gemini integration
│       └── llama.py        # Llama.cpp stub
├── server/                 # FastAPI backend
│   ├── main.py             # App entry point
│   ├── routes/             # API endpoints
│   │   ├── traces.py       # CRUD operations
│   │   ├── replay.py       # Replay engine
│   │   └── chat.py         # OpenAI-compatible
│   └── storage/            # Persistence
│       ├── files.py        # JSON storage
│       └── sqlite.py       # SQLite index
├── cli/                    # Command line
│   └── main.py             # CLI commands
├── ui/                     # Web interface
│   ├── index.html          # Trace inspector
│   └── app.js              # UI logic
├── examples/               # Example scripts
│   ├── test_openai_call.py
│   └── test_gemini_call.py
└── tests/                  # Test suite
    └── test_schema.py
```

---

## 🚀 Quick Start

```bash
# 1. Activate environment
.\sentinel\Scripts\activate

# 2. Set API keys
$env:GOOGLE_API_KEY = "your-key"
$env:OPENAI_API_KEY = "your-key"  # Optional

# 3. Start server
python -m uvicorn server.main:app --reload

# 4. Open UI
# http://127.0.0.1:8000/ui

# 5. Run a test
python examples\test_gemini_call.py
```

---

## 🔮 What's Next (Phase 7+)

| Feature | Priority | Status |
|---------|----------|--------|
| LangChain integration example | High | Planned |
| Diff view for replay comparison | Medium | Planned |
| Export traces to JSON/CSV | Medium | Planned |
| Streaming response support | Medium | Planned |
| More adapters (Anthropic, Cohere) | Low | Planned |
| PyPI package publishing | High | Planned |

---

## 📝 Key Design Decisions

1. **Local-First**: All data stays on your machine
2. **Zero Infrastructure**: JSON + SQLite, no external services
3. **Provider Agnostic**: Works with any LLM via adapters
4. **Immutable Traces**: Once created, traces never change
5. **Replay Lineage**: Track the history of replayed traces
6. **OpenAI Compatible**: Drop-in replacement for OpenAI base URL

---

## 🤝 Usage Example

```python
from sdk.adapters.gemini import GeminiAdapter

# Create adapter (auto-traces all calls)
adapter = GeminiAdapter(api_key="your-key")

# Make a call - automatically captured!
response, trace = adapter.chat_completion(
    model="gemini-2.5-flash",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(f"Response: {response.text}")
print(f"Trace ID: {trace.trace_id}")
print(f"Latency: {trace.response.latency_ms}ms")
```

---

*Last Updated: 2026-01-17*
