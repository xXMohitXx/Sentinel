# Sentinel - Local Development Guide

## Quick Start

### 1. Activate Virtual Environment

```powershell
# Windows
.\sentinel\Scripts\activate

# Linux/Mac
source sentinel/bin/activate
```

### 2. Start the Server

```powershell
python -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
```

**Or using the CLI:**
```powershell
python -m cli.main server --reload
```

### 3. Access the Application

| URL | Description |
|-----|-------------|
| [http://127.0.0.1:8000](http://127.0.0.1:8000) | API root |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger API docs |
| [http://127.0.0.1:8000/ui](http://127.0.0.1:8000/ui) | Trace Inspector UI |
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Health check |

---

## Testing the API

### Create a Test Trace

```powershell
# Using curl
curl -X POST http://127.0.0.1:8000/v1/traces -H "Content-Type: application/json" -d '{
  "request": {
    "provider": "openai",
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "parameters": {"temperature": 0.7, "max_tokens": 256}
  },
  "response": {
    "text": "Hello! How can I help you today?",
    "latency_ms": 150
  },
  "runtime": {
    "library": "openai",
    "version": "1.0.0"
  }
}'
```

### Using PowerShell

```powershell
$body = @{
    request = @{
        provider = "openai"
        model = "gpt-4"
        messages = @(@{role = "user"; content = "Hello!"})
        parameters = @{temperature = 0.7; max_tokens = 256}
    }
    response = @{
        text = "Hi there!"
        latency_ms = 100
    }
    runtime = @{
        library = "openai"
        version = "1.0.0"
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/traces" -Method Post -Body $body -ContentType "application/json"
```

### List Traces

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/traces"
```

---

## Running Tests

```powershell
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_schema.py -v

# Run with coverage
python -m pytest tests/ --cov=sdk --cov=server
```

---

## CLI Commands

```powershell
# Initialize Sentinel config
python -m cli.main init

# Start server
python -m cli.main server --port 8000 --reload

# List traces
python -m cli.main list

# Show a trace
python -m cli.main show <trace_id>

# Replay a trace
python -m cli.main replay <trace_id>
```

---

## Development Workflow

1. **Start server with auto-reload:**
   ```powershell
   python -m uvicorn server.main:app --reload
   ```

2. **Open UI in browser:**
   Navigate to http://127.0.0.1:8000/ui

3. **Create test traces via API docs:**
   Navigate to http://127.0.0.1:8000/docs

4. **Refresh UI to see new traces**

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Use `--port 8001` or kill the existing process |
| Module not found | Ensure virtual environment is activated |
| No traces showing | Create a trace via the API first |
