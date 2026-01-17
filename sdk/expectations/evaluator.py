"""
Expectation Evaluator

Evaluates a set of rules against an LLM response and produces a Verdict.

Design rules:
- Verdicts are computed at trace creation time (never deferred)
- Verdicts are immutable once written
- All violations are reported (not short-circuited)
- Severity is the maximum of all violations
"""

from typing import Literal, Optional
from pydantic import BaseModel

from sdk.expectations.rules import (
    Rule,
    RuleResult,
    SeverityLevel,
    MustIncludeRule,
    MustNotIncludeRule,
    MaxLatencyRule,
    MinTokensRule,
)


class Verdict(BaseModel):
    """
    Immutable verdict for an LLM call.
    
    Once written to a trace, this MUST never be recalculated or modified.
    """
    status: Literal["pass", "fail"]
    severity: Optional[SeverityLevel] = None  # None when passing
    violations: list[str] = []
    
    class Config:
        frozen = True  # Enforce immutability


class Evaluator:
    """
    Evaluates rules against LLM responses.
    
    Usage:
        evaluator = Evaluator()
        evaluator.add_rule(MustIncludeRule(["refund"]))
        evaluator.add_rule(MaxLatencyRule(1500))
        verdict = evaluator.evaluate(response_text, latency_ms)
    """
    
    def __init__(self):
        self.rules: list[Rule] = []
    
    def add_rule(self, rule: Rule) -> "Evaluator":
        """Add a rule to the evaluator. Returns self for chaining."""
        self.rules.append(rule)
        return self
    
    def must_include(self, substrings: list[str], case_sensitive: bool = False) -> "Evaluator":
        """Add a must_include rule."""
        return self.add_rule(MustIncludeRule(substrings, case_sensitive))
    
    def must_not_include(self, substrings: list[str], case_sensitive: bool = False) -> "Evaluator":
        """Add a must_not_include rule."""
        return self.add_rule(MustNotIncludeRule(substrings, case_sensitive))
    
    def max_latency_ms(self, max_ms: int) -> "Evaluator":
        """Add a max_latency_ms rule."""
        return self.add_rule(MaxLatencyRule(max_ms))
    
    def min_tokens(self, min_tokens: int) -> "Evaluator":
        """Add a min_tokens rule."""
        return self.add_rule(MinTokensRule(min_tokens))
    
    def evaluate(self, response_text: str, latency_ms: int) -> Verdict:
        """
        Evaluate all rules and produce a verdict.
        
        All rules are evaluated (no short-circuit).
        Severity is the maximum of all violations.
        """
        if not self.rules:
            return Verdict(status="pass")
        
        results: list[RuleResult] = []
        for rule in self.rules:
            result = rule.evaluate(response_text, latency_ms)
            results.append(result)
        
        # Collect all violations
        violations = [r.violation_message for r in results if not r.passed]
        
        if not violations:
            return Verdict(status="pass")
        
        # Determine max severity
        severity_order = {"low": 0, "medium": 1, "high": 2}
        max_severity: SeverityLevel = "low"
        
        for result in results:
            if not result.passed:
                if severity_order[result.severity] > severity_order[max_severity]:
                    max_severity = result.severity
        
        return Verdict(
            status="fail",
            severity=max_severity,
            violations=violations,
        )


def evaluate(
    response_text: str,
    latency_ms: int,
    must_include: Optional[list[str]] = None,
    must_not_include: Optional[list[str]] = None,
    max_latency_ms: Optional[int] = None,
    min_tokens: Optional[int] = None,
) -> Verdict:
    """
    Convenience function to evaluate expectations.
    
    Args:
        response_text: The LLM response text
        latency_ms: Response latency in milliseconds
        must_include: Substrings that must appear
        must_not_include: Substrings that must NOT appear
        max_latency_ms: Maximum latency threshold
        min_tokens: Minimum token count
        
    Returns:
        Verdict with pass/fail status and any violations
    """
    evaluator = Evaluator()
    
    if must_include:
        evaluator.must_include(must_include)
    
    if must_not_include:
        evaluator.must_not_include(must_not_include)
    
    if max_latency_ms is not None:
        evaluator.max_latency_ms(max_latency_ms)
    
    if min_tokens is not None:
        evaluator.min_tokens(min_tokens)
    
    return evaluator.evaluate(response_text, latency_ms)
