# Phylax Mental Model

> **What Phylax is — and isn't.**

---

## The One-Liner

**Phylax is a regression gate for LLM outputs.**

It answers one question:  
*"Did my LLM behavior change from what I expected?"*

---

## What Phylax IS

### 1. An Observer
Phylax watches your LLM calls and records them. It never modifies what your code does.

### 2. A Judge (with simple rules)
Phylax evaluates responses with explicit, deterministic rules:
- Does output contain "X"?
- Is latency under Y ms?
- Is response at least Z tokens?

No AI. No fuzzy matching. Just yes/no.

### 3. A Regression Gate
Phylax compares current outputs to "golden" (blessed) baselines:
- Same = pass
- Different = fail

Your CI blocks the change.

### 4. A Debugger
When failures happen, Phylax shows:
- What failed
- Where in the execution chain
- What the expected vs actual output was

---

## What Phylax is NOT

### ❌ Not an LLM Evaluator
Phylax doesn't judge if your output is "good". It judges if it matches expectations.

### ❌ Not a Prompt Engineering Tool
Phylax doesn't help you write prompts. It tells you when prompts break.

### ❌ Not a Monitoring Dashboard
Phylax is for CI, not production monitoring. Use observability tools for that.

### ❌ Not AI-Powered
Phylax uses zero AI to evaluate. Rules are code, not inference.

---

## The Phylax Lifecycle

```
1. TRACE      → Record LLM call
2. EVALUATE   → Apply expectations (PASS/FAIL)
3. BLESS      → Mark good outputs as golden
4. CHECK      → Compare new outputs to golden
5. FAIL CI    → Block regressions
```

---

## Key Mental Shifts

### "I don't test LLM outputs, they're non-deterministic"
**Shift**: You don't test exactness. You test expectations.
- Does it mention the product? ✅
- Is it under 2 seconds? ✅
- Does it avoid apologies? ✅

### "CI can't catch LLM changes"
**Shift**: It can if you bless baselines.
- Run suite → get outputs
- Bless ones you like → they become golden
- Future runs compare against golden

### "Graphs are for visualization"
**Shift**: Graphs are for debugging.
- Multi-step agents create causality chains
- Failures propagate through the graph
- Root cause analysis is automatic

---

## When to Use Phylax

| Scenario | Use Phylax? |
|----------|---------------|
| Production LLM app | ✅ Yes |
| CI/CD pipeline | ✅ Yes |
| Multi-step agent | ✅ Yes |
| Casual experimentation | ❌ Overkill |
| Prompt iteration | ❌ Too early |
| Real-time monitoring | ❌ Wrong tool |

---

## The Trust Contract

Phylax makes these promises (see [contract.md](contract.md)):

1. **Traces are immutable** — Never modified after creation
2. **Verdicts are deterministic** — Same input = same result
3. **CI exit codes are reliable** — 0 = pass, 1 = fail
4. **No AI judgment** — Only explicit rules

If you can't trust your testing tool, it's worthless.

---

## Summary

```
Phylax = Trace + Expect + Bless + Check

Trace   → Record everything
Expect  → Define PASS/FAIL rules
Bless   → Lock known-good outputs
Check   → Block regressions in CI
```

That's the entire mental model.
