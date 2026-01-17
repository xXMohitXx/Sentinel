"""
Sentinel Expectations Package

Rule-based expectation system for LLM call validation.
Provides PASS/FAIL verdicts based on deterministic rules.

Rules supported:
- must_include: Substring(s) must appear
- must_not_include: Substring(s) must NOT appear
- max_latency_ms: Latency ceiling
- min_tokens: Minimum response length

Design constraints:
- Deterministic only (no AI judgment)
- Verdicts computed at trace creation time
- Verdicts are immutable once written
"""

from sdk.expectations.rules import (
    Rule,
    MustIncludeRule,
    MustNotIncludeRule,
    MaxLatencyRule,
    MinTokensRule,
)
from sdk.expectations.evaluator import (
    Verdict,
    Evaluator,
    evaluate,
)

__all__ = [
    # Rules
    "Rule",
    "MustIncludeRule",
    "MustNotIncludeRule",
    "MaxLatencyRule",
    "MinTokensRule",
    # Evaluation
    "Verdict",
    "Evaluator",
    "evaluate",
]
