# Sentinel

> Developer-first local LLM tracing, replay & debugging system

**Sentinel** is a local-first developer tool that records, reproduces, compares, and debugs LLM calls across cloud and local models.

## What Sentinel Does

- **Captures** every LLM request and response with full context
- **Stores** traces locally as immutable, portable JSON files
- **Replays** historical calls with optional parameter overrides
- **Compares** outputs across models, prompts, and configurations
- **Exposes** an OpenAI-compatible API for drop-in integration

## Quick Start

### Installation

```bash
# Create and activate virtual environment
python -m venv sentinel
sentinel\Scripts\activate  # Windows
# source sentinel/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Usage

#### As a Decorator

```python
from sdk import trace

@trace
def my_llm_call(prompt: str):
    # Your LLM call here
    pass
```

#### Start the Server

```bash
sentinel server start
# or
uvicorn server.main:app --reload
```

#### API Endpoints

- `POST /v1/chat/completions` - OpenAI-compatible chat endpoint
- `GET /v1/traces` - List all traces
- `GET /v1/traces/{id}` - Get specific trace
- `POST /v1/replay/{id}` - Replay a trace

## Project Structure

```
sentinel/
├── sdk/           # Python SDK for capturing traces
├── server/        # FastAPI server
├── cli/           # Command-line interface
├── ui/            # Minimal inspection UI
└── tests/         # Test suite
```

```
sentinel_v0/
├── pyproject.toml      # Project metadata & dependencies
├── requirements.txt    # Python dependencies
├── config.yaml         # Default configuration
├── README.md           # Project documentation
├── sentinel/           # Virtual environment
├── sdk/                # Python SDK
│   ├── schema.py       # Trace schema (Pydantic models)
│   ├── capture.py      # Core capture layer
│   ├── decorator.py    # @trace decorator
│   └── adapters/       # OpenAI & llama.cpp adapters
├── server/             # FastAPI server
│   ├── main.py         # Application entry point
│   ├── routes/         # API endpoints
│   │   ├── traces.py   # Trace CRUD
│   │   ├── replay.py   # Replay engine
│   │   └── chat.py     # OpenAI-compatible endpoint
│   └── storage/        # Storage backends
│       ├── files.py    # JSON file storage
│       └── sqlite.py   # SQLite index
├── cli/                # Command-line interface
│   └── main.py         # CLI commands
├── ui/                 # Web UI
│   ├── index.html      # Trace inspector UI
│   └── app.js          # JavaScript logic
└── tests/              # Test suite
    └── test_schema.py  # Schema tests
```

## Technology Stack

- **Python 3.10+**
- **FastAPI** + **Uvicorn** for HTTP server
- **JSON files** + **SQLite** for storage
- **Pydantic** for schema validation

## License

MIT
