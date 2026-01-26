# Sentinel Quickstart

> **Goal: From zero to CI failure in 10 minutes.**

---

## 1. Install (2 min)

```bash
git clone https://github.com/xXMohitXx/Sentinel.git
cd Sentinel
pip install -r requirements.txt
```

Set your API key:
```bash
# Windows PowerShell
$env:GOOGLE_API_KEY = "your-key"

# Linux/Mac
export GOOGLE_API_KEY="your-key"
```

---

## 2. Start Server (1 min)

```bash
python -m cli.main server
```

Open: http://127.0.0.1:8000/ui

---

## 3. Create Your First Trace (3 min)

Create `myapp.py`:

```python
from sdk.decorator import trace, expect
from sdk.adapters.gemini import GeminiAdapter

@trace(provider="gemini")
@expect(must_include=["hello"], max_latency_ms=2000)
def greet(name):
    adapter = GeminiAdapter()
    response, _ = adapter.generate(f"Say hello to {name}")
    return response

# Run it
result = greet("World")
print(result)
```

Run:
```bash
python myapp.py
```

Check UI — you should see your trace!

---

## 4. Bless a Golden (1 min)

Find your trace ID in the UI and mark it as the baseline:

```bash
python -m cli.main bless <trace_id> --yes
```

---

## 5. Run CI Check (1 min)

```bash
python -m cli.main check
```

- **Exit 0**: All goldens pass ✅
- **Exit 1**: Regression detected ❌

---

## 6. Add to CI (2 min)

```yaml
# .github/workflows/sentinel.yml
name: Sentinel Check
on: [push]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python -m cli.main check
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

---

## Done! You now have:

✅ LLM call tracing  
✅ Expectation evaluation (PASS/FAIL)  
✅ Golden baseline comparison  
✅ CI regression gate  

---

## Next Steps

- [Mental Model](mental-model.md) — What Sentinel is
- [Graph Model](graph-model.md) — Multi-step agents
- [Failure Playbook](failure-playbook.md) — Debug failures
