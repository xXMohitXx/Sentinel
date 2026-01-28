# Phylax Failure Playbook

> **How to debug failures — fast.**

---

## 1. Trace Failed

### Symptom
UI shows ❌ for a trace, verdict is "fail".

### Debug Steps

1. **Open trace details** — Click the trace in the list

2. **Check violations** — Look at the failure banner
   ```
   ❌ FAIL: must_include['refund'] not found
   ```

3. **Review response** — Expand "Response" section
   - Is the output what you expected?
   - Is it empty or truncated?

4. **Check expectations** — Look at what rules you set
   - Is `must_include` reasonable?
   - Is `max_latency_ms` too strict?

5. **Compare latency** — Check if timeout or slow

### Common Fixes

| Issue | Fix |
|-------|-----|
| Wrong output | Fix prompt |
| Latency too high | Increase `max_latency_ms` |
| Missing keyword | Update `must_include` or fix prompt |
| Contains forbidden word | Update prompt to avoid it |

---

## 2. Golden Mismatch

### Symptom
`Phylax check` fails with hash mismatch.

### Debug Steps

1. **Find the golden** — Which trace was blessed?
   ```bash
   python -m cli.main list --blessed
   ```

2. **Compare outputs** — Look at diff in UI
   - What changed between old and new?
   - Is the change acceptable?

3. **Decide action**:
   - If change is good → Bless the new trace
   - If change is bad → Fix your code/prompt

### Re-bless if Acceptable

```bash
python -m cli.main bless <new-trace-id> --force
```

---

## 3. Graph Failed

### Symptom
Execution graph shows ❌ overall verdict.

### Debug Steps

1. **Enable Forensics Mode** — Click 🔬 button

2. **Find root cause** — Look for pulsing red node
   - This is the first node that failed
   - Start debugging here

3. **Check parent** — What input did it receive?
   - Click parent node
   - Was the input malformed?

4. **Review tainted nodes** — Yellow/warning nodes
   - These received bad data
   - They may have passed but with wrong output

5. **Use investigation path**
   ```bash
   curl http://127.0.0.1:8000/v1/executions/{id}/investigate
   ```

### Investigation Order

```
1. Root cause node     → What failed?
2. Parent input        → What triggered it?
3. Validation rules    → Which rule violated?
4. Tainted downstream  → What did it affect?
```

---

## 4. CI Check Failing

### Symptom
`Phylax check` exits 1 in CI.

### Debug Steps

1. **Check CI logs** — See which trace failed

2. **Run locally**
   ```bash
   python -m cli.main check
   ```

3. **List failures**
   ```bash
   python -m cli.main list --failed
   ```

4. **Inspect specific trace**
   ```bash
   python -m cli.main show <trace-id>
   ```

### Common CI Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| No golden exists | Never blessed | Bless a trace |
| Model changed | Different API version | Re-bless or fix |
| Prompt changed | Code update | Re-bless if intentional |
| Latency spike | Slow network | Increase threshold |

---

## 5. Replay Failed

### Symptom
Replay trace has different output than expected.

### Debug Steps

1. **Compare original and replay**
   - Open both traces
   - Check diff

2. **Check if deterministic**
   - LLM outputs vary by nature
   - Only check if regression is significant

3. **Review expectations**
   - Are they too strict for non-determinism?

---

## 6. Server Not Starting

### Symptom
`Phylax server` fails.

### Debug Steps

1. **Check port 8000** — Is it in use?
   ```bash
   netstat -an | findstr 8000  # Windows
   lsof -i :8000               # Linux/Mac
   ```

2. **Check config** — Is `~/.Phylax/` readable?

3. **Check dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## 7. Traces Not Saving

### Symptom
Made calls but UI is empty.

### Debug Steps

1. **Check adapter setup**
   - Is `GOOGLE_API_KEY` set?
   - Is adapter returning correctly?

2. **Check decorator**
   - Is `@trace` applied to function?

3. **Check server connected**
   - Is server running?
   - Is trace sent to right host?

4. **Check storage**
   - Does `~/.Phylax/traces/` exist?
   - Are there JSON files?

---

## Quick Reference

| Failure | First Check |
|---------|-------------|
| Trace ❌ | Read violation message |
| Golden mismatch | Check output diff |
| Graph ❌ | Enable forensics mode |
| CI exit 1 | List failed traces |
| Replay differs | Compare with original |
| Server error | Check port 8000 |
| No traces | Check @trace decorator |

---

## Emergency Commands

```bash
# See all failures
python -m cli.main list --failed

# Show specific trace
python -m cli.main show <id>

# Re-bless after fixing
python -m cli.main bless <id> --force

# Run CI check locally
python -m cli.main check
```
