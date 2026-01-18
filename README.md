# Sentinel prevents LLM regressions from reaching production.

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

## Commands

| Command | What it does |
|---------|--------------|
| `sentinel bless <id>` | Mark trace as golden baseline |
| `sentinel check` | Replay all golden traces, exit 1 on failure |
| `sentinel list --failed` | Show only failed traces |
| `sentinel replay <id>` | Re-run a trace |

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

## Status

**Phase 11 of 12 Complete**

- ✅ Trace capture (OpenAI, Gemini)
- ✅ Expectation engine (4 rules)
- ✅ Golden traces + hash comparison
- ✅ CI integration (`sentinel check`)
- ✅ Failure-first UI

---

## Links

- [Documentation](DOCUMENTATION.md)
- [Development Guide](DEVELOPMENT.md)
- [GitHub](https://github.com/xXMohitXx/Sentinel)

---

MIT License
